import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import re
from datetime import datetime
import time
import random
from urllib.parse import urlparse, urljoin

class WebScraperError(Exception):
    pass

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

def extract_projects(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Extract project information from the page."""
    projects = []
    
    # Look for common project section patterns
    project_sections = soup.find_all(['section', 'div'], class_=re.compile(r'project|portfolio|work', re.IGNORECASE))
    
    for section in project_sections:
        project = {
            "title": "",
            "description": "",
            "technologies": [],
            "url": ""
        }
        
        # Try to find project title
        title_elem = section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if title_elem:
            project["title"] = title_elem.text.strip()
        
        # Try to find project description
        desc_elem = section.find(['p', 'div'], class_=re.compile(r'description|about|summary', re.IGNORECASE))
        if desc_elem:
            project["description"] = desc_elem.text.strip()
        
        # Try to find technologies used
        tech_elem = section.find(['div', 'ul'], class_=re.compile(r'tech|stack|tools|skills', re.IGNORECASE))
        if tech_elem:
            tech_list = tech_elem.find_all(['li', 'span'])
            project["technologies"] = [tech.text.strip() for tech in tech_list]
        
        # Try to find project URL
        link_elem = section.find('a', href=True)
        if link_elem:
            project["url"] = link_elem['href']
        
        if project["title"] or project["description"]:
            projects.append(project)
    
    return projects

def extract_skills(soup: BeautifulSoup) -> List[str]:
    """Extract skills from the page."""
    skills = []
    
    # Look for common skills section patterns
    skills_sections = soup.find_all(['section', 'div'], class_=re.compile(r'skill|expertise|technologies', re.IGNORECASE))
    
    for section in skills_sections:
        skill_elements = section.find_all(['li', 'span', 'div'])
        for elem in skill_elements:
            skill = elem.text.strip()
            if skill and len(skill) < 50:  # Avoid long text that's probably not a skill
                skills.append(skill)
    
    return list(set(skills))  # Remove duplicates

def scrape_portfolio(url: str) -> Dict[str, Any]:
    """
    Scrape portfolio website data.
    
    Args:
        url (str): Portfolio website URL
        
    Returns:
        Dict containing portfolio information
    """
    try:
        # Normalize URL
        url = normalize_url(url)
        
        # Add random delay to avoid rate limiting
        time.sleep(random.uniform(1, 3))
        
        # Make request
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract data
        portfolio_data = {
            "url": url,
            "title": soup.title.string if soup.title else "",
            "scraped_at": datetime.now().isoformat(),
            "social_links": extract_social_links(soup, url),
            "projects": extract_projects(soup),
            "skills": extract_skills(soup),
            "internal_links": extract_links(soup, url)
        }
        
        # Try to extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            portfolio_data["description"] = meta_desc.get('content', '')
        
        return portfolio_data
        
    except requests.exceptions.RequestException as e:
        raise WebScraperError(f"Error fetching website data: {str(e)}")
    except Exception as e:
        raise WebScraperError(f"Unexpected error: {str(e)}")

def is_portfolio_website(url: str) -> bool:
    """
    Check if a website is likely a portfolio website.
    
    Args:
        url (str): Website URL
        
    Returns:
        bool: True if likely a portfolio website, False otherwise
    """
    try:
        portfolio_data = scrape_portfolio(url)
        
        # Check for portfolio indicators
        indicators = [
            len(portfolio_data["projects"]) > 0,
            len(portfolio_data["skills"]) > 0,
            any(keyword in portfolio_data["title"].lower() for keyword in 
                ["portfolio", "projects", "work", "developer", "designer", "engineer"]),
            any(keyword in portfolio_data.get("description", "").lower() for keyword in 
                ["portfolio", "projects", "work", "developer", "designer", "engineer"])
        ]
        
        return any(indicators)
    except WebScraperError:
        return False 