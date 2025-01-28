from pathlib import Path
import random
from pypdf import PdfReader


def get_random_file_from_directory(directory: Path) -> Path:
    files = list(directory.glob("*"))
    return random.choice(files) if files else None  # type: ignore


def get_pdf_text(pdf_path: Path) -> str:
    if not str(pdf_path).endswith(".pdf"):
        with open(pdf_path, "r") as fp:
            return fp.read()

    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text
