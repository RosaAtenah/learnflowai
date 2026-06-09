import fitz
from config.settings import MAX_FILE_SIZE_MB, ZONE1_PAGES, ZONE2_PAGES, MIN_TEXT_LENGTH , CHUNK_SIZE, CHUNK_OVERLAP
from utils.text_cleaner import clean_text

def extract_text_from_pdf(pdf_file, max_pages=None, page_range=None):
    """
    Extracts text from a PDF file.
    
    Args:
        pdf_file    : uploaded PDF file (Streamlit UploadedFile)
        max_pages   : maximum number of pages to read (from the beginning)
                      ignored if page_range is provided
        page_range  : tuple (start_page, end_page) — 1-indexed, inclusive
                      example: (10, 15) extracts pages 10 to 15
    
    Returns:
        str : extracted and concatenated text
    """

    text = ""

    pdf_document = fitz.open(
        stream=pdf_file.read(),
        filetype="pdf"
    )

    nb_pages = len(pdf_document)

    # Determine which pages to extract

    if page_range is not None:
        # User chose a specific range (e.g. pages 10 to 15)
        start_page, end_page = page_range

        # Convert to 0-indexed and clamp to document bounds
        start_index = max(0, start_page - 1)
        end_index   = min(nb_pages - 1, end_page - 1)

        pages_to_read = range(start_index, end_index + 1)

    elif max_pages is not None:
        # Read from the beginning up to max_pages
        pages_to_read = range(min(nb_pages, max_pages))

    else:
        # Read the entire document
        pages_to_read = range(nb_pages)

    # Extract text from selected pages

    for i in pages_to_read:
        page_text = pdf_document[i].get_text()
        if page_text.strip():               # skip blank pages silently
            text += page_text

    pdf_document.close()
    pdf_file.seek(0)

    return clean_text(text)


def verify_pdf_validity(pdf_file):
    """
    Validates the uploaded PDF.
    Returns a dictionary:
    {
        "valid": True/False,
        "error": None or blocking error message,
        "warning": None or warning message,
        "suggestion": None or suggestion to display to the user,
        "nb_pages": int,
        "action": "normal" / "warn" / "partial" / "block"
    }
    """

    result = {
        "valid": True,
        "error": None,
        "warning": None,
        "suggestion": None,
        "nb_pages": 0,
        "action": "normal"
    }

# Check 1: File too large (size in MB)    
    pdf_file.seek(0, 2)           
    file_size_mb = pdf_file.tell() / (1024 * 1024)
    pdf_file.seek(0)             

    if file_size_mb > MAX_FILE_SIZE_MB:
        result["valid"] = False
        result["error"] = (
            f"Fichier trop volumineux ({file_size_mb:.1f} Mo). "
            f"Maximum autorisé : {MAX_FILE_SIZE_MB} Mo."
        )
        result["action"] = "block"
        return result

    # Opening the document
    try:
        pdf_document = fitz.open(
            stream=pdf_file.read(),
            filetype="pdf"
        )
    except Exception:
        result["valid"] = False
        result["error"] = "File corrupted, cannot be opened"
        result["action"] = "block"
        pdf_file.seek(0)
        return result

    # Number of pages + suggestion per area
    nb_pages = len(pdf_document)
    result["nb_pages"] = nb_pages

    if nb_pages == 0:
        result["valid"] = False
        result["error"] = "This PDF contains no pages."
        result["action"] = "block"
        pdf_document.close()
        pdf_file.seek(0)
        return result

    elif nb_pages <= ZONE1_PAGES:
    # Zone 1: ≤ 30 pages → normal processing
        result["action"] = "normal"

    elif nb_pages <= ZONE2_PAGES:
        # Zone 2: 31 to 50 pages → warning
        result["action"] = "warn"
        result["warning"] = (
            f"Your document contains {nb_pages} pages. "
            f"Processing will take longer (~{nb_pages * 5} seconds). "
            f"You can choose to process only a part of it."
        )
        result["suggestion"] = "partial"

    else:
        # Zone 3: > 50 pages → split recommendation
        result["action"] = "partial"
        result["warning"] = (
            f"Your document contains {nb_pages} pages. "
            f"It is too large for full processing at once."
        )
        result["suggestion"] = (
            f"Recommendation: split your PDF into sections of {ZONE1_PAGES} pages "
            f"and process each section separately. "
            f"By default, only the first {ZONE1_PAGES} pages will be processed."
        )

    # Scanned PDF (text not extractable)
    sample_text = ""
    # we check the first 3 pages
    pages_to_check = min(3, nb_pages)   
    for i in range(pages_to_check):
        sample_text += pdf_document[i].get_text()

    if len(sample_text.strip()) < MIN_TEXT_LENGTH:
        result["valid"] = False
        result["error"] = (
            "This PDF appears to be scanned or does not contain extractable text."
            "Only PDFs with selectable text are supported."
        )
        result["action"] = "block"
        pdf_document.close()
        pdf_file.seek(0)
        return result

    #Blank pages (non-blocking warning)
    blank_pages = []
    for i in range(nb_pages):
        page_text = pdf_document[i].get_text().strip()
        if len(page_text) < 10:
            blank_pages.append(i + 1)   

    if blank_pages:
        ratio_blank = len(blank_pages) / nb_pages
        if ratio_blank > 0.5:
            # More than 50% blank pages → probably a scanned PDF
            result["valid"] = False
            result["error"] = (
                f"{len(blank_pages)} out of {nb_pages} pages are blank or unreadable. "
                "This document does not seem to contain enough text."
            )
            result["action"] = "block"
        else:
            # A few blank pages → simple warning
            result["warning"] = (
                result["warning"] or "" +
                f" {len(blank_pages)} blank page(s) detected "
                f"(pages {blank_pages}) and will be ignored."
            )

    pdf_document.close()
    pdf_file.seek(0)

    return result


def chunk_text(text: str) -> list:
    """
    Splits extracted text into overlapping chunks.

    Args:
        text : clean extracted text from PDF

    Returns:
        list of str : list of chunks ready for LLM
    """
    chunks = []
    words  = text.split()

    step   = CHUNK_SIZE - CHUNK_OVERLAP

    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + CHUNK_SIZE])
        if chunk.strip():
            chunks.append(chunk)

    return chunks