#!/usr/bin/env python3
"""
LinkedIn Jobs Search Box Click Test
Integrated scraper for the LinkedIn Job Automation System
"""

import asyncio
import logging
import json
import requests
from playwright.async_api import async_playwright
from datetime import datetime
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInJobScraper:
    """
    LinkedIn Job Scraper integrated with Rails backend via API
    """

    def __init__(self, backend_url: str = "http://localhost:3001"):
        self.backend_url = backend_url
        self.page = None
        self.browser = None
        self.context = None

    async def start(self):
        """Initialize browser and context"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Keep visible for debugging
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def stop(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()

    async def login_to_linkedin(self, email: str = None, password: str = None) -> bool:
        """
        Login to LinkedIn with credentials
        Returns True if successful, False otherwise
        """
        try:
            # Navigate to LinkedIn login
            await self.page.goto("https://www.linkedin.com/login")
            await self.page.wait_for_load_state('networkidle')

            print("📧 Please login manually in the browser window")
            print("⏳ Waiting for login to complete...")

            # Wait for successful login by checking for navigation to feed or jobs page
            await self.page.wait_for_url("**/feed/**", timeout=60000)

            # Navigate to jobs page
            await self.page.goto("https://www.linkedin.com/jobs/")
            await self.page.wait_for_load_state('networkidle')

            return True

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    async def search_jobs(self, search_term: str = "Ruby", location: str = "") -> List[Dict]:
        """
        Perform job search and return results
        """
        try:
            print(f"🔍 Searching for '{search_term}' jobs...")

            # Take debug screenshot
            await self.page.screenshot(path="jobs_page_debug.png")
            print("📸 Debug screenshot saved")

            # Wait for page to fully load
            await asyncio.sleep(5)

            # Search for the search box with multiple selectors
            search_box_selectors = [
                'input[placeholder="Title, skill or Company"]',
                'input[placeholder*="Title"]',
                'input[placeholder*="skill"]',
                'input[placeholder*="Company"]',
                '.jobs-search-box__input.jobs-search-box__input--keyword',
                '.jobs-search-box__input--keyword',
                '.jobs-search-box__input',
                'input[aria-label*="Search by title"]',
                'input[type="text"]'
            ]

            search_box_found = False
            for selector in search_box_selectors:
                try:
                    search_box = await self.page.wait_for_selector(selector, timeout=3000)
                    if search_box:
                        print(f"✅ Found search box: {selector}")

                        # Clear existing text and type search term
                        await search_box.click()
                        await search_box.fill("")  # Clear existing text
                        await asyncio.sleep(0.5)
                        await search_box.type(search_term, delay=100)

                        # Press Enter to search
                        await search_box.press('Enter')
                        print(f"✅ Search initiated for: {search_term}")

                        # Wait for results to load
                        await self.page.wait_for_load_state('networkidle')
                        await asyncio.sleep(3)

                        search_box_found = True
                        break

                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue

            if not search_box_found:
                print("❌ Could not find search box")
                return []

            # Extract job listings
            jobs = await self.extract_job_listings()

            # Send jobs to Rails backend
            await self.send_jobs_to_backend(jobs)

            return jobs

        except Exception as e:
            logger.error(f"Job search failed: {e}")
            return []

    async def extract_job_listings(self) -> List[Dict]:
        """
        Extract job listing data from the current page
        """
        try:
            # Wait for job cards to load
            await self.page.wait_for_selector('.job-card-container', timeout=10000)

            # Extract job data
            jobs = await self.page.evaluate("""
                () => {
                    const jobCards = document.querySelectorAll('.job-card-container, .jobs-search__results-list li');
                    const jobs = [];

                    jobCards.forEach((card, index) => {
                        try {
                            const titleElement = card.querySelector('h3 a, .job-card-list__title a');
                            const companyElement = card.querySelector('.job-card-container__company-name, .job-card-list__company-name');
                            const locationElement = card.querySelector('.job-card-container__metadata-item, .job-card-list__metadata');
                            const linkElement = card.querySelector('h3 a, .job-card-list__title a');

                            if (titleElement) {
                                jobs.push({
                                    title: titleElement.innerText.trim(),
                                    company: companyElement ? companyElement.innerText.trim() : 'Unknown Company',
                                    location: locationElement ? locationElement.innerText.trim() : 'Unknown Location',
                                    url: linkElement ? linkElement.href : '',
                                    scraped_at: new Date().toISOString(),
                                    source: 'linkedin'
                                });
                            }
                        } catch (e) {
                            console.log('Error extracting job data:', e);
                        }
                    });

                    return jobs;
                }
            """)

            print(f"📊 Extracted {len(jobs)} job listings")
            return jobs

        except Exception as e:
            logger.error(f"Job extraction failed: {e}")
            return []

    async def send_jobs_to_backend(self, jobs: List[Dict]):
        """
        Send extracted jobs to Rails backend via GraphQL
        """
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
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                print(f"✅ Successfully sent {len(jobs)} jobs to backend")
            else:
                print(f"⚠️ Backend API error: {response.status_code}")

        except Exception as e:
            logger.error(f"Failed to send jobs to backend: {e}")


async def main():
    """
    Main function to run the scraper
    """
    print("🚀 LinkedIn Job Scraper Starting...")
    print("=" * 50)

    scraper = LinkedInJobScraper()

    try:
        # Start browser
        await scraper.start()
        print("✅ Browser started")

        # Login to LinkedIn
        login_success = await scraper.login_to_linkedin()
        if not login_success:
            print("❌ Login failed")
            return

        # Search for jobs
        jobs = await scraper.search_jobs("Ruby Developer")

        if jobs:
            print(f"🎉 Found {len(jobs)} jobs!")
            for i, job in enumerate(jobs[:5], 1):  # Show first 5 jobs
                print(f"{i}. {job['title']} at {job['company']} - {job['location']}")
        else:
            print("⚠️ No jobs found")

        # Keep browser open for inspection
        print("⏳ Keeping browser open for 10 seconds...")
        await asyncio.sleep(10)

    except Exception as e:
        logger.error(f"Scraper failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.stop()
        print("🏁 Scraper finished")


if __name__ == "__main__":
    print("LinkedIn Job Automation System - Scraper Module")
    print("Integrated with Rails backend via GraphQL API")
    print()

    asyncio.run(main())