import re

def clean_text(text: str) -> str:

    # Remove form feed characters (PDF page break artifact)
    text = text.replace("\x0c", "\n")

    # Remove multiple consecutive blank lines (keep max 1)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove multiple spaces (keep single space)
    text = re.sub(r" {2,}", " ", text)

    # Remove lines that look like headers/footers
    # (short lines with page numbers, copyright, university name)
    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()

        # Skip very short lines (likely page numbers or artifacts)
        if len(stripped) <= 3:
            continue

        # Skip lines that are only numbers (page numbers)
        if stripped.isdigit():
            continue

        # Skip lines with copyright symbols
        if "©" in stripped or "®" in stripped:
            continue

        cleaned_lines.append(stripped)

    text = "\n".join(cleaned_lines)

    # Final strip
    return text.strip()