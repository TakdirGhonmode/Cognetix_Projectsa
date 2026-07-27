import os
from docx import Document
from PyPDF2 import PdfReader


def read_txt(file_path):
    """
    Reads text from a .txt file.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def read_docx(file_path):
    """
    Reads text from a .docx file.
    """
    document = Document(file_path)
    text = []

    for paragraph in document.paragraphs:
        text.append(paragraph.text)

    return "\n".join(text)


def read_pdf(file_path):
    """
    Reads text from a .pdf file.
    """
    reader = PdfReader(file_path)
    text = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)

    return "\n".join(text)


def extract_resume_text(file_path):
    """
    Detects the file type and extracts text.
    """
    extension = os.path.splitext(file_path)[1].lower()

    try:
        if extension == ".txt":
            return read_txt(file_path)

        elif extension == ".docx":
            return read_docx(file_path)

        elif extension == ".pdf":
            return read_pdf(file_path)

        else:
            print(f"Unsupported file format: {file_path}")
            return None

    except Exception as error:
        print(f"Error reading {file_path}")
        print(error)
        return None