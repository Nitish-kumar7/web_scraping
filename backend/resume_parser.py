import pdfplumber
import docx
import io
from typing import Dict, Any, List
import re
from datetime import datetime

class ResumeParserError(Exception):
    pass

def extract_text_from_pdf(content: bytes) -> str:
    """
    Extract text from PDF content.
    
    Args:
        content (bytes): PDF file content
        
    Returns:
        str: Extracted text
    """
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            return text
    except Exception as e:
        raise ResumeParserError(f"Error extracting text from PDF: {str(e)}")

def extract_text_from_docx(content: bytes) -> str:
    """
    Extract text from DOCX content.
    
    Args:
        content (bytes): DOCX file content
        
    Returns:
        str: Extracted text
    """
    try:
        doc = docx.Document(io.BytesIO(content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        raise ResumeParserError(f"Error extracting text from DOCX: {str(e)}")

def extract_email(text: str) -> str:
    """Extract email address from text."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group(0) if match else ""

def extract_phone(text: str) -> str:
    """Extract phone number from text."""
    phone_pattern = r'\+?[\d\s-]{10,}'
    match = re.search(phone_pattern, text)
    return match.group(0) if match else ""

def extract_skills(text: str) -> List[str]:
    """Extract skills from text."""
    # Common technical skills to look for
    common_skills = [
        "Python", "Java", "JavaScript", "C++", "C#", "Ruby", "PHP",
        "HTML", "CSS", "React", "Angular", "Vue", "Node.js", "Django",
        "Flask", "Spring", "Express", "MongoDB", "MySQL", "PostgreSQL",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git", "Linux",
        "Agile", "Scrum", "DevOps", "CI/CD", "REST", "GraphQL", "API"
    ]
    
    found_skills = []
    for skill in common_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            found_skills.append(skill)
    
    return found_skills

def extract_education(text: str) -> List[Dict[str, str]]:
    """Extract education information from text."""
    education = []
    # Look for common education patterns
    edu_patterns = [
        r'(Bachelor|Master|PhD|B\.?Tech|M\.?Tech|B\.?E|M\.?E|B\.?Sc|M\.?Sc)[^.]*',
        r'University of [^.]*',
        r'[A-Z][a-z]+ University',
        r'[A-Z][a-z]+ Institute'
    ]
    
    for pattern in edu_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            education.append({
                "degree": match.group(0),
                "year": "",  # Could be enhanced with year extraction
                "institution": ""  # Could be enhanced with institution extraction
            })
    
    return education

def extract_experience(text: str) -> List[Dict[str, str]]:
    """Extract work experience from text."""
    experience = []
    # Look for common experience patterns
    exp_patterns = [
        r'(Senior|Junior|Lead)?\s*(Software|Web|Mobile|Full Stack|Frontend|Backend|DevOps|Data|ML|AI)\s*(Engineer|Developer|Architect|Scientist)',
        r'(Software|Web|Mobile|Full Stack|Frontend|Backend|DevOps|Data|ML|AI)\s*(Engineer|Developer|Architect|Scientist)',
        r'(Project|Team|Technical)\s*(Manager|Lead|Architect)'
    ]
    
    for pattern in exp_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            experience.append({
                "title": match.group(0),
                "company": "",  # Could be enhanced with company extraction
                "duration": "",  # Could be enhanced with duration extraction
                "description": ""  # Could be enhanced with description extraction
            })
    
    return experience

def parse_resume(content: bytes, filename: str) -> Dict[str, Any]:
    """
    Parse resume content and extract relevant information.
    
    Args:
        content (bytes): Resume file content
        filename (str): Name of the resume file
        
    Returns:
        Dict containing parsed resume information
    """
    try:
        # Determine file type and extract text
        if filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(content)
        elif filename.lower().endswith('.docx'):
            text = extract_text_from_docx(content)
        else:
            raise ResumeParserError("Unsupported file format")
        
        # Extract information
        return {
            "email": extract_email(text),
            "phone": extract_phone(text),
            "skills": extract_skills(text),
            "education": extract_education(text),
            "experience": extract_experience(text),
            "raw_text": text,
            "parsed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise ResumeParserError(f"Error parsing resume: {str(e)}") 