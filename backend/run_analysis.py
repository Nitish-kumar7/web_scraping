from ai_analysis import analyze_candidate, JobRequirements
from web_scraper import scrape_portfolio
import json
from typing import Dict, Any, List

def get_user_input() -> tuple:
    """Get user input for candidate analysis with default values for skills and requirements."""
    print("\n🤖 AI Skill Matching Engine")
    print("=" * 50)
    
    # Get candidate information
    print("\n📝 Candidate Information:")
    portfolio_url = input("Enter portfolio URL: ").strip()
    github_username = input("Enter GitHub username: ").strip()
    instagram_handle = input("Enter Instagram handle: ").strip()
    
    # Default required skills for a full-stack developer
    required_skills = [
        "Python",
        "JavaScript",
        "HTML",
        "CSS",
        "React",
        "Node.js",
        "Git",
        "SQL",
        "REST",
        "API"
    ]
    
    # Default preferred skills
    preferred_skills = [
        "TypeScript",
        "AWS",
        "Docker",
        "MongoDB",
        "Express.js",
        "Redux",
        "GraphQL",
        "CI/CD",
        "Agile",
        "DevOps"
    ]
    
    # Default requirements
    requirements = JobRequirements(
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        min_experience_years=1,
        min_projects=2,
        min_github_stars=5,
        min_github_repos=3,
        required_education="bachelor"
    )
    
    print("\n✅ Using default requirements for Full Stack Developer position")
    print("Required Skills:", ", ".join(required_skills))
    print("Preferred Skills:", ", ".join(preferred_skills))
    print("Minimum Requirements:")
    print(f"- Experience: {requirements.min_experience_years} years")
    print(f"- Projects: {requirements.min_projects}")
    print(f"- GitHub Stars: {requirements.min_github_stars}")
    print(f"- GitHub Repos: {requirements.min_github_repos}")
    print(f"- Education: {requirements.required_education}")
    
    return portfolio_url, github_username, instagram_handle, requirements

def save_analysis_results(results: Dict[str, Any], filename: str = "candidate_analysis.json") -> None:
    """Save analysis results to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"✅ Analysis results saved to {filename}")

def display_skill_matching(results: Dict[str, Any]) -> None:
    """Display skill matching results in a clear format."""
    evaluation = results["evaluation"]
    
    print("\n📊 Skill Matching Results")
    print("=" * 50)
    
    # Display overall score
    print(f"\n🎯 Overall Match Score: {evaluation['overall_score']}%")
    print(f"Qualified: {'✅ Yes' if evaluation['is_qualified'] else '❌ No'}")
    
    # Display skill matches
    print("\n🔍 Skill Analysis:")
    print("-" * 30)
    
    # Required skills
    print("Matching Required Skills:")
    matching_required = evaluation.get("matching_required_skills", [])
    if matching_required:
        for skill in matching_required:
            print(f"✅ {skill}")
    else:
        print("No matching required skills found")
    
    # Preferred skills
    print("\nMatching Preferred Skills:")
    matching_preferred = evaluation.get("matching_preferred_skills", [])
    if matching_preferred:
        for skill in matching_preferred:
            print(f"✨ {skill}")
    else:
        print("No matching preferred skills found")
    
    # Missing skills
    print("\nMissing Required Skills:")
    missing_required = evaluation.get("missing_required_skills", [])
    if missing_required:
        for skill in missing_required:
            print(f"❌ {skill}")
    else:
        print("No missing required skills")
    
    # Display other scores
    print("\n📈 Detailed Scores:")
    print(f"Skill Match Score: {evaluation['skill_match_score']}%")
    print(f"Experience Score: {evaluation['experience_score']}%")
    print(f"Project Score: {evaluation['project_score']}%")
    print(f"GitHub Score: {evaluation['github_score']}%")
    print(f"Education Score: {evaluation['education_score']}%")
    
    # Display recommendations
    if evaluation.get('recommendations'):
        print("\n💡 Recommendations for Improvement:")
        for rec in evaluation['recommendations']:
            print(f"- {rec}")

def main():
    try:
        print("🔍 Starting AI Skill Matching Engine...")
        
        # Get user input
        portfolio_url, github_username, instagram_handle, requirements = get_user_input()
        
        # Run the analysis
        results = analyze_candidate(
            portfolio_url=portfolio_url,
            job_requirements=requirements,
            github_url=github_username,
            instagram_handle=instagram_handle
        )
        
        # Display results
        display_skill_matching(results)
        
        # Save detailed results
        save_analysis_results(results)
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")

if __name__ == "__main__":
    main() 