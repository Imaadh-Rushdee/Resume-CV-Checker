import json
import re
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("API_KEY"))  # Change this when switching providers


def parse_resume(text: str) -> dict:
    """Send resume text to AI and return structured JSON."""
    prompt = f"""
You are an intelligent resume parser.

Extract information from the resume and return ONLY valid JSON.
No explanations. No markdown. No extra text.

Rules:
- Use fixed schema fields when data exists.
- Any extra info (address, certifications, languages, awards, projects) goes into "extra_fields".
- Do NOT guess values; if not found, return null or empty array.

Schema:
{{
  "name": null | string,
  "email": null | string,
  "phone": null | string,
  "linkedin": null | string,
  "github": null | string,
  "date_of_birth": null | string,
  "job_role": null | string,
  "technical_skills": string[],
  "soft_skills": string[],
  "education": string[],
  "experience": string[],
  "extra_fields": object
}}

Resume Text:
{text}
"""
    try:
        response = client.responses.create(model="gpt-4o-mini", input=prompt, temperature=0)
        return json.loads(response.output_text)
    except Exception as e:
        print("❌ AI parsing failed:", e)
        return {}


def recommend_roles(data: dict, requested_role: str = None) -> list:
    """Return recommended job roles and indicate match with requested role."""
    prompt = f"""
Resume Data: {json.dumps(data)}
Requested Role: {requested_role or "None"}

Suggest 3-5 suitable job roles for this candidate.
Indicate for each role if it matches the requested role with yes/no.
Return JSON array like:
[{{"role": "Web Developer", "match_requested_role": "yes"}}, ...]
Only return JSON, no explanations.
"""
    try:
        response = client.responses.create(model="gpt-4o-mini", input=prompt, temperature=0)
        text = response.output_text.strip()
        match = re.search(r'\[.*\]', text, re.DOTALL)
        return json.loads(match.group(0)) if match else []
    except Exception as e:
        print("❌ Failed to recommend roles:", e)
        return []


def resume_score(data: dict, job_description: str, role_level: str = "Beginner") -> dict:
    """AI-assisted resume scoring (10 categories)."""
    prompt = f"""
You are a professional hiring assistant.

Candidate Resume Data: {json.dumps(data)}
Job Description: {job_description}
Role Level: {role_level}

Evaluate the resume and assign scores for the following 10 categories:
1. Education
2. Experience
3. Technical Skills
4. Soft Skills
5. Projects
6. Certifications / Training
7. Achievements / Awards
8. Extra Skills
9. Professional Online Presence
10. Overall Presentation

Rules:
- Each category score should be 0-20.
- Score relevant categories higher; ignore irrelevant ones for this job type.
- Return JSON only, with category names as keys and scores as values.
- Include "Total Score" and "Percentage".
- No extra text.

Output Example:
{{
  "Education": 15,
  "Experience": 10,
  "Technical Skills": 18,
  "Soft Skills": 12,
  "Projects": 20,
  "Certifications": 10,
  "Achievements": 5,
  "Extra Skills": 8,
  "Online Presence": 10,
  "Presentation": 10,
  "Total Score": 118,
  "Percentage": 59.0
}}
"""
    try:
        response = client.responses.create(model="gpt-4o-mini", input=prompt, temperature=0)
        text = response.output_text.strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        return json.loads(match.group(0)) if match else {}
    except Exception as e:
        print("❌ AI scoring failed:", e)
        return {}


def ats_score(data: dict, job_description: str, requested_role: str = None) -> int:
    """Return ATS score (0-100) comparing resume to job description."""
    prompt = f"""
Resume Data: {json.dumps(data)}
Requested Role: {requested_role or "None"}
Job Description: {job_description}

Evaluate how well this resume matches the requested role and job description.
Return ONLY an integer 0-100, no explanations.
"""
    try:
        response = client.responses.create(model="gpt-4o-mini", input=prompt, temperature=0)
        match = re.search(r'\d+', response.output_text.strip())
        return int(match.group(0)) if match else 0
    except Exception as e:
        print("❌ Failed ATS score:", e)
        return 0
