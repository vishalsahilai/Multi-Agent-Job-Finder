import re
import io
from pathlib import Path
from typing import Union

#  PDF 
def _read_pdf(file: Union[str, Path, bytes]) -> str:
    """Extract text from a PDF file or bytes object."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("pypdf is required: pip install pypdf")
 
    if isinstance(file, (str, Path)):
        reader = PdfReader(str(file))
    else:
        reader = PdfReader(io.BytesIO(file))
 
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
 
    return "\n".join(pages)

#  DOCX
 
def _read_docx(file: Union[str, Path, bytes]) -> str:
    """Extract text from a DOCX file or bytes object."""
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx is required: pip install python-docx")
 
    if isinstance(file, (str, Path)):
        doc = Document(str(file))
    else:
        doc = Document(io.BytesIO(file))
 
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs)