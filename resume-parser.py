import os
import re
import json
import pdfplumber
from pydantic import BaseModel, EmailStr, HttpUrl, ValidationError, conint
from typing import List, Optional
from openai import OpenAI
import os
import google.generativeai as genai

# -------------------------------
# 1. Setup OpenAI API Key
# -------------------------------

# -------------------------------
# 2. Define Candidate Schema with Validation
# -------------------------------
class Candidate(BaseModel):
    name: str
    contact_number: str
    gender: Optional[str]
    year_of_experience: str
    years_of_experience: conint(ge=0, le=60)
    number_of_companies: conint(ge=1, le=50)
    current_company_name: str
    Previous_Company_Name: List[str]
    Email_Id: EmailStr
    Primary_SKills: List[str]
    Secondary_SKills: List[str]
    source_file: str
    linkedin_profile: Optional[HttpUrl] = None
    github_profile: Optional[HttpUrl] = None

# -------------------------------
# 3. Function to Extract Text from PDF
# -------------------------------
def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()

# -------------------------------
# 4. Few-Shot Prompt for Resume Parsing
# -------------------------------
FEW_SHOT_EXAMPLES = """
You are an expert resume parser. Extract structured JSON for candidates.
Always return a valid JSON array with one candidate object.
Ensure correct formats: email, phone, int for years, etc.

Example:
Input Resume Text:
"Ratan Kumar Tiple, 15 years experience, worked at Newpark, Capgemini, Accenture.
Email: tipleratan@gmail.com, Contact: +91-9920947920.
LinkedIn: https://linkedin.com/in/ratantiple
GitHub: https://github.com/ratantiple
Skills: Angular, Azure Devops, .NET, SQL, Java"

Output JSON:
[
  {
    "name": "TEST",
    "contact_number": "+91-89562356",
    "gender": "Male",
    "year_of_experience": "15 years",
    "years_of_experience": 15,
    "number_of_companies": 5,
    "current_company_name": "Newpark",
    "Previous_Company_Name": ["Capgemini","Accenture"],
    "Email_Id": "test@gmail.com",
    "Primary_SKills": ["Angular","Azure Devops",".NET","SQL","Java"],
    "Secondary_SKills": ["Bootstrap","Microservices","Cloud"],
    "linkedin_profile": "https://linkedin.com/in/ratantiple",
    "github_profile": "https://github.com/ratantiple",
    "source_file": "resumes/RatanTiple.pdf"
  }
]
"""

def parse_resume_with_gemini(text, file_name):
    prompt = f"""
    You are a strict JSON generator. 
    Extract the following fields from the resume below and return ONLY valid JSON. 
    Do not include explanations, markdown, or extra text.

    Required JSON format:
    {{
        "name": "",
        "contact_number": "",
        "gender": "",
        "years_of_experience": "",
        "number_of_companies": "",
        "current_company_name": "",
        "technology_skills": []
    }}

    Resume Content:
    {text}
    """

    try:
        response = model.generate_content( prompt,
    generation_config={"response_mime_type": "application/json"})
        parsed_json = json.loads(response.text)  # Ensure it’s valid JSON
        return parsed_json
    except Exception as e:
        print(f"❌ Gemini parse failed: {e}")
        return {
            "name": None,
            "contact_number": None,
            "gender": None,
            "years_of_experience": None,
            "number_of_companies": None,
            "current_company_name": None,
            "technology_skills": []
        }

    
def parse_resume_with_openai(resume_text: str, source_file: str):
    prompt = FEW_SHOT_EXAMPLES + f"\n\nInput Resume Text:\n{resume_text}\n\nOutput JSON:"
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Faster + cheaper, use "gpt-4o" for more accuracy
        messages=[
            {"role": "system", "content": "You are a resume parsing AI assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=1000
    )
    
    raw_output = response.choices[0].message.content.strip()
    try:
        candidate_json = json.loads(raw_output)
        # Validate and enrich with source_file
        candidate_json[0]["source_file"] = source_file
        candidate = Candidate(**candidate_json[0])
        return candidate.dict()
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"❌ Parsing/Validation failed for {source_file}: {e}")
        return None

# -------------------------------
# 5. Process All PDFs in a Folder
# -------------------------------
def process_resumes(folder_path: str, output_file: str = "candidates.json"):
    results = []
    for file in os.listdir(folder_path):
        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(folder_path, file)
            text = extract_text_from_pdf(pdf_path)
            #candidate = parse_resume_with_openai(text, pdf_path)
            candidate = parse_resume_with_gemini(text, pdf_path)
            if candidate:
                results.append(candidate)
    
    # Save output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"✅ Parsing complete. Results saved to {output_file}")

# -------------------------------
# Run Script
# -------------------------------
if __name__ == "__main__":
    process_resumes("resumes")  # <-- Change to your folder path
