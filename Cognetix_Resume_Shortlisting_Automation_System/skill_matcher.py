
import re

# Predefined skill dictionary
SKILL_SET = {
    "python", "java", "c", "c++", "javascript", "html", "css",
    "sql", "mysql", "mongodb", "react", "spring", "spring boot",
    "django", "flask", "git", "github", "aws", "docker",
    "pandas", "numpy", "excel", "power bi"
}

# Common certifications
CERTIFICATIONS = [
    "aws certified",
    "azure",
    "oracle",
    "google cloud",
    "python certification",
    "java certification"
]


def extract_skills(text):
    """
    Extract skills from resume text using keyword matching.
    """
    text = text.lower()
    found_skills = []

    for skill in SKILL_SET:
        if skill in text:
            found_skills.append(skill)

    return sorted(list(set(found_skills)))


def extract_experience(text):
    """
    Extract years of experience using regex.
    Examples:
    3 years
    5+ years
    2 yrs
    """
    text = text.lower()

    pattern = r'(\d+)\s*\+?\s*(?:years|year|yrs|yr)'

    match = re.search(pattern, text)

    if match:
        return int(match.group(1))

    return 0


def extract_certifications(text):
    """
    Extract certifications from resume.
    """
    text = text.lower()
    found = []

    for cert in CERTIFICATIONS:
        if cert in text:
            found.append(cert)

    return found


def match_skills(candidate_skills, required_skills):
    """
    Returns matched skills.
    """
    matched = []

    for skill in candidate_skills:
        if skill.lower() in [s.lower() for s in required_skills]:
            matched.append(skill)

    return matched

