"""
PDF Generator – Distinct Templates per Document Type.

Each intelligence asset has its own branded, purpose-built layout:
  1. generate_any_pdf()          – Generic fallback (Botivate branded)
  2. generate_transcript_pdf()   – Verbatim Transcript  (🎤 Speech Record)
  3. generate_audit_log_pdf()    – AI Audit Trail       (🔍 Process Log)
  4. generate_summary_pdf()      – Executive Briefing   (📊 Narrative Summary)
  5. draw_header_footer()        – Shared Botivate header/footer (used by MOM)
"""
import io
import os
import logging
import textwrap
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger("pdf_generator")

LOGO_PATH = r"c:\Users\prabh\Desktop\MOM_AI_Assistant\B PNG.png"
PAGE_W, PAGE_H = A4  # 595.27, 841.89

# ──────────────────────────────────────────────────────────────────────
# SHARED HEADER/FOOTER – Used by Official MOM PDF
# ──────────────────────────────────────────────────────────────────────

def draw_header_footer(canvas, doc):
    """Botivate corporate header + footer for Official MOM."""
    canvas.saveState()
    # Header Ribbon
    canvas.setFillColor(colors.HexColor("#60a5fa"))
    canvas.rect(0, 830, 297, 12, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#4f46e5"))
    canvas.rect(297, 830, 298, 12, fill=1, stroke=0)

    # Footer Ribbon
    canvas.setFillColor(colors.HexColor("#60a5fa"))
    p1 = canvas.beginPath()
    p1.moveTo(0, 0); p1.lineTo(200, 0); p1.lineTo(220, 15); p1.lineTo(0, 15); p1.close()
    canvas.drawPath(p1, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor("#4f46e5"))
    p2 = canvas.beginPath()
    p2.moveTo(200, 0); p2.lineTo(595.27, 0); p2.lineTo(595.27, 25); p2.lineTo(230, 25); p2.close()
    canvas.drawPath(p2, stroke=0, fill=1)

    # Logo and Branding
    if os.path.exists(LOGO_PATH):
        try:
            logo = ImageReader(LOGO_PATH)
            canvas.drawImage(logo, 30, 755, width=60, height=60, preserveAspectRatio=True, mask='auto')
            canvas.setStrokeColor(colors.HexColor("#1e293b"))
            canvas.setLineWidth(1.5)
            canvas.line(100, 760, 100, 805)
            canvas.setFillColor(colors.HexColor("#000000"))
            canvas.setFont("Helvetica-Bold", 24)
            canvas.drawString(110, 785, "Botivate")
            canvas.setFont("Helvetica-Oblique", 11)
            canvas.drawString(110, 770, "Powering Businesses")
            canvas.drawString(110, 757, "On Autopilot")
        except Exception as e:
            logger.warning(f"Could not draw logo: {e}")

    # Company Info (Right)
    canvas.setFillColor(colors.HexColor("#1e293b"))
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawRightString(565, 790, "BOTIVATE SERVICES LLP")
    canvas.setFont("Helvetica", 10)
    canvas.setFillColor(colors.HexColor("#4f46e5"))
    canvas.drawRightString(565, 775, "Shriram Business Park, Block-I ,")
    canvas.drawRightString(565, 762, "Office No- 224 , Vidhan Sabha Rd,")
    canvas.drawRightString(565, 749, "Raipur, Chhattisgarh 493111")

    # Divider Line
    canvas.setStrokeColor(colors.HexColor("#4f46e5"))
    canvas.setLineWidth(1.5)
    canvas.line(30, 735, 565, 735)

    # Footer Text
    canvas.setFillColor(colors.HexColor("#000000"))
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(30, 45, "HR Department / Intelligence Division")
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.drawString(30, 32, "Botivate Services LLP")
    canvas.restoreState()


# ──────────────────────────────────────────────────────────────────────
# 1. GENERIC BRANDED PDF (Fallback)
# ──────────────────────────────────────────────────────────────────────

def generate_any_pdf(title: str, subtitle: str, content: str) -> bytes:
    """Generate a standard Botivate-branded PDF for any text content."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=120, bottomMargin=120)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=14, textColor=colors.HexColor("#1e293b"), spaceAfter=12)
    h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor("#334155"), spaceAfter=8, spaceBefore=12)
    body = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor("#475569"), leading=14, spaceAfter=6)

    elements = []
    elements.append(Paragraph(f"<b>{title.upper()}</b>", h1))
    if subtitle:
        elements.append(Paragraph(f"<i>{subtitle}</i>", body))
    elements.append(Spacer(1, 20))
    for line in content.split('\n'):
        if line.strip():
            if line.strip().startswith('•') or line.strip().startswith('- '):
                elements.append(Paragraph(line.strip(), body))
            elif line.strip().isupper() and len(line) < 50:
                elements.append(Paragraph(f"<b>{line.strip()}</b>", h2))
            else:
                elements.append(Paragraph(line.strip(), body))
        else:
            elements.append(Spacer(1, 10))
    doc.build(elements, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# ──────────────────────────────────────────────────────────────────────
# 2. VERBATIM TRANSCRIPT PDF  🎤
# ──────────────────────────────────────────────────────────────────────

def _transcript_header_footer(canvas, doc):
    """Minimal transcript layout: dark sidebar + subtle branding."""
    canvas.saveState()
    # Left sidebar accent bar
    canvas.setFillColor(colors.HexColor("#0ea5e9"))
    canvas.rect(0, 0, 8, PAGE_H, fill=1, stroke=0)
    # Top bar
    canvas.setFillColor(colors.HexColor("#0c4a6e"))
    canvas.rect(8, PAGE_H - 50, PAGE_W - 8, 50, fill=1, stroke=0)
    # Title in top bar
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawString(24, PAGE_H - 35, "VERBATIM TRANSCRIPT")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(PAGE_W - 30, PAGE_H - 25, "Botivate Meeting Intelligence")
    canvas.drawRightString(PAGE_W - 30, PAGE_H - 38, f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
    # Footer
    canvas.setFillColor(colors.HexColor("#0c4a6e"))
    canvas.rect(8, 0, PAGE_W - 8, 30, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(20, 10, "Botivate Services LLP | Speech-to-Text Record")
    canvas.drawRightString(PAGE_W - 20, 10, f"Page {doc.page}")
    canvas.restoreState()


def generate_transcript_pdf(title: str, date: str, transcript_text: str) -> bytes:
    """Generate a clearly formatted Transcript PDF with speaker-style layout."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=24, rightMargin=30, topMargin=70, bottomMargin=50)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('TTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, textColor=colors.HexColor("#0c4a6e"), spaceAfter=4)
    meta_style = ParagraphStyle('TMeta', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor("#64748b"), spaceAfter=2)
    body_style = ParagraphStyle('TBody', parent=styles['Normal'], fontName='Courier', fontSize=9, textColor=colors.HexColor("#1e293b"), leading=14, spaceAfter=4, leftIndent=12)
    line_num_style = ParagraphStyle('TLineNum', parent=styles['Normal'], fontName='Helvetica', fontSize=7, textColor=colors.HexColor("#94a3b8"), leading=14, spaceAfter=4)

    elements = []
    elements.append(Paragraph(f"<b>{title}</b>", title_style))
    elements.append(Paragraph(f"Meeting Date: {date}", meta_style))
    elements.append(Paragraph(f"Document Type: Verbatim Speech-to-Text Record", meta_style))
    elements.append(Paragraph(f"Extraction Engine: AssemblyAI / Faster-Whisper", meta_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=12))

    # Split transcript into lines and number them
    lines = transcript_text.split('\n')
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            elements.append(Spacer(1, 6))
            continue

        # Format: line number + monospace text
        row_data = [[
            Paragraph(f"<font color='#94a3b8'>{i:04d}</font>", line_num_style),
            Paragraph(stripped, body_style)
        ]]
        t = Table(row_data, colWidths=[35, PAGE_W - 100])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(t)

    # End marker
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
    elements.append(Paragraph(f"<i>— End of Transcript ({len(lines)} lines) —</i>", meta_style))

    doc.build(elements, onFirstPage=_transcript_header_footer, onLaterPages=_transcript_header_footer)
    result = buffer.getvalue()
    buffer.close()
    return result


# ──────────────────────────────────────────────────────────────────────
# 3. AI AUDIT LOG PDF  🔍
# ──────────────────────────────────────────────────────────────────────

def _audit_header_footer(canvas, doc):
    """Technical process trail layout: dark header, numbered pages."""
    canvas.saveState()
    # Top bar
    canvas.setFillColor(colors.HexColor("#1e1b4b"))
    canvas.rect(0, PAGE_H - 55, PAGE_W, 55, fill=1, stroke=0)
    # Accent line
    canvas.setFillColor(colors.HexColor("#f59e0b"))
    canvas.rect(0, PAGE_H - 58, PAGE_W, 3, fill=1, stroke=0)
    # Title
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawString(30, PAGE_H - 30, "AI PROCESSING AUDIT LOG")
    canvas.setFont("Helvetica", 8)
    canvas.drawString(30, PAGE_H - 44, "Chunk-by-Chunk Summarization Trail")
    canvas.drawRightString(PAGE_W - 30, PAGE_H - 30, "Botivate Intelligence Engine")
    canvas.drawRightString(PAGE_W - 30, PAGE_H - 44, f"{datetime.now().strftime('%d %b %Y, %I:%M %p')}")
    # Footer
    canvas.setFillColor(colors.HexColor("#f1f5f9"))
    canvas.rect(0, 0, PAGE_W, 28, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.setFont("Helvetica", 7)
    canvas.drawString(20, 10, "CONFIDENTIAL — AI Audit Trail | Botivate Services LLP")
    canvas.drawRightString(PAGE_W - 20, 10, f"Page {doc.page}")
    canvas.restoreState()


def generate_audit_log_pdf(title: str, date: str, chunk_summaries: list) -> bytes:
    """Generate an AI Audit Log PDF showing each chunk's extraction."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=75, bottomMargin=45)
    styles = getSampleStyleSheet()

    sec_title = ParagraphStyle('ASecTitle', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor("#1e1b4b"), spaceAfter=4, spaceBefore=16)
    meta_style = ParagraphStyle('AMeta', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor("#64748b"), spaceAfter=2)
    body_style = ParagraphStyle('ABody', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor("#334155"), leading=13, spaceAfter=4, leftIndent=8)
    chunk_label = ParagraphStyle('AChunk', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor("#f59e0b"), spaceAfter=2, spaceBefore=14)

    elements = []
    elements.append(Paragraph(f"<b>Meeting: {title}</b>", sec_title))
    elements.append(Paragraph(f"Date: {date} | Total Segments: {len(chunk_summaries)}", meta_style))
    elements.append(Paragraph(f"Pipeline: AssemblyAI Transcription → Hierarchical Chunk Summarization → Final Synthesis", meta_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=12))

    for i, chunk in enumerate(chunk_summaries, 1):
        # Chunk header with accent
        elements.append(Paragraph(f"▸ SEGMENT {i} of {len(chunk_summaries)}", chunk_label))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#fbbf24"), spaceAfter=6))

        # Chunk content
        for line in chunk.split('\n'):
            stripped = line.strip()
            if stripped:
                elements.append(Paragraph(stripped, body_style))
            else:
                elements.append(Spacer(1, 4))

    # Summary
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1e1b4b"), spaceAfter=8))
    elements.append(Paragraph(f"<i>Audit completed — {len(chunk_summaries)} segments processed.</i>", meta_style))

    doc.build(elements, onFirstPage=_audit_header_footer, onLaterPages=_audit_header_footer)
    result = buffer.getvalue()
    buffer.close()
    return result


# ──────────────────────────────────────────────────────────────────────
# 4. EXECUTIVE SUMMARY / NARRATIVE BRIEFING PDF  📊
# ──────────────────────────────────────────────────────────────────────

def _summary_header_footer(canvas, doc):
    """Executive briefing layout: clean, professional, green accent."""
    canvas.saveState()
    # Top accent bar
    canvas.setFillColor(colors.HexColor("#059669"))
    canvas.rect(0, PAGE_H - 6, PAGE_W, 6, fill=1, stroke=0)
    # Header area
    canvas.setFillColor(colors.HexColor("#f0fdf4"))
    canvas.rect(0, PAGE_H - 60, PAGE_W, 54, fill=1, stroke=0)
    # Title
    canvas.setFillColor(colors.HexColor("#064e3b"))
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(30, PAGE_H - 30, "EXECUTIVE SUMMARY BRIEFING")
    canvas.setFont("Helvetica", 8)
    canvas.drawString(30, PAGE_H - 44, "AI-Synthesized Meeting Intelligence")
    # Right info
    if os.path.exists(LOGO_PATH):
        try:
            logo = ImageReader(LOGO_PATH)
            canvas.drawImage(logo, PAGE_W - 65, PAGE_H - 55, width=35, height=35, preserveAspectRatio=True, mask='auto')
        except:
            pass
    canvas.setFillColor(colors.HexColor("#064e3b"))
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(PAGE_W - 75, PAGE_H - 30, "Botivate Services LLP")
    canvas.drawRightString(PAGE_W - 75, PAGE_H - 42, f"{datetime.now().strftime('%d %b %Y')}")
    # Footer
    canvas.setFillColor(colors.HexColor("#059669"))
    canvas.rect(0, 0, PAGE_W, 3, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.setFont("Helvetica", 7)
    canvas.drawString(20, 8, "Botivate Services LLP | Executive Briefing")
    canvas.drawRightString(PAGE_W - 20, 8, f"Page {doc.page}")
    canvas.restoreState()


def generate_summary_pdf(title: str, date: str, summary_text: str) -> bytes:
    """Generate a professional Executive Summary Briefing PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=75, bottomMargin=30)
    styles = getSampleStyleSheet()

    h1 = ParagraphStyle('SH1', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=15, textColor=colors.HexColor("#064e3b"), spaceAfter=6)
    h2 = ParagraphStyle('SH2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor("#065f46"), spaceAfter=6, spaceBefore=14)
    meta = ParagraphStyle('SMeta', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor("#64748b"), spaceAfter=2)
    body = ParagraphStyle('SBody', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor("#1e293b"), leading=15, spaceAfter=8)
    bullet = ParagraphStyle('SBullet', parent=body, leftIndent=16, bulletIndent=4)

    elements = []
    elements.append(Paragraph(f"<b>{title}</b>", h1))
    elements.append(Paragraph(f"Meeting Date: {date} | Synthesised by Botivate AI", meta))
    elements.append(Spacer(1, 4))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#d1fae5"), spaceAfter=14))

    # Parse content
    for line in summary_text.split('\n'):
        stripped = line.strip()
        if not stripped:
            elements.append(Spacer(1, 8))
            continue
        # Heading detection
        if stripped.startswith('##'):
            elements.append(Paragraph(f"<b>{stripped.lstrip('#').strip()}</b>", h2))
        elif stripped.isupper() and len(stripped) < 60:
            elements.append(Paragraph(f"<b>{stripped}</b>", h2))
        elif stripped.startswith('•') or stripped.startswith('- ') or stripped.startswith('* '):
            clean = stripped.lstrip('•-* ').strip()
            elements.append(Paragraph(f"● {clean}", bullet))
        elif stripped[0].isdigit() and '.' in stripped[:4]:
            elements.append(Paragraph(stripped, bullet))
        else:
            elements.append(Paragraph(stripped, body))

    # Closing
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#d1fae5"), spaceAfter=8))
    elements.append(Paragraph("<i>— End of Executive Summary —</i>", meta))

    doc.build(elements, onFirstPage=_summary_header_footer, onLaterPages=_summary_header_footer)
    result = buffer.getvalue()
    buffer.close()
    return result
