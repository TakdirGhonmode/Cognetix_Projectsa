# Resume Shortlisting Automation System

## Project Overview

The Resume Shortlisting Automation System is a Python-based application that helps recruiters automatically screen resumes, extract candidate skills, calculate scores, rank candidates, and generate a shortlist based on job requirements.

This project supports resumes in **PDF**, **DOCX**, and **TXT** formats.

---

## Features

- Parse resumes from PDF, DOCX, and TXT files
- Extract technical skills from resumes
- Extract years of experience
- Match candidate skills with required job skills
- Calculate candidate scores
- Rank candidates based on score
- Export shortlisted candidates to CSV and Excel
- Handle invalid and unsupported files

---

## Technologies Used

- Python 3.10+
- Pandas
- python-docx
- PyPDF2

---

## Project Structure

```
Resume_Shortlisting_Automation_System/
│
├── resumes/
│   ├── candidate1.txt
│   ├── candidate2.docx
│   └── candidate3.pdf
│
├── main.py
├── resume_parser.py
├── skill_matcher.py
├── scoring.py
├── requirements.txt
├── README.md
```

---

## Installation

Install the required libraries:

```bash
pip install pandas python-docx PyPDF2 openpyxl
```

---

## How to Run

Run the project using:

```bash
python main.py
```

Enter the required skills when prompted.

Example:

```
Python, Java, Spring Boot, SQL, MySQL, Git, GitHub, Docker, AWS
```

Enter the number of candidates to shortlist.

Example:

```
3
```

---

## Output

The application generates:

- Ranked candidate list
- Candidate score
- Matched skills
- CSV report
- Excel report

---

## Sample Output

```
========== Resume Shortlisting Automation System ==========

Enter required skills:
Python, Java, Spring Boot, SQL

Enter number of candidates:
3

========== Shortlisted Candidates ==========

Rank : 1
Candidate : Amit Kumar
Matched Skills : Python, Java, SQL, Spring Boot
Score : 100

Rank : 2
Candidate : Priya Verma
Matched Skills : Python, Java, SQL
Score : 82

Rank : 3
Candidate : Rahul Sharma
Matched Skills : Python, SQL
Score : 60
```

---

## Future Improvements

- AI-based resume analysis
- NLP-based skill extraction
- Graphical User Interface (GUI)
- Database integration
- Job Description upload
- Email notification system

---

## Author

**Takdir Mahendra Ghonmode**

Python Internship Project

Cognetix Global Technology LLP
