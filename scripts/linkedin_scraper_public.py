#!/usr/bin/env python3
"""
Public LinkedIn Jobs Scraper
Simple, robust scraper that works without authentication
Uses public LinkedIn job search pages
"""

import asyncio
import logging
import json
import requests
from playwright.async_api import async_playwright
from datetime import datetime
from typing import Dict, List, Optional
import urllib.parse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PublicLinkedInJobScraper:
    """
    Simple LinkedIn Job Scraper that uses public pages (no authentication required)
    """

    def __init__(self, backend_url: str = "http://localhost:3001"):
        self.backend_url = backend_url
        self.page = None
        self.browser = None
        self.context = None

    async def start(self):
        """Initialize browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def stop(self):
        """Clean up browser resources"""
        if self.context:
            await self.context.close()

    async def search_jobs(self, search_term: str = "Ruby Developer", location: str = "United States") -> List[Dict]:
        """
        Search for jobs on public LinkedIn pages
        """
        try:
            # Build search URL for public LinkedIn
            encoded_keywords = urllib.parse.quote(search_term)
            encoded_location = urllib.parse.quote(location)
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_keywords}&location={encoded_location}"

            print(f"🔍 Searching for '{search_term}' jobs in '{location}'...")
            print(f"🌐 URL: {search_url}")

            # Navigate to search results
            await self.page.goto(search_url)
            await self.page.wait_for_load_state('load')

            # Wait for job listings to load
            try:
                await self.page.wait_for_selector('ul[role="list"]', timeout=10000)
                print("✅ Job listings loaded")
            except:
                print("⚠️ No job listings found, trying alternative wait...")
                await asyncio.sleep(3)

            # Extract jobs from the page
            jobs = await self.extract_jobs()

            if jobs:
                # Send to backend if configured
                await self.send_jobs_to_backend(jobs)

            return jobs

        except Exception as e:
            logger.error(f"Job search failed: {e}")
            return []

    async def extract_jobs(self) -> List[Dict]:
        """
        Extract job data from the current page
        """
        try:
            print("📊 Extracting job listings...")

            # Wait a bit more for dynamic content
            await asyncio.sleep(2)

            # Try to find job list items using the public page structure
            job_selectors = [
                'ul[role="list"] li',  # Main jobs list
                'main ul li',          # Alternative main list
                'li[data-occludable-job-id]',  # Jobs with data attributes
            ]

            jobs_data = []

            for selector in job_selectors:
                try:
                    job_elements = await self.page.query_selector_all(selector)
                    if job_elements and len(job_elements) > 0:
                        print(f"✅ Found {len(job_elements)} job elements with selector: {selector}")

                        # Extract data from each job element
                        for i, job_element in enumerate(job_elements[:15]):  # Limit to first 15 jobs
                            try:
                                job_data = await self.extract_single_job(job_element)
                                if job_data and job_data['title'] != "Unknown Job":
                                    jobs_data.append(job_data)

                            except Exception as e:
                                logger.debug(f"Failed to extract job {i}: {e}")
                                continue

                        break  # Success with this selector

                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue

            print(f"✅ Successfully extracted {len(jobs_data)} jobs")
            return jobs_data

        except Exception as e:
            logger.error(f"Job extraction failed: {e}")
            return []

    async def extract_single_job(self, job_element) -> Optional[Dict]:
        """
        Extract data from a single job element
        """
        try:
            # Get the full text content
            full_text = await job_element.inner_text()
            if not full_text or len(full_text.strip()) < 10:
                return None

            # Extract job title
            title = await self.extract_title(job_element, full_text)

            # Extract company name
            company = await self.extract_company(job_element, full_text)

            # Extract location
            location = await self.extract_location(job_element, full_text)

            # Extract job URL
            url = await self.extract_url(job_element)

            # Return job data
            return {
                'title': title,
                'company': company,
                'location': location,
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'source': 'linkedin_public'
            }

        except Exception as e:
            logger.debug(f"Error extracting single job: {e}")
            return None

    async def extract_title(self, job_element, full_text: str) -> str:
        """Extract job title"""
        try:
            # Try different selectors for job titles
            title_selectors = [
                'h3 a',
                'h3',
                'a[data-tracking-control-name*="job_card_title"]',
                'a[href*="/jobs/view/"]',
            ]

            for selector in title_selectors:
                title_element = await job_element.query_selector(selector)
                if title_element:
                    title_text = await title_element.inner_text()
                    if title_text and len(title_text.strip()) > 3:
                        return title_text.strip()

            # Fallback: try to parse from text
            lines = full_text.split('\n')
            for line in lines[:3]:  # Check first few lines
                line = line.strip()
                if (len(line) > 10 and len(line) < 100 and
                    any(keyword in line.lower() for keyword in ['engineer', 'developer', 'manager', 'analyst', 'specialist'])):
                    return line

            return "Unknown Job"

        except:
            return "Unknown Job"

    async def extract_company(self, job_element, full_text: str) -> str:
        """Extract company name"""
        try:
            # Try different selectors for company
            company_selectors = [
                'h4 a',
                'h4',
                'a[data-tracking-control-name*="company"]',
            ]

            for selector in company_selectors:
                company_element = await job_element.query_selector(selector)
                if company_element:
                    company_text = await company_element.inner_text()
                    if company_text and len(company_text.strip()) > 1:
                        return company_text.strip()

            # Fallback: parse from text patterns
            lines = full_text.split('\n')
            for line in lines:
                line = line.strip()
                # Look for company patterns (short lines without job keywords)
                if (len(line) > 2 and len(line) < 50 and
                    not any(keyword in line.lower() for keyword in ['engineer', 'developer', 'manager', 'software', 'senior', 'junior']) and
                    not any(loc in line for loc in ['CA', 'NY', 'Remote', 'ago', 'hours', 'days', 'weeks'])):
                    return line

            return "Unknown Company"

        except:
            return "Unknown Company"

    async def extract_location(self, job_element, full_text: str) -> str:
        """Extract job location"""
        try:
            # Look for location patterns in the text
            location_indicators = [
                'Remote', 'Hybrid', 'On-site',
                'CA', 'NY', 'TX', 'FL', 'WA', 'IL', 'PA', 'OH', 'GA', 'NC', 'VA', 'NJ',
                'United States', 'USA', 'San Francisco', 'New York', 'Los Angeles', 'Seattle', 'Austin'
            ]

            lines = full_text.split('\n')
            for line in lines:
                for indicator in location_indicators:
                    if indicator in line:
                        # Clean up the location line
                        location = line.strip()
                        if len(location) < 100:  # Reasonable location length
                            return location

            return "Unknown Location"

        except:
            return "Unknown Location"

    async def extract_url(self, job_element) -> str:
        """Extract job URL"""
        try:
            # Find the main job link
            link_selectors = [
                'a[href*="/jobs/view/"]',
                'h3 a',
                'a',
            ]

            for selector in link_selectors:
                link_element = await job_element.query_selector(selector)
                if link_element:
                    href = await link_element.get_attribute('href')
                    if href and '/jobs/view/' in href:
                        # Ensure it's a full URL
                        if href.startswith('http'):
                            return href
                        else:
                            return f"https://www.linkedin.com{href}"

            return ""

        except:
            return ""

    async def send_jobs_to_backend(self, jobs: List[Dict]):
        """Send extracted jobs to Rails backend via GraphQL"""
        try:
            if not jobs:
                return

            # GraphQL mutation to create jobs
            mutation = """
                mutation CreateJobs($jobs: [JobInput!]!) {
                    createJobs(input: { jobs: $jobs }) {
                        jobs {
                            id
                            title
                            company
                        }
                        errors
                    }
                }
            """

            # Send to backend
            response = requests.post(
                f"{self.backend_url}/graphql",
                json={
                    "query": mutation,
                    "variables": {"jobs": jobs}
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            if response.status_code == 200:
                print(f"✅ Successfully sent {len(jobs)} jobs to backend")
            else:
                print(f"⚠️ Backend API error: {response.status_code}")

        except Exception as e:
            logger.error(f"Failed to send jobs to backend: {e}")


async def main():
    """Main function to run the scraper"""
    print("🚀 Public LinkedIn Job Scraper Starting...")
    print("=" * 50)

    scraper = PublicLinkedInJobScraper()

    try:
        # Start browser
        await scraper.start()
        print("✅ Browser started")

        # Search for jobs
        jobs = await scraper.search_jobs("Ruby on Rails", "United States")

        if jobs:
            print(f"🎉 Found {len(jobs)} jobs!")
            for i, job in enumerate(jobs[:10], 1):  # Show first 10 jobs
                print(f"{i}. {job['title']} at {job['company']} - {job['location']}")
                if job['url']:
                    print(f"   🔗 {job['url']}")
        else:
            print("⚠️ No jobs found")

        # Keep browser open briefly for inspection
        print("⏳ Keeping browser open for 5 seconds...")
        await asyncio.sleep(5)

    except Exception as e:
        logger.error(f"Scraper failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.stop()
        print("🏁 Scraper finished")


if __name__ == "__main__":
    print("LinkedIn Job Automation System - Public Scraper Module")
    print("Works without LinkedIn authentication")
    print()

    asyncio.run(main())