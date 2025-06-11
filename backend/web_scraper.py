import requests
from bs4 import BeautifulSoup
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
import re
from datetime import datetime
import random

class WebScraperError(Exception):
    pass

@dataclass
class PortfolioData:
    name: Optional[str] = None
    about: Optional[str] = None
    skills: List[str] = None
    experience: List[Dict] = None
    projects: List[Dict] = None
    education: List[Dict] = None
    contact: Dict = None
    social_links: Dict[str, str] = None
    internal_links: List[str] = None
    url: str = None
    title: str = None
    description: str = None
    scraped_at: str = None

    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.experience is None:
            self.experience = []
        if self.projects is None:
            self.projects = []
        if self.education is None:
            self.education = []
        if self.contact is None:
            self.contact = {}
        if self.social_links is None:
            self.social_links = {}
        if self.internal_links is None:
            self.internal_links = []

def get_headers() -> Dict[str, str]:
    """Get headers for web requests."""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

def is_valid_url(url: str) -> bool:
    """Check if URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def normalize_url(url: str) -> str:
    """Normalize URL by adding scheme if missing."""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url

def fetch_page(url: str) -> Optional[str]:
    """
    Fetch the HTML content of a webpage.
    
    Args:
        url (str): The URL to fetch
        
    Returns:
        Optional[str]: The HTML content if successful, None otherwise
    """
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    """Extract all links from the page."""
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        absolute_url = urljoin(base_url, href)
        if is_valid_url(absolute_url):
            links.append(absolute_url)
    return links

def extract_social_links(soup: BeautifulSoup, base_url: str) -> Dict[str, str]:
    """Extract social media links from the page."""
    social_platforms = {
        'github': r'github\.com',
        'linkedin': r'linkedin\.com',
        'twitter': r'twitter\.com',
        'instagram': r'instagram\.com',
        'facebook': r'facebook\.com',
        'medium': r'medium\.com',
        'dev.to': r'dev\.to',
        'behance': r'behance\.net',
        'dribbble': r'dribbble\.com'
    }
    
    social_links = {}
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        absolute_url = urljoin(base_url, href)
        
        for platform, pattern in social_platforms.items():
            if re.search(pattern, absolute_url, re.IGNORECASE):
                social_links[platform] = absolute_url
                break
    
    return social_links

def parse_portfolio(html: str, url: str) -> PortfolioData:
    """
    Parse portfolio data from HTML content.
    
    Args:
        html (str): The HTML content to parse
        url (str): The URL of the portfolio
        
    Returns:
        PortfolioData: Structured portfolio data
    """
    soup = BeautifulSoup(html, 'html.parser')
    data = PortfolioData(url=url, scraped_at=datetime.now().isoformat())

    # Basic metadata
    data.title = soup.title.string if soup.title else ""
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        data.description = meta_desc.get('content', '')

    # Name (from header logo or h1)
    name_tag = soup.select_one('a.logo')
    if name_tag:
        data.name = name_tag.get_text(strip=True)
    else:
        h1_tag = soup.find('h1')
        if h1_tag:
            data.name = h1_tag.get_text(strip=True)

    # About (first p in hero section)
    about_tag = soup.select_one('#hero p')
    if about_tag:
        data.about = about_tag.get_text(strip=True)

    # Skills
    skills = set()
    for img in soup.select('#skills .marquee-item img'):
        alt = img.get('alt')
        if alt:
            skills.add(alt.strip())
    data.skills = list(skills)

    # Experience
    data.experience = []
    for entry in soup.select('#experience .timeline-entry'):
        title = entry.select_one('h1.font-semibold.text-3xl')
        date = entry.select_one('p.my-3.text-white-50')
        resp_list = entry.select('ul li.text-lg')
        responsibilities = [li.get_text(strip=True) for li in resp_list]
        data.experience.append({
            'title': title.get_text(strip=True) if title else None,
            'date': date.get_text(strip=True).replace('🗓️', '').strip() if date else None,
            'responsibilities': responsibilities
        })

    # Education
    data.education = []
    for edu_block in soup.select('#education [section="education"], #education .p-4.rounded-xl'):
        years = edu_block.find_previous('h3', class_='text-xl')
        institution = edu_block.select_one('h3.text-xl.font-bold')
        degree = edu_block.select_one('p.text-neutral-600, p.dark\:text-neutral-300')
        data.education.append({
            'years': years.get_text(strip=True) if years else None,
            'institution': institution.get_text(strip=True) if institution else None,
            'degree': degree.get_text(strip=True) if degree else None
        })

    # Contact and Social Links
    data.contact = {}
    data.social_links = extract_social_links(soup, url)
    for a in soup.select('footer .socials a'):
        href = a.get('href')
        if not href:
            continue
        if 'linkedin' in href:
            data.contact['linkedin'] = href
        elif 'instagram' in href:
            data.contact['instagram'] = href
        elif 'x.com' in href or 'twitter' in href:
            data.contact['twitter'] = href

    # Internal Links
    data.internal_links = extract_links(soup, url)

    return data

def fetch_with_playwright(url: str) -> Optional[str]:
    """
    Fetch webpage content using Playwright for JavaScript-heavy sites.
    
    Args:
        url (str): The URL to fetch
        
    Returns:
        Optional[str]: The HTML content if successful, None otherwise
    """
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            page = browser.new_page()
            page.goto(url)
            time.sleep(2)  # Wait for JS to load
            html = page.content()
            browser.close()
            return html
    except ImportError:
        print("Playwright not installed. Please install it using: pip install playwright and then playwright install")
        return None
    except Exception as e:
        print(f"Error using Playwright: {e}")
        return None

def save_to_json(data: PortfolioData, filename: str = "portfolio_data.json") -> None:
    """
    Save portfolio data to a JSON file.
    
    Args:
        data (PortfolioData): The portfolio data to save
        filename (str): The output filename
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data.__dict__, f, indent=4, ensure_ascii=False)
        print(f"✅ Data saved to '{filename}'")
    except Exception as e:
        print(f"❌ Error saving data: {e}")

def scrape_portfolio(url: str) -> PortfolioData:
    """
    Scrape portfolio website data.
    
    Args:
        url (str): Portfolio website URL
        
    Returns:
        PortfolioData: Structured portfolio information
    """
    try:
        # Normalize URL
        url = normalize_url(url)
        
        # Add random delay to avoid rate limiting
        time.sleep(random.uniform(1, 3))
        
        # Try Playwright first for JavaScript-heavy sites
        html = fetch_with_playwright(url)
        
        # Fallback to regular requests if Playwright fails
        if not html:
            html = fetch_page(url)
            
        if not html:
            raise WebScraperError("Failed to fetch webpage content")
            
        return parse_portfolio(html, url)
        
    except Exception as e:
        raise WebScraperError(f"Error scraping portfolio: {str(e)}")

def main():
    """Main execution function."""
    portfolio_url = "https://yuva-sri-ramesh-portfolio.vercel.app/"
    
    try:
        # Validate URL
        parsed_url = urlparse(portfolio_url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise ValueError("Invalid URL format")
            
        # Scrape portfolio
        result = scrape_portfolio(portfolio_url)
        
        # Save results
        save_to_json(result)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main() 