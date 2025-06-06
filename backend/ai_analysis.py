from typing import Dict, Any, List, Optional
import os
from datetime import datetime
import json
import re
from github_extractor import fetch_github_profile
from instagram_scraper import scrape_instagram_profile
from web_scraper import scrape_portfolio
from resume_parser import parse_resume

class AIAnalysisError(Exception):
    pass

def normalize_skills(skills: List[str]) -> List[str]:
    """Normalize and standardize skill names."""
    skill_mapping = {
        # Programming Languages
        "python": "Python",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "java": "Java",
        "c++": "C++",
        "c#": "C#",
        "ruby": "Ruby",
        "php": "PHP",
        "go": "Go",
        "rust": "Rust",
        "swift": "Swift",
        "kotlin": "Kotlin",
        
        # Web Technologies
        "html": "HTML",
        "css": "CSS",
        "react": "React",
        "angular": "Angular",
        "vue": "Vue.js",
        "node": "Node.js",
        "express": "Express.js",
        "django": "Django",
        "flask": "Flask",
        "spring": "Spring",
        "laravel": "Laravel",
        
        # Databases
        "mysql": "MySQL",
        "postgresql": "PostgreSQL",
        "mongodb": "MongoDB",
        "redis": "Redis",
        "elasticsearch": "Elasticsearch",
        
        # Cloud & DevOps
        "aws": "AWS",
        "azure": "Azure",
        "gcp": "GCP",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "jenkins": "Jenkins",
        "git": "Git",
        "ci/cd": "CI/CD",
        
        # Other
        "agile": "Agile",
        "scrum": "Scrum",
        "devops": "DevOps",
        "rest": "REST",
        "graphql": "GraphQL",
        "api": "API"
    }
    
    normalized_skills = []
    for skill in skills:
        skill_lower = skill.lower()
        if skill_lower in skill_mapping:
            normalized_skills.append(skill_mapping[skill_lower])
        else:
            normalized_skills.append(skill)
    
    return list(set(normalized_skills))  # Remove duplicates

def extract_skills_from_text(text: str) -> List[str]:
    """Extract skills from text using common patterns."""
    # Common technical skills to look for
    common_skills = [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Ruby", "PHP",
        "HTML", "CSS", "React", "Angular", "Vue", "Node.js", "Django", "Flask",
        "Spring", "Express", "MongoDB", "MySQL", "PostgreSQL", "AWS", "Azure",
        "GCP", "Docker", "Kubernetes", "Git", "Linux", "Agile", "Scrum", "DevOps",
        "CI/CD", "REST", "GraphQL", "API"
    ]
    
    found_skills = []
    for skill in common_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            found_skills.append(skill)
    
    return found_skills

def calculate_skill_match(candidate_skills: List[str], job_skills: List[str]) -> Dict[str, Any]:
    """Calculate skill match between candidate and job requirements."""
    candidate_skills = normalize_skills(candidate_skills)
    job_skills = normalize_skills(job_skills)
    
    # Calculate matches and missing skills
    matching_skills = [skill for skill in candidate_skills if skill in job_skills]
    missing_skills = [skill for skill in job_skills if skill not in candidate_skills]
    
    # Calculate match score
    if not job_skills:
        match_score = 0
    else:
        match_score = len(matching_skills) / len(job_skills) * 100
    
    return {
        "match_score": round(match_score, 2),
        "matching_skills": matching_skills,
        "missing_skills": missing_skills
    }

def analyze_github_profile(username: str) -> Dict[str, Any]:
    """Analyze GitHub profile data."""
    try:
        profile_data = fetch_github_profile(username)
        
        # Extract skills from repositories
        skills = []
        for repo in profile_data.get("repos", []):
            if repo.get("language"):
                skills.append(repo["language"])
        
        # Calculate activity metrics
        activity_score = profile_data.get("activity_score", 0)
        total_stars = profile_data.get("total_stars", 0)
        
        return {
            "skills": normalize_skills(skills),
            "activity_score": activity_score,
            "total_stars": total_stars,
            "repositories": len(profile_data.get("repos", [])),
            "followers": profile_data.get("followers", 0)
        }
    except Exception as e:
        raise AIAnalysisError(f"Error analyzing GitHub profile: {str(e)}")

def analyze_portfolio(url: str) -> Dict[str, Any]:
    """Analyze portfolio website data."""
    try:
        portfolio_data = scrape_portfolio(url)
        
        # Extract skills from projects and skills sections
        skills = set()
        for project in portfolio_data.get("projects", []):
            skills.update(project.get("technologies", []))
        skills.update(portfolio_data.get("skills", []))
        
        return {
            "skills": normalize_skills(list(skills)),
            "projects_count": len(portfolio_data.get("projects", [])),
            "social_links": portfolio_data.get("social_links", {})
        }
    except Exception as e:
        raise AIAnalysisError(f"Error analyzing portfolio: {str(e)}")

def analyze_candidate(
    github_url: Optional[str] = None,
    instagram_url: Optional[str] = None,
    portfolio_url: Optional[str] = None,
    job_description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze candidate data from multiple sources.
    
    Args:
        github_url (str, optional): GitHub profile URL
        instagram_url (str, optional): Instagram profile URL
        portfolio_url (str, optional): Portfolio website URL
        job_description (str, optional): Job description text
        
    Returns:
        Dict containing analysis results
    """
    try:
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "sources_analyzed": [],
            "skills": [],
            "skill_match": None
        }
        
        # Extract skills from job description
        job_skills = []
        if job_description:
            job_skills = extract_skills_from_text(job_description)
        
        # Analyze GitHub profile
        if github_url:
            github_analysis = analyze_github_profile(github_url)
            analysis["skills"].extend(github_analysis["skills"])
            analysis["github_analysis"] = github_analysis
            analysis["sources_analyzed"].append("github")
        
        # Analyze portfolio
        if portfolio_url:
            portfolio_analysis = analyze_portfolio(portfolio_url)
            analysis["skills"].extend(portfolio_analysis["skills"])
            analysis["portfolio_analysis"] = portfolio_analysis
            analysis["sources_analyzed"].append("portfolio")
        
        # Normalize and deduplicate skills
        analysis["skills"] = normalize_skills(analysis["skills"])
        
        # Calculate skill match if job description is provided
        if job_skills:
            analysis["skill_match"] = calculate_skill_match(analysis["skills"], job_skills)
        
        return analysis
        
    except Exception as e:
        raise AIAnalysisError(f"Error analyzing candidate data: {str(e)}")

def generate_candidate_summary(analysis: Dict[str, Any]) -> str:
    """Generate a human-readable summary of the candidate analysis."""
    try:
        summary_parts = []
        
        # Add skills summary
        if analysis["skills"]:
            summary_parts.append(f"Technical Skills: {', '.join(analysis['skills'])}")
        
        # Add GitHub analysis if available
        if "github_analysis" in analysis:
            github = analysis["github_analysis"]
            summary_parts.append(
                f"GitHub Activity: {github['repositories']} repositories, "
                f"{github['followers']} followers, {github['total_stars']} stars"
            )
        
        # Add portfolio analysis if available
        if "portfolio_analysis" in analysis:
            portfolio = analysis["portfolio_analysis"]
            summary_parts.append(
                f"Portfolio: {portfolio['projects_count']} projects showcased"
            )
        
        # Add skill match if available
        if analysis["skill_match"]:
            match = analysis["skill_match"]
            summary_parts.append(
                f"Skill Match: {match['match_score']}% "
                f"({len(match['matching_skills'])} matching skills)"
            )
            if match["missing_skills"]:
                summary_parts.append(
                    f"Missing Skills: {', '.join(match['missing_skills'])}"
                )
        
        return "\n".join(summary_parts)
        
    except Exception as e:
        raise AIAnalysisError(f"Error generating summary: {str(e)}") 