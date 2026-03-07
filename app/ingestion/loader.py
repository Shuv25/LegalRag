"""
PDF loader for legal documents.
Loads and preprocesses PDF files page by page using pdfplumber,
returning structured page content with page numbers for downstream chunking.
"""

import re
import pdfplumber

#-------Imports from other packages---------
from logs.logger import get_logger

logger = get_logger()

def load_pdf(file_path: str) -> list[dict]:
    """
    To load and preprocess the file given by user
    :param file_path:
    :return:
    """
    texts = []
    try:
        with pdfplumber.open(file_path) as pdf:
            pages = pdf.pages
            for page in pages:
                page_no = page.page_number
                raw_text = page.extract_text()
                if raw_text:
                    raw_text = re.sub(r'\s+', ' ',raw_text )
                    page_content = re.sub(r'\n{3,}', '\n\n', raw_text)
                    texts.append({"page_no":page_no,"page_content":page_content})
                else:
                    logger.warning(f"No texts found on the page no {page_no} of uploaded pdf")
        return texts
    except Exception as e:
        logger.error(f"Got an error while loading the pdf:{e}")
        raise RuntimeError("Got an error while loading the pdf")