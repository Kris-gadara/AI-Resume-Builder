"""
Resume PDF Generator
======================
Generates ATS-friendly PDF resumes using ReportLab's Platypus engine.
"""

import os
import re
import logging
from datetime import datetime
from typing import Optional

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
PRIMARY_COLOR = HexColor("#2B3A67")
ACCENT_COLOR = HexColor("#496A81")
TEXT_COLOR = HexColor("#333333")
LIGHT_GRAY = HexColor("#CCCCCC")


def _ensure_output_dir() -> None:
    """Create the output directory if it does not exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _sanitize_filename(name: str) -> str:
    """Remove characters that are problematic in file names."""
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", name).strip("_")


# ---------------------------------------------------------------------------
# Custom Styles
# ---------------------------------------------------------------------------

def _build_styles() -> dict[str, ParagraphStyle]:
    """Return a dictionary of custom ParagraphStyles for the resume."""
    base = getSampleStyleSheet()

    styles: dict[str, ParagraphStyle] = {}

    styles["Name"] = ParagraphStyle(
        "Name",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=PRIMARY_COLOR,
        alignment=TA_CENTER,
        spaceAfter=4,
    )

    styles["ContactInfo"] = ParagraphStyle(
        "ContactInfo",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=ACCENT_COLOR,
        alignment=TA_CENTER,
        spaceAfter=12,
    )

    styles["SectionHeading"] = ParagraphStyle(
        "SectionHeading",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=PRIMARY_COLOR,
        spaceBefore=14,
        spaceAfter=6,
        borderPadding=(0, 0, 2, 0),
    )

    styles["BodyText"] = ParagraphStyle(
        "BodyText",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=TEXT_COLOR,
        alignment=TA_JUSTIFY,
        spaceAfter=4,
    )

    styles["BulletItem"] = ParagraphStyle(
        "BulletItem",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=TEXT_COLOR,
        leftIndent=18,
        spaceAfter=3,
        bulletIndent=6,
        bulletFontName="Helvetica",
        bulletFontSize=10,
    )

    styles["SubHeading"] = ParagraphStyle(
        "SubHeading",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=ACCENT_COLOR,
        spaceAfter=2,
    )

    return styles


# ---------------------------------------------------------------------------
# Section Builders
# ---------------------------------------------------------------------------

def _add_section_divider(elements: list) -> None:
    """Append a thin horizontal rule as a section divider."""
    elements.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=LIGHT_GRAY,
            spaceAfter=6,
            spaceBefore=2,
        )
    )


def _add_header(
    elements: list,
    styles: dict,
    name: str,
    email: str,
    phone: str,
) -> None:
    """Add the resume header (name + contact line)."""
    elements.append(Paragraph(name, styles["Name"]))
    contact_parts = [p for p in (email, phone) if p]
    if contact_parts:
        contact_line = " &nbsp;|&nbsp; ".join(contact_parts)
        elements.append(Paragraph(contact_line, styles["ContactInfo"]))
    _add_section_divider(elements)


def _add_section(
    elements: list,
    styles: dict,
    heading: str,
    body: str,
) -> None:
    """Add a generic resume section with heading and body paragraphs."""
    if not body or not body.strip():
        return

    elements.append(Paragraph(heading.upper(), styles["SectionHeading"]))
    _add_section_divider(elements)

    for line in body.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Detect bullet points (•, -, *)
        if line and line[0] in ("•", "-", "*", "–"):
            clean = line.lstrip("•-*– ").strip()
            # Escape XML-sensitive characters for ReportLab
            clean = clean.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            elements.append(
                Paragraph(f"• {clean}", styles["BulletItem"])
            )
        elif "|" in line:
            # Likely a sub-heading (e.g., "Job Title | Company | Dates")
            safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            elements.append(Paragraph(safe, styles["SubHeading"]))
        else:
            safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            elements.append(Paragraph(safe, styles["BodyText"]))

    elements.append(Spacer(1, 6))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_pdf(
    resume_data: dict,
    filename: Optional[str] = None,
) -> str:
    """
    Generate a professional, ATS-friendly PDF resume.

    Parameters
    ----------
    resume_data : dict
        Expected keys:
        - name (str)
        - email (str)
        - phone (str)
        - summary (str)
        - skills (str)
        - experience (str)
        - education (str, optional)
    filename : str, optional
        Custom filename (without extension). If omitted a timestamped
        name is generated from the user's name.

    Returns
    -------
    str
        Absolute path to the generated PDF file.
    """
    _ensure_output_dir()

    # Build filename
    if not filename:
        safe_name = _sanitize_filename(resume_data.get("name", "resume"))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resume_{safe_name}_{timestamp}"

    filepath = os.path.join(OUTPUT_DIR, f"{filename}.pdf")

    # Create the document
    doc = SimpleDocTemplate(
        filepath,
        pagesize=LETTER,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        title=f"Resume - {resume_data.get('name', '')}",
        author="AI Resume Builder",
    )

    styles = _build_styles()
    elements: list = []

    # Header
    _add_header(
        elements,
        styles,
        name=resume_data.get("name", ""),
        email=resume_data.get("email", ""),
        phone=resume_data.get("phone", ""),
    )

    # Professional Summary
    _add_section(elements, styles, "Professional Summary", resume_data.get("summary", ""))

    # Skills
    _add_section(elements, styles, "Skills", resume_data.get("skills", ""))

    # Experience
    _add_section(elements, styles, "Professional Experience", resume_data.get("experience", ""))

    # Education (optional)
    education = resume_data.get("education", "")
    if education and education.strip():
        _add_section(elements, styles, "Education", education)

    # Build PDF
    try:
        doc.build(elements)
        logger.info("PDF generated: %s", filepath)
    except Exception as exc:
        logger.error("PDF generation failed: %s", exc)
        raise RuntimeError(f"Failed to generate PDF: {exc}") from exc

    return filepath
