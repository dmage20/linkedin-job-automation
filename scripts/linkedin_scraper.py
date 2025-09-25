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
        """Initialize browser and context with persistent session"""
        playwright = await async_playwright().start()

        # Use persistent context to save login session
        self.context = await playwright.chromium.launch_persistent_context(
            user_data_dir="./linkedin_session",  # Directory to save session data
            headless=False,  # Keep visible for debugging
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )

        self.browser = self.context.browser
        self.page = await self.context.new_page()

    async def stop(self):
        """Clean up browser resources (keeps session data)"""
        if self.context:
            await self.context.close()

    async def login_to_linkedin(self, email: str = None, password: str = None) -> bool:
        """
        Login to LinkedIn with credentials
        Returns True if successful, False otherwise
        """
        try:
            # Step 1: Navigate to LinkedIn login page
            print("🌐 Navigating to LinkedIn login page...")
            await self.page.goto("https://www.linkedin.com/login")
            await self.page.wait_for_load_state('load')

            # Step 2: Wait for login form to be ready
            try:
                await self.page.wait_for_selector('#username', state='visible', timeout=10000)
                print("📧 Please enter your credentials in the browser window")
                print("⏳ Waiting for login completion (including any security checks)...")
                print("💡 If you see a CAPTCHA or security check, please complete it")
            except:
                # Might already be logged in
                current_url = self.page.url
                if '/feed' in current_url or '/jobs' in current_url:
                    print("✅ Already logged in - skipping login")
                    await self.page.goto("https://www.linkedin.com/jobs/")
                    await self.page.wait_for_load_state('load')
                    return True

            # Step 3: Wait for successful login (navigate away from login page)
            # This handles regular login and CAPTCHAs with 3-minute timeout
            await self.page.wait_for_url(lambda url: '/login' not in url and '/checkpoint' not in url,
                                        timeout=180000)

            print("✅ Login successful - navigating to landing page")

            # Step 4: Wait for landing page to load (less strict, just wait for basic load)
            await self.page.wait_for_load_state('load')
            await asyncio.sleep(2)  # Brief pause to let page settle

            # Step 5: Navigate to jobs page
            print("📋 Navigating to Jobs page...")
            await self.page.goto("https://www.linkedin.com/jobs/")
            await self.page.wait_for_load_state('load')

            print("✅ Successfully on Jobs page - ready to search")
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

                        # Wait for results to load - use URL change or job cards appearing
                        print("⏳ Waiting for search results...")
                        try:
                            # Wait for either URL to update with search query OR job cards to appear
                            await self.page.wait_for_function(
                                """() => {
                                    return document.querySelector('.job-card-container') !== null ||
                                           document.querySelector('.jobs-search__results-list') !== null ||
                                           window.location.href.includes('keywords=')
                                }""",
                                timeout=30000
                            )
                            print("✅ Search results detected")
                        except:
                            print("⚠️ Results may still be loading...")

                        # Give extra time for all results to render
                        await asyncio.sleep(2)

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
            print("📊 Attempting to extract job listings...")

            # Wait for the main jobs list to load
            print("⏳ Waiting for job search results to load...")

            # Wait for the main jobs list (based on actual page structure)
            main_jobs_list_selector = 'main ul[role="list"]'
            try:
                await self.page.wait_for_selector(main_jobs_list_selector, timeout=15000)
                print(f"✅ Found main jobs list")
            except:
                print("⚠️ Main jobs list not found, trying alternative selectors...")
                # Fallback selectors
                fallback_selectors = ['main ul', 'main list', '[role="main"] ul']
                result_loaded = False
                for selector in fallback_selectors:
                    try:
                        await self.page.wait_for_selector(selector, timeout=5000)
                        print(f"✅ Found jobs container: {selector}")
                        result_loaded = True
                        break
                    except:
                        continue

                if not result_loaded:
                    print("⚠️ No job containers found, waiting for network idle...")
                    try:
                        await self.page.wait_for_load_state('networkidle', timeout=10000)
                        print("✅ Network idle")
                    except:
                        print("⚠️ Network timeout, proceeding anyway...")

            # Additional wait for dynamic content
            await asyncio.sleep(2)

            # Extract job data from list items
            print("🔍 Extracting job data from list items...")

            # Get all job list items - try both authenticated and public page structures
            job_selectors = [
                # For authenticated LinkedIn (dashboard-style layout)
                '[data-view-name="job-card"]',  # Job cards with data attributes
                'div[class*="job"]',  # Divs with job-related classes
                'article',  # Job articles
                'section[aria-label*="job"]',  # Sections labeled as jobs
                # For public LinkedIn search results
                'main div > ul li',  # Jobs list inside main div
                'main ul:nth-of-type(2) li',  # Second ul (skip navigation ul)
                'main section ul li',  # Jobs in a section
                'li[role="listitem"]',  # Specific listitem roles
            ]

            jobs_found = 0
            jobs_data = []

            for selector in job_selectors:
                try:
                    job_elements = await self.page.query_selector_all(selector)
                    jobs_found = len(job_elements)
                    if jobs_found > 0:
                        print(f"✅ Found {jobs_found} job elements with selector: {selector}")

                        # Extract job data from each element
                        for i, job_element in enumerate(job_elements[:10]):  # Limit to first 10 for now
                            try:
                                # Extract job title - try multiple strategies
                                title_selectors = [
                                    'h3',  # Standard heading 3
                                    'a[data-control-name*="job_card_title"]',  # LinkedIn job title links
                                    'a[href*="/jobs/view/"]',  # Job view links
                                    '.jobs-search-results__list-item a',  # Search result links
                                    'span[aria-hidden="true"]',  # Sometimes titles are in spans
                                ]
                                title = "Unknown Job"
                                for title_sel in title_selectors:
                                    title_element = await job_element.query_selector(title_sel)
                                    if title_element:
                                        title_text = await title_element.inner_text()
                                        # Filter out short/empty titles
                                        if title_text and len(title_text.strip()) > 3:
                                            title = title_text.strip()
                                            break

                                # Extract company name from the full text using patterns
                                company = "Unknown Company"
                                full_text = await job_element.inner_text()

                                # Parse company from the text - it's all in one line
                                # Pattern: "Job Title (Verified job)Job Title Company • Location • Salary..."
                                # We need to find the text between the repeated job title and the first bullet

                                # Find the first bullet point
                                if '•' in full_text:
                                    # Split on first bullet to get the part before location/salary
                                    before_bullet = full_text.split('•')[0]

                                    # Remove the job title and common prefixes to isolate company
                                    # Remove "(Verified job)" and the repeated title
                                    cleaned_text = before_bullet.replace('(Verified job)', '').strip()

                                    # The pattern is usually: "TitleTitle Company"
                                    # Try to find where the title ends and company begins
                                    if title != "Unknown Job" and title in cleaned_text:
                                        # Find the last occurrence of the title
                                        last_title_pos = cleaned_text.rfind(title)
                                        if last_title_pos != -1:
                                            # Extract text after the title
                                            after_title = cleaned_text[last_title_pos + len(title):].strip()
                                            if after_title and len(after_title) < 50:
                                                # Simple validation: company name shouldn't contain job keywords
                                                job_keywords = ['engineer', 'developer', 'manager', 'software', 'senior', 'junior', 'lead']
                                                is_company = not any(keyword.lower() in after_title.lower() for keyword in job_keywords)
                                                if is_company:
                                                    company = after_title

                                # Fallback: try to find known company names in the text
                                if company == "Unknown Company":
                                    known_companies = ['OpenAI', 'Netflix', 'Google', 'Microsoft', 'Amazon', 'Meta', 'Apple', 'LinkedIn', 'Uber', 'Airbnb', 'Spotify', 'Unity', 'Cedar']
                                    for known in known_companies:
                                        if known in full_text:
                                            company = known
                                            break

                                # Fallback: try standard selectors
                                if company == "Unknown Company":
                                    company_selectors = ['h4', 'a[data-control-name*="company"]']
                                    for company_sel in company_selectors:
                                        company_element = await job_element.query_selector(company_sel)
                                        if company_element:
                                            company_text = await company_element.inner_text()
                                            if company_text and len(company_text.strip()) > 1:
                                                company = company_text.split('•')[0].strip()
                                                break

                                # Extract location - try multiple approaches
                                location = "Unknown Location"

                                # Method 1: Look for text patterns that indicate location
                                full_text = await job_element.inner_text()
                                location_patterns = [', CA', ', NY', ', TX', 'United States', ', FL', ', WA', ', MA', ', IL', ', PA', ', OH', ', GA', ', NC', ', VA', ', NJ', ', MI', ', WI', ', MN', ', CO', ', AZ', ', NV', ', OR', ', UT', ', NM', ', KS', ', OK', ', AR', ', LA', ', MS', ', AL', ', TN', ', KY', ', IN', ', WV', ', MD', ', DE', ', CT', ', RI', ', VT', ', NH', ', ME', ', AK', ', HI', ', SC', ', ND', ', SD', ', MT', ', WY', ', ID', ', NE', ', IA', ', MO']

                                for pattern in location_patterns:
                                    if pattern in full_text:
                                        # Find the location text
                                        lines = full_text.split('\n')
                                        for line in lines:
                                            if pattern in line and len(line) < 50:  # Reasonable location length
                                                location = line.strip()
                                                break
                                        if location != "Unknown Location":
                                            break

                                # Method 2: If still unknown, look for generic elements with location-like text
                                if location == "Unknown Location":
                                    generic_elements = await job_element.query_selector_all('generic')
                                    for elem in generic_elements:
                                        elem_text = await elem.inner_text()
                                        if elem_text and any(pattern in elem_text for pattern in location_patterns) and len(elem_text) < 50:
                                            location = elem_text.strip()
                                            break

                                # Extract job URL from the first link
                                url_element = await job_element.query_selector('a')
                                url = ""
                                if url_element:
                                    url = await url_element.get_attribute('href')
                                    if url and not url.startswith('http'):
                                        url = f"https://www.linkedin.com{url}"

                                job_data = {
                                    'title': title.strip(),
                                    'company': company.strip(),
                                    'location': location,
                                    'url': url,
                                    'scraped_at': datetime.now().isoformat(),
                                    'source': 'linkedin'
                                }
                                jobs_data.append(job_data)

                            except Exception as e:
                                logger.debug(f"Failed to extract job {i}: {e}")
                                continue

                        break  # Success, no need to try other selectors

                except Exception as e:
                    print(f"⚠️ Selector {selector} failed: {e}")
                    continue

            if not jobs_data:
                print("❌ No job data extracted")
                return []

            print(f"✅ Successfully extracted {len(jobs_data)} jobs")
            return jobs_data

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