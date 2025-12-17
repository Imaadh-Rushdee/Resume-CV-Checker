import pdfplumber
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils import ai_provider


pdf_path = "../../my_cv_se.pdf"


def extract_pdf_data(resume_pdf: str) -> str:
    """Extract text from PDF."""
    raw_text = ""
    with pdfplumber.open(resume_pdf) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                raw_text += text + "\n"
    print("✅ Extracted Data")
    return raw_text


if __name__ == "__main__":
    raw = extract_pdf_data(pdf_path)
    extracted_info = ai_provider.parse_resume(raw)

    print("\nFinal Extracted Info:")
    print(json.dumps(extracted_info, indent=2))

    requested_role = extracted_info.get("job_role", "Intern")
    recommended = ai_provider.recommend_roles(extracted_info, requested_role)
    print("\nRecommended Roles:", recommended)

    print("Resume Score (Beginner):", ai_provider.resume_score(extracted_info, requested_role, "Beginner"))
    print("Resume Score (Intermediate):", ai_provider.resume_score(extracted_info, requested_role, "Intermediate"))
    print("Resume Score (Advanced):", ai_provider.resume_score(extracted_info, requested_role, "Advanced"))

    job_desc = requested_role  # or a more detailed JD
    print("ATS Score:", ai_provider.ats_score(extracted_info, job_desc, requested_role))
