import os
import pandas as pd

from resume_parser import extract_resume_text
from skill_matcher import (
    extract_skills,
    extract_experience,
    extract_certifications,
    match_skills,
)
from scoring import calculate_score, rank_candidates


def main():
    print("========== Resume Shortlisting Automation System ==========\n")

    # Load Job Criteria
    required_skills = input(
        "Enter required skills (comma separated): "
    ).lower().split(",")

    required_skills = [skill.strip() for skill in required_skills]

    top_n = int(input("Enter number of candidates to shortlist: "))

    resume_folder = "resumes"

    candidates = []

    if not os.path.exists(resume_folder):
        print("Resumes folder not found.")
        return

    for file_name in os.listdir(resume_folder):

        file_path = os.path.join(resume_folder, file_name)

        text = extract_resume_text(file_path)

        if not text:
            print(f"Skipping {file_name}")
            continue

        skills = extract_skills(text)

        experience = extract_experience(text)

        certifications = extract_certifications(text)

        matched = match_skills(skills, required_skills)

        score = calculate_score(
            matched,
            required_skills,
            experience,
        )

        candidate = {
            "Candidate Name": os.path.splitext(file_name)[0],
            "Matched Skills": ", ".join(matched),
            "Experience": experience,
            "Certifications": ", ".join(certifications),
            "Score": score,
        }

        candidates.append(candidate)

    if not candidates:
        print("No valid resumes found.")
        return

    ranked_candidates = rank_candidates(candidates)

    shortlist = ranked_candidates[:top_n]

    df = pd.DataFrame(shortlist)

    df.to_csv("shortlist.csv", index=False)

    df.to_excel("shortlist.xlsx", index=False)

    print("\n========== Shortlisted Candidates ==========\n")

    print(df)

    print("\nCSV file generated successfully.")

    print("Excel file generated successfully.")


if __name__ == "__main__":
    main()