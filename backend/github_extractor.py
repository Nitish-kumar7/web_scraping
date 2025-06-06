import requests
from typing import Dict, Any
import os
from datetime import datetime

class GitHubAPIError(Exception):
    pass

def fetch_github_profile(username: str) -> Dict[str, Any]:
    """
    Fetch GitHub profile data using the GitHub API.
    
    Args:
        username (str): GitHub username
        
    Returns:
        Dict containing profile information
    """
    base_url = "https://api.github.com"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Candidate-Verification-System"
    }
    
    # Add GitHub token if available
    if token := os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {token}"
    
    try:
        # Get user profile
        user_url = f"{base_url}/users/{username}"
        user_response = requests.get(user_url, headers=headers)
        user_response.raise_for_status()
        user_data = user_response.json()
        
        # Get user repositories
        repos_url = f"{base_url}/users/{username}/repos"
        repos_response = requests.get(repos_url, headers=headers)
        repos_response.raise_for_status()
        repos_data = repos_response.json()
        
        # Get user contributions
        contributions_url = f"{base_url}/users/{username}/events/public"
        contributions_response = requests.get(contributions_url, headers=headers)
        contributions_response.raise_for_status()
        contributions_data = contributions_response.json()
        
        # Process repository data
        languages = {}
        total_stars = 0
        for repo in repos_data:
            # Count stars
            total_stars += repo.get("stargazers_count", 0)
            
            # Get language statistics
            if repo.get("language"):
                languages[repo["language"]] = languages.get(repo["language"], 0) + 1
        
        # Calculate activity score based on contributions
        activity_score = len(contributions_data)
        
        return {
            "name": user_data.get("name"),
            "bio": user_data.get("bio"),
            "location": user_data.get("location"),
            "public_repos": user_data.get("public_repos"),
            "followers": user_data.get("followers"),
            "following": user_data.get("following"),
            "created_at": user_data.get("created_at"),
            "profile_url": user_data.get("html_url"),
            "languages": languages,
            "total_stars": total_stars,
            "activity_score": activity_score,
            "last_updated": datetime.now().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        raise GitHubAPIError(f"Error fetching GitHub data: {str(e)}")
    except Exception as e:
        raise GitHubAPIError(f"Unexpected error: {str(e)}")

def get_repository_details(username: str, repo_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific repository.
    
    Args:
        username (str): GitHub username
        repo_name (str): Repository name
        
    Returns:
        Dict containing repository details
    """
    base_url = "https://api.github.com"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Candidate-Verification-System"
    }
    
    if token := os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {token}"
    
    try:
        repo_url = f"{base_url}/repos/{username}/{repo_name}"
        response = requests.get(repo_url, headers=headers)
        response.raise_for_status()
        repo_data = response.json()
        
        return {
            "name": repo_data.get("name"),
            "description": repo_data.get("description"),
            "language": repo_data.get("language"),
            "stars": repo_data.get("stargazers_count"),
            "forks": repo_data.get("forks_count"),
            "open_issues": repo_data.get("open_issues_count"),
            "created_at": repo_data.get("created_at"),
            "updated_at": repo_data.get("updated_at"),
            "url": repo_data.get("html_url")
        }
        
    except requests.exceptions.RequestException as e:
        raise GitHubAPIError(f"Error fetching repository data: {str(e)}")
    except Exception as e:
        raise GitHubAPIError(f"Unexpected error: {str(e)}") 