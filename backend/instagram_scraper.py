import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
import re
from datetime import datetime
import time
import random

class InstagramScraperError(Exception):
    pass

def get_headers() -> Dict[str, str]:
    """Get headers for Instagram requests."""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

def extract_username_from_url(url: str) -> str:
    """Extract username from Instagram URL."""
    patterns = [
        r'instagram\.com/([^/?]+)',
        r'instagram\.com/([^/?]+)/?$',
        r'@([^/?]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return url  # If no pattern matches, return the input as username

def scrape_instagram_profile(username_or_url: str) -> Dict[str, Any]:
    """
    Scrape public Instagram profile data.
    
    Args:
        username_or_url (str): Instagram username or profile URL
        
    Returns:
        Dict containing profile information
    """
    try:
        # Extract username from URL if needed
        username = extract_username_from_url(username_or_url)
        
        # Construct profile URL
        profile_url = f"https://www.instagram.com/{username}/"
        
        # Add random delay to avoid rate limiting
        time.sleep(random.uniform(1, 3))
        
        # Make request
        response = requests.get(profile_url, headers=get_headers())
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract profile data
        profile_data = {
            "username": username,
            "profile_url": profile_url,
            "scraped_at": datetime.now().isoformat()
        }
        
        # Try to extract bio
        meta_description = soup.find('meta', property='og:description')
        if meta_description:
            profile_data["bio"] = meta_description.get('content', '')
        
        # Try to extract profile picture
        meta_image = soup.find('meta', property='og:image')
        if meta_image:
            profile_data["profile_picture"] = meta_image.get('content', '')
        
        # Extract follower and following counts from bio text
        if "bio" in profile_data:
            bio_text = profile_data["bio"]
            followers_match = re.search(r'(\d+(?:,\d+)*) Followers', bio_text)
            following_match = re.search(r'(\d+(?:,\d+)*) Following', bio_text)
            
            if followers_match:
                profile_data["followers"] = followers_match.group(1)
            if following_match:
                profile_data["following"] = following_match.group(1)
        
        # Extract recent posts (limited to what's visible in the initial HTML)
        posts = []
        post_elements = soup.find_all('article')
        for post in post_elements[:6]:  # Limit to 6 recent posts
            post_data = {
                "type": "image",  # Default type
                "url": "",
                "caption": ""
            }
            
            # Try to get post URL
            link = post.find('a')
            if link:
                post_data["url"] = "https://www.instagram.com" + link.get('href', '')
            
            # Try to get caption
            caption = post.find('div', {'class': '_a9zs'})
            if caption:
                post_data["caption"] = caption.text.strip()
            
            posts.append(post_data)
        
        profile_data["recent_posts"] = posts
        
        return profile_data
        
    except requests.exceptions.RequestException as e:
        raise InstagramScraperError(f"Error fetching Instagram data: {str(e)}")
    except Exception as e:
        raise InstagramScraperError(f"Unexpected error: {str(e)}")

def is_private_profile(username_or_url: str) -> bool:
    """
    Check if an Instagram profile is private.
    
    Args:
        username_or_url (str): Instagram username or profile URL
        
    Returns:
        bool: True if profile is private, False otherwise
    """
    try:
        profile_data = scrape_instagram_profile(username_or_url)
        return "This Account is Private" in profile_data.get("bio", "")
    except InstagramScraperError:
        return True  # Assume private if we can't access the profile 