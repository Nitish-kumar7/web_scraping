import requests
from bs4 import BeautifulSoup
import json
import re
import time
from typing import Optional, Dict, Any
import logging
from datetime import datetime
import random
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstagramScraper:
    def __init__(self, rate_limit: int = 5):
        """
        Initialize the Instagram scraper with rate limiting.
        
        Args:
            rate_limit (int): Minimum seconds between requests
        """
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.driver = None
        self._setup_driver()

    def _setup_driver(self):
        """Set up the Selenium WebDriver with Chrome options."""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')  # Updated headless mode syntax
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Add experimental options to avoid detection
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            try:
                # Use webdriver-manager to handle ChromeDriver installation
                service = ChromeService(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("WebDriver initialized successfully with ChromeDriverManager")
            except Exception as e:
                logger.error(f"Failed to initialize WebDriver with ChromeDriverManager: {e}")
                raise

            # Set page load timeout
            self.driver.set_page_load_timeout(30)
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            raise

    def _respect_rate_limit(self):
        """Ensure we don't make requests too frequently."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last_request)
        self.last_request_time = time.time()

    def _extract_profile_data(self) -> Optional[Dict[str, Any]]:
        """Extract profile data from the current page."""
        profile_info = {}
        try:
            # Wait for the main content to load
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "main"))
                )
                logger.info("Main content loaded.")
            except TimeoutException:
                logger.warning("Timeout waiting for main content.")
                # Continue attempting to parse even if timeout occurs, as some content might be available

            # Get the page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Try to find the profile data in script tags (application/ld+json)
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'ProfilePage':
                        logger.info("Found data in application/ld+json script tag.")
                        author_data = data.get('author', {})
                        profile_info.update({
                            'username': author_data.get('alternateName', '').replace('@', ''),
                            'full_name': author_data.get('name', ''),
                            'biography': author_data.get('description', ''),
                            'profile_pic_url': author_data.get('image', ''),
                            'external_url': author_data.get('url', ''),
                            'timestamp': datetime.now().isoformat()
                        })
                        # If we found this structured data, it's likely the main info, return it.
                        return profile_info
                except (json.JSONDecodeError, AttributeError) as e:
                    logger.debug(f"Error parsing application/ld+json script: {e}")
                    continue # Try next script tag
                except Exception as e:
                    logger.debug(f"Unexpected error in application/ld+json script parsing: {e}")
                    continue

            logger.warning("Could not find primary data in application/ld+json script tags. Falling back to meta tags.")

            # Fallback to meta tags if JSON extraction fails or wasn't primary
            
            # Get description
            meta_description = soup.find('meta', {'name': 'description'})
            if meta_description:
                content = meta_description.get('content', '')
                profile_info['description_meta'] = content # Store raw meta description
                logger.info(f"Found meta description: {content[:100]}...")
                
                # Extract numbers from description
                match = re.search(r'(\d[\d,]*)\s*Followers,\s*(\d[\d,]*)\s*Following,\s*(\d[\d,]*)\s*Posts', content)
                if match:
                    logger.info("Extracted counts from meta description.")
                    try:
                        profile_info.update({
                            'followers_count': int(match.group(1).replace(',', '')),
                            'following_count': int(match.group(2).replace(',', '')),
                            'posts_count': int(match.group(3).replace(',', ''))
                        })
                    except ValueError:
                        logger.warning("Could not convert follower/following/post counts to int from meta description.")

            # Get profile picture from og:image
            profile_pic = soup.find('meta', {'property': 'og:image'})
            if profile_pic:
                profile_info['profile_pic_url'] = profile_pic.get('content')
                logger.info("Found og:image meta tag.")

            # Get title and try to extract username
            title = soup.find('title')
            if title:
                profile_info['title'] = title.text.strip()
                logger.info(f"Found title: {title.text.strip()}")
                # Extract username from title (basic attempt)
                username_match = re.search(r'@?([a-zA-Z0-9._-]+)', title.text)
                if username_match:
                     # Only update username if not already found and seems valid
                    if 'username' not in profile_info or not profile_info['username']:
                        profile_info['username'] = username_match.group(1)
                        logger.info(f"Extracted username from title: {profile_info['username']}")

            # Attempt to find biography in meta description or other common places
            if 'biography' not in profile_info or not profile_info['biography']:
                meta_description_tag = soup.find('meta', attrs={'name': 'description'})
                if meta_description_tag and meta_description_tag.get('content'):
                     # Check if it looks like a typical bio (not just counts)
                     if 'Followers' not in meta_description_tag['content']:
                         profile_info['biography'] = meta_description_tag.get('content')
                         logger.info("Found biography in meta description.")

            # Return gathered info, even if incomplete
            return profile_info if profile_info else None

        except TimeoutException:
            logger.error("Timeout while waiting for page elements")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during profile data extraction: {e}")
            return None

    def scrape_profile(self, username: str) -> Dict[str, Any]:
        """
        Scrape public profile data from an Instagram username.
        
        Args:
            username (str): Instagram username to scrape
            
        Returns:
            Dict containing profile information or error details
        """
        profile_url = f"https://www.instagram.com/{username}/"
        
        try:
            # Ensure driver is initialized before use
            if not self.driver:
                 self._setup_driver() # Re-initialize if it was closed

            self._respect_rate_limit()
            logger.info(f"Attempting to scrape: {profile_url}")
            
            # Navigate to the profile page
            self.driver.get(profile_url)
            
            # Check if profile exists or is private
            if "Page Not Found" in self.driver.page_source or "Sorry, this page isn't available" in self.driver.page_source:
                 # Attempt to extract meta data even if page not found to check for private profiles
                 soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                 meta_data = self._extract_meta_data(soup) # Reuse meta data extraction logic
                 if meta_data and 'description' in meta_data and ('Private' in meta_data['description'] or 'followers' not in meta_data['description'].lower()):
                      logger.warning(f"Profile @{username} appears to be private or not found.")
                      return {
                          'username': username,
                          'error': 'Profile not found or is private',
                          'timestamp': datetime.now().isoformat()
                      }
                 else:
                    logger.error(f"Profile @{username} not found or unavailable.")
                    return {
                        'username': username,
                        'error': 'Profile not found or unavailable',
                        'timestamp': datetime.now().isoformat()
                    }
            # Extract profile data
            profile_data = self._extract_profile_data()
            
            if profile_data:
                # Ensure username is consistent, prioritize the requested one
                profile_data['username'] = username
                logger.info(f"Successfully scraped data for @{username}")
                return profile_data
            
            # If all extraction methods fail
            logger.error(f"Could not extract profile data for @{username} after loading.")
            return {
                'username': username,
                'error': 'Could not extract profile data after loading',
                'timestamp': datetime.now().isoformat()
            }
            
        except TimeoutException:
            logger.error(f"Timeout while loading page for @{username}")
            return {
                'username': username,
                'error': 'Timeout while loading page',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Unexpected error while scraping @{username}: {e}")
            return {
                'username': username,
                'error': f"Unexpected error: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
        finally:
            # Clean up only if an error occurred that prevents further use, otherwise keep the driver for the next request
            # To clean up after each request regardless of error, move the quit() here
            # For persistent use across requests in a server, manage driver lifecycle carefully
            pass # Decide when to quit the driver based on application needs

    def __del__(self):
        """Clean up the WebDriver when the object is destroyed."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

# Example usage
if __name__ == "__main__":
    # Ensure you have chromedriver installed and in your PATH
    # Or specify the executable_path when initializing webdriver.Chrome
    scraper = InstagramScraper(rate_limit=5)
    test_usernames = ["instagram", "therock", "nasa", "nitish5300", "this_user_does_not_exist_12345"]
    
    for username in test_usernames:
        print(f"\nScraping data for @{username}...")
        profile_data = scraper.scrape_profile(username)
        
        if 'error' not in profile_data:
            print("\n--- Scraped Instagram Data ---")
            for key, value in profile_data.items():
                if key != 'timestamp':
                    print(f"{key.replace('_', ' ').title()}: {value}")
        else:
            print(f"Error: {profile_data['error']}")