"""PDF text extraction with OCR fallback for scanned documents."""

import os
from pathlib import Path
from typing import Optional

from .config import get_config, get_tesseract_path


def read_file(file_path: str) -> str:
    """
    Read text from a PDF or TXT file.

    For PDFs: attempts pdfplumber first. Falls back to pytesseract OCR
    if extracted text is sparse (< min_chars_per_page per page).
    For TXT files: reads directly.

    Args:
        file_path: Path to the PDF or TXT file.

    Returns:
        Extracted text as a single string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file type is unsupported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()
    if ext == ".txt":
        return _read_txt(path)
    elif ext == ".pdf":
        return _read_pdf(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Expected .pdf or .txt")


def _read_txt(path: Path) -> str:
    """Read text directly from a .txt file."""
    return path.read_text(encoding="utf-8", errors="replace")


def _read_pdf(path: Path) -> str:
    """Read PDF using pdfplumber; fall back to OCR if text is sparse."""
    try:
        import pdfplumber
    except ImportError:
        raise ImportError(
            "pdfplumber is required for PDF reading. Install with: pip install pdfplumber"
        )

    min_chars = get_config("min_chars_per_page", 20)
    pages_text = []

    with pdfplumber.open(str(path)) as pdf:
        num_pages = len(pdf.pages)
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text)

    # Check average characters per page
    total_chars = sum(len(t) for t in pages_text)
    avg_chars = total_chars / max(num_pages, 1)

    if avg_chars < min_chars:
        # Fall back to OCR
        return _read_pdf_ocr(path)

    return "\n\n".join(pages_text)


def _read_pdf_ocr(path: Path) -> str:
    """Extract text from PDF using pytesseract OCR."""
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError:
        raise ImportError(
            "pytesseract and pdf2image are required for OCR. "
            "Install with: pip install pytesseract pdf2image"
        )

    # Set custom tesseract path if configured
    custom_path = get_tesseract_path()
    if custom_path:
        pytesseract.pytesseract.tesseract_cmd = custom_path

    lang = get_config("ocr_language", "eng")
    images = convert_from_path(str(path))
    pages_text = []

    for image in images:
        text = pytesseract.image_to_string(image, lang=lang)
        pages_text.append(text)

    return "\n\n".join(pages_text)


def extract_pages(file_path: str) -> list:
    """
    Extract text from each page separately.

    Returns:
        List of strings, one per page.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()
    if ext == ".txt":
        # Treat the whole file as one page
        return [_read_txt(path)]
    elif ext == ".pdf":
        return _extract_pdf_pages(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _extract_pdf_pages(path: Path) -> list:
    """Extract text from each PDF page individually."""
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required for PDF reading.")

    min_chars = get_config("min_chars_per_page", 20)
    pages_text = []

    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text)

    # Check if OCR is needed
    avg_chars = sum(len(t) for t in pages_text) / max(len(pages_text), 1)
    if avg_chars < min_chars:
        try:
            from pdf2image import convert_from_path
            import pytesseract
            lang = get_config("ocr_language", "eng")
            images = convert_from_path(str(path))
            return [pytesseract.image_to_string(img, lang=lang) for img in images]
        except ImportError:
            pass  # Return sparse pdfplumber text if OCR not available

    return pages_text
