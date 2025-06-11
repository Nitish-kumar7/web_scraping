from typing import Dict, Any, List, Optional
import os
from datetime import datetime
import json
import re
from dataclasses import dataclass
from github_extractor import fetch_github_profile
from instagram_scraper import InstagramScraper
from web_scraper import scrape_portfolio, PortfolioData
from resume_parser import parse_resume
import google.generativeai as genai
from dotenv import load_dotenv
import pathlib

# Load environment variables from parent directory
parent_dir = pathlib.Path(__file__).parent.parent
env_path = parent_dir / '.env'
load_dotenv(env_path)

class AIAnalysisError(Exception):
    pass

@dataclass
class JobRequirements:
    required_skills: List[str]
    preferred_skills: List[str]
    min_experience_years: int
    min_projects: int
    min_github_stars: int
    min_github_repos: int
    required_education: Optional[str] = None

@dataclass
class CandidateScore:
    overall_score: float
    skill_match_score: float
    experience_score: float
    project_score: float
    github_score: float
    education_score: float
    is_qualified: bool
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]

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

def calculate_skill_match(candidate_skills: List[str], job_skills: List[str], preferred_skills: List[str]) -> Dict[str, Any]:
    """Calculate skill match between candidate and job requirements."""
    candidate_skills = normalize_skills(candidate_skills)
    job_skills = normalize_skills(job_skills)
    preferred_skills = normalize_skills(preferred_skills)
    
    # Calculate matches and missing skills
    matching_required = [skill for skill in candidate_skills if skill in job_skills]
    matching_preferred = [skill for skill in candidate_skills if skill in preferred_skills]
    missing_required = [skill for skill in job_skills if skill not in candidate_skills]
    
    # Calculate match scores
    required_score = len(matching_required) / len(job_skills) * 100 if job_skills else 0
    preferred_score = len(matching_preferred) / len(preferred_skills) * 100 if preferred_skills else 0
    
    # Weighted final score (70% required, 30% preferred)
    final_score = (required_score * 0.7) + (preferred_score * 0.3)
    
    return {
        "match_score": round(final_score, 2),
        "required_match_score": round(required_score, 2),
        "preferred_match_score": round(preferred_score, 2),
        "matching_required_skills": matching_required,
        "matching_preferred_skills": matching_preferred,
        "missing_required_skills": missing_required
    }

def calculate_experience_score(experience: List[Dict], min_years: int) -> float:
    """Calculate experience score based on years of experience."""
    total_years = 0
    for exp in experience:
        if exp.get('date'):
            # Extract years from date string (assuming format like "2020-2022" or "2020-Present")
            years = exp['date'].split('-')
            if len(years) == 2:
                try:
                    start_year = int(years[0])
                    end_year = int(years[1]) if years[1].isdigit() else datetime.now().year
                    total_years += end_year - start_year
                except ValueError:
                    continue
    
    # Calculate score (100% if meets or exceeds minimum, otherwise proportional)
    score = min(100, (total_years / min_years) * 100) if min_years > 0 else 100
    return round(score, 2)

def calculate_project_score(projects: List[Dict], min_projects: int) -> float:
    """Calculate project score based on number and quality of projects."""
    if not projects:
        return 0
    
    # Count projects with descriptions and technologies
    quality_projects = sum(1 for p in projects if p.get('description') and p.get('technologies'))
    
    # Calculate score based on quantity and quality
    quantity_score = min(100, (len(projects) / min_projects) * 100) if min_projects > 0 else 100
    quality_score = (quality_projects / len(projects)) * 100
    
    # Weighted average (60% quantity, 40% quality)
    final_score = (quantity_score * 0.6) + (quality_score * 0.4)
    return round(final_score, 2)

def calculate_github_score(github_data: Dict[str, Any], min_stars: int, min_repos: int) -> float:
    """Calculate GitHub activity score."""
    if not github_data:
        return 0
    
    stars_score = min(100, (github_data.get('total_stars', 0) / min_stars) * 100) if min_stars > 0 else 100
    repos_score = min(100, (github_data.get('repositories', 0) / min_repos) * 100) if min_repos > 0 else 100
    activity_score = github_data.get('activity_score', 0)
    
    # Weighted average (40% stars, 30% repos, 30% activity)
    final_score = (stars_score * 0.4) + (repos_score * 0.3) + (activity_score * 0.3)
    return round(final_score, 2)

def calculate_education_score(education: List[Dict], required_education: Optional[str]) -> float:
    """Calculate education score based on required education level."""
    if not required_education:
        return 100
    
    education_levels = {
        "high school": 1,
        "associate": 2,
        "bachelor": 3,
        "master": 4,
        "phd": 5
    }
    
    required_level = education_levels.get(required_education.lower(), 0)
    if required_level == 0:
        return 100
    
    highest_level = 0
    for edu in education:
        degree = edu.get('degree', '').lower()
        for level, value in education_levels.items():
            if level in degree:
                highest_level = max(highest_level, value)
    
    # Calculate score (100% if meets or exceeds required level, otherwise proportional)
    score = min(100, (highest_level / required_level) * 100)
    return round(score, 2)

def evaluate_candidate(
    portfolio_data: PortfolioData,
    github_data: Optional[Dict[str, Any]],
    job_requirements: JobRequirements
) -> CandidateScore:
    """
    Evaluate candidate's qualifications against job requirements.
    
    Args:
        portfolio_data: Portfolio data from web scraper
        github_data: GitHub profile data
        job_requirements: Job requirements
        
    Returns:
        CandidateScore object with evaluation results
    """
    # Calculate individual scores
    skill_match = calculate_skill_match(
        portfolio_data.skills,
        job_requirements.required_skills,
        job_requirements.preferred_skills
    )
    
    experience_score = calculate_experience_score(
        portfolio_data.experience,
        job_requirements.min_experience_years
    )
    
    project_score = calculate_project_score(
        portfolio_data.projects,
        job_requirements.min_projects
    )
    
    github_score = calculate_github_score(
        github_data,
        job_requirements.min_github_stars,
        job_requirements.min_github_repos
    ) if github_data else 0
    
    education_score = calculate_education_score(
        portfolio_data.education,
        job_requirements.required_education
    )
    
    # Calculate overall score (weighted average)
    weights = {
        "skill_match": 0.35,
        "experience": 0.25,
        "projects": 0.20,
        "github": 0.15,
        "education": 0.05
    }
    
    overall_score = (
        skill_match["match_score"] * weights["skill_match"] +
        experience_score * weights["experience"] +
        project_score * weights["projects"] +
        github_score * weights["github"] +
        education_score * weights["education"]
    )
    
    # Determine if candidate is qualified
    is_qualified = (
        skill_match["required_match_score"] >= 70 and  # At least 70% of required skills
        experience_score >= 70 and  # At least 70% of required experience
        project_score >= 70 and  # At least 70% of required projects
        overall_score >= 75  # Overall score of at least 75%
    )
    
    # Identify strengths and weaknesses
    strengths = []
    weaknesses = []
    
    if skill_match["match_score"] >= 80:
        strengths.append("Strong skill match with job requirements")
    elif skill_match["match_score"] < 60:
        weaknesses.append(f"Missing key skills: {', '.join(skill_match['missing_required_skills'])}")
    
    if experience_score >= 80:
        strengths.append("Meets or exceeds required experience")
    elif experience_score < 60:
        weaknesses.append("Below required experience level")
    
    if project_score >= 80:
        strengths.append("Strong project portfolio")
    elif project_score < 60:
        weaknesses.append("Limited project experience")
    
    if github_score >= 80:
        strengths.append("Active GitHub presence")
    elif github_score < 60:
        weaknesses.append("Limited GitHub activity")
    
    # Generate recommendations
    recommendations = []
    if not is_qualified:
        if skill_match["match_score"] < 70:
            recommendations.append("Focus on acquiring missing required skills")
        if experience_score < 70:
            recommendations.append("Gain more relevant work experience")
        if project_score < 70:
            recommendations.append("Build more projects to showcase skills")
        if github_score < 70:
            recommendations.append("Increase GitHub activity and contributions")
    
    return CandidateScore(
        overall_score=round(overall_score, 2),
        skill_match_score=skill_match["match_score"],
        experience_score=experience_score,
        project_score=project_score,
        github_score=github_score,
        education_score=education_score,
        is_qualified=is_qualified,
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recommendations
    )

def generate_candidate_summary(score: CandidateScore) -> str:
    """Generate a human-readable summary of the candidate evaluation."""
    summary_parts = []
    
    # Overall assessment
    summary_parts.append(f"Overall Score: {score.overall_score}%")
    summary_parts.append(f"Qualification Status: {'Qualified' if score.is_qualified else 'Not Qualified'}")
    summary_parts.append("\nDetailed Scores:")
    summary_parts.append(f"- Skill Match: {score.skill_match_score}%")
    summary_parts.append(f"- Experience: {score.experience_score}%")
    summary_parts.append(f"- Projects: {score.project_score}%")
    summary_parts.append(f"- GitHub Activity: {score.github_score}%")
    summary_parts.append(f"- Education: {score.education_score}%")
    
    # Strengths
    if score.strengths:
        summary_parts.append("\nStrengths:")
        for strength in score.strengths:
            summary_parts.append(f"- {strength}")
    
    # Weaknesses
    if score.weaknesses:
        summary_parts.append("\nAreas for Improvement:")
        for weakness in score.weaknesses:
            summary_parts.append(f"- {weakness}")
    
    # Recommendations
    if score.recommendations:
        summary_parts.append("\nRecommendations:")
        for rec in score.recommendations:
            summary_parts.append(f"- {rec}")
    
    return "\n".join(summary_parts)

# Configure Gemini
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY not found in environment variables")
    print("Please set your Google API key in the .env file in the web_scraping directory")
    print("You can get an API key from: https://makersuite.google.com/app/apikey")
    gemini_model = None
else:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-pro')
        print("✅ Gemini AI model configured successfully")
    except Exception as e:
        print(f"Warning: Gemini configuration failed: {e}")
        gemini_model = None

def extract_skills_with_gemini(text: str) -> List[str]:
    """Extract skills from text using Gemini."""
    if not gemini_model:
        return extract_skills_from_text(text)  # Fallback to regex-based extraction
        
    prompt = f"""
    Extract technical skills from the following text. Return only a JSON array of skills.
    Focus on programming languages, frameworks, tools, and technologies.
    Example output format: ["Python", "React", "AWS"]
    
    Text to analyze:
    {text}
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        skills = json.loads(response.text)
        return skills
    except Exception as e:
        print(f"Warning: Gemini skill extraction failed: {e}")
        return extract_skills_from_text(text)  # Fallback to regex-based extraction

def match_skills_with_gemini(candidate_skills: List[str], job_skills: List[str]) -> Dict[str, Any]:
    """Match candidate skills with job requirements using Gemini."""
    if not gemini_model:
        return calculate_skill_match(candidate_skills, job_skills, [])  # Fallback to basic matching
        
    prompt = f"""
    Compare the candidate's skills with the job requirements and provide a detailed analysis.
    Return a JSON object with the following structure:
    {{
        "match_score": float,  # Overall match percentage (0-100)
        "matching_skills": List[str],  # Skills that match
        "missing_skills": List[str],  # Required skills that are missing
        "skill_gaps": List[str],  # Detailed analysis of skill gaps
        "recommendations": List[str]  # Recommendations for improvement
    }}

    Candidate Skills: {json.dumps(candidate_skills)}
    Job Requirements: {json.dumps(job_skills)}
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        analysis = json.loads(response.text)
        return analysis
    except Exception as e:
        print(f"Warning: Gemini skill matching failed: {e}")
        return calculate_skill_match(candidate_skills, job_skills, [])  # Fallback to basic matching

def analyze_candidate(
    portfolio_url: str,
    job_requirements: JobRequirements,
    github_url: Optional[str] = None,
    instagram_handle: Optional[str] = None,
    job_description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze a candidate's qualifications based on their portfolio and other data.
    Uses Gemini for skill extraction and matching.
    """
    try:
        # Scrape portfolio data
        portfolio_data = scrape_portfolio(portfolio_url)
        
        # Extract skills using Gemini
        all_text = f"{portfolio_data.description} {' '.join(portfolio_data.skills)}"
        if job_description:
            all_text += f" {job_description}"
        
        extracted_skills = extract_skills_with_gemini(all_text)
        
        # Fetch GitHub data if URL provided
        github_data = None
        if github_url:
            try:
                github_data = fetch_github_profile(github_url)
            except Exception as e:
                print(f"Warning: Could not fetch GitHub data: {str(e)}")
        
        # Fetch Instagram data if handle provided
        instagram_data = None
        if instagram_handle:
            try:
                instagram_data = scrape_instagram_profile(instagram_handle)
            except Exception as e:
                print(f"Warning: Could not fetch Instagram data: {str(e)}")
        
        # Match skills using Gemini
        skill_analysis = match_skills_with_gemini(extracted_skills, job_requirements.required_skills)
        
        # Calculate other scores
        experience_score = calculate_experience_score(portfolio_data.experience, job_requirements.min_experience_years)
        project_score = calculate_project_score(portfolio_data.projects, job_requirements.min_projects)
        github_score = calculate_github_score(github_data, job_requirements.min_github_stars, job_requirements.min_github_repos)
        education_score = calculate_education_score(portfolio_data.education, job_requirements.required_education)
        
        # Calculate overall score
        overall_score = (
            skill_analysis.get('match_score', 0) * 0.4 +
            experience_score * 0.2 +
            project_score * 0.2 +
            github_score * 0.1 +
            education_score * 0.1
        )
        
        # Create evaluation result using CandidateScore dataclass
        evaluation = CandidateScore(
            overall_score=round(overall_score, 2),
            skill_match_score=skill_analysis.get('match_score', 0),
            experience_score=experience_score,
            project_score=project_score,
            github_score=github_score,
            education_score=education_score,
            is_qualified=overall_score >= 70,  # Consider qualified if score >= 70%
            strengths=skill_analysis.get('matching_skills', []),
            weaknesses=skill_analysis.get('missing_skills', []),
            recommendations=skill_analysis.get('recommendations', [])
        )
        
        # Generate summary
        summary = generate_candidate_summary(evaluation)
        
        return {
            "evaluation": evaluation.__dict__,
            "summary": summary,
            "portfolio_data": portfolio_data.__dict__,
            "github_data": github_data,
            "instagram_data": instagram_data,
            "job_requirements": job_requirements.__dict__,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise AIAnalysisError(f"Error analyzing candidate: {str(e)}")

def scrape_instagram_profile(username: str) -> Dict[str, Any]:
    """Helper function to scrape Instagram profile using InstagramScraper class."""
    scraper = InstagramScraper()
    try:
        return scraper.scrape_profile(username)
    finally:
        if scraper.driver:
            scraper.driver.quit()

def main():
    """Example usage of the candidate analysis system."""
    # Example job requirements
    requirements = JobRequirements(
        required_skills=["Python", "JavaScript", "React", "Node.js"],
        preferred_skills=["TypeScript", "AWS", "Docker"],
        min_experience_years=2,
        min_projects=3,
        min_github_stars=10,
        min_github_repos=5,
        required_education="bachelor"
    )
    
    # Analyze candidate
    try:
        results = analyze_candidate(
            portfolio_url="https://example-portfolio.com",
            job_requirements=requirements,
            github_url="https://github.com/example"
        )
        
        # Print summary
        print(results["summary"])
        
        # Save detailed results
        with open("candidate_analysis.json", "w") as f:
            json.dump(results, f, indent=2)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 