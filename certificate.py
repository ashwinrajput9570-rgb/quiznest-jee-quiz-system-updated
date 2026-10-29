"""PDF certificate generation for QuizNest (uses ReportLab)."""
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

PROJECT_NAME = "QuizNest JEE Quiz System"
NAVY = colors.HexColor("#1f2a5c")
GOLD = colors.HexColor("#b8923a")
GREY = colors.HexColor("#555555")


def _fit(c, text, font, size, max_width):
    while size > 10 and c.stringWidth(text, font, size) > max_width:
        size -= 1
    return size


def _fmt_date(iso):
    try:
        return datetime.fromisoformat(iso).strftime("%d %B %Y")
    except (TypeError, ValueError):
        return None


def _num(v):
    v = round(float(v), 1)
    return str(int(v)) if v == int(v) else str(v)


def build_certificate_pdf(student_name, quiz_title, subject, chapter,
                          score, total_marks, completed_at):
    buf = io.BytesIO()
    w, h = landscape(A4)
    c = canvas.Canvas(buf, pagesize=(w, h))
    c.setTitle("QuizNest Certificate")
    c.setAuthor(PROJECT_NAME)
    cx = w / 2
    maxw = w - 200

    # Borders
    c.setStrokeColor(NAVY); c.setLineWidth(4); c.rect(25, 25, w - 50, h - 50)
    c.setStrokeColor(GOLD); c.setLineWidth(1.5); c.rect(36, 36, w - 72, h - 72)

    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(cx, h - 80, PROJECT_NAME.upper())
    c.setFillColor(NAVY); c.setFont("Times-Bold", 40)
    c.drawCentredString(cx, h - 130, "Certificate of Achievement")
    c.setStrokeColor(GOLD); c.setLineWidth(1.5)
    c.line(cx - 110, h - 145, cx + 110, h - 145)

    c.setFillColor(GREY); c.setFont("Helvetica", 13)
    c.drawCentredString(cx, h - 180, "This is to certify that")

    name = (student_name or "").strip() or "Student"
    size = _fit(c, name, "Times-BoldItalic", 34, maxw)
    c.setFillColor(NAVY); c.setFont("Times-BoldItalic", size)
    c.drawCentredString(cx, h - 225, name)
    c.setStrokeColor(GREY); c.setLineWidth(0.6)
    c.line(cx - 200, h - 235, cx + 200, h - 235)

    c.setFillColor(GREY); c.setFont("Helvetica", 13)
    c.drawCentredString(cx, h - 265, "has successfully completed the quiz")

    title = quiz_title or "Quiz"
    size = _fit(c, title, "Helvetica-Bold", 20, maxw)
    c.setFillColor(NAVY); c.setFont("Helvetica-Bold", size)
    c.drawCentredString(cx, h - 295, title)

    details = []
    if subject:
        details.append(f"Subject: {subject}")
    if chapter:
        details.append(f"Chapter: {chapter}")
    if details:
        c.setFillColor(GREY); c.setFont("Helvetica", 12)
        c.drawCentredString(cx, h - 318, "   |   ".join(details))

    pct = round(score / total_marks * 100, 1) if total_marks else 0
    boxes = [("Marks Obtained", _num(score)), ("Total Marks", _num(total_marks)),
             ("Percentage", f"{pct:g}%")]
    bw, bh, gap = 150, 62, 25
    x0 = cx - (3 * bw + 2 * gap) / 2
    y0 = 105
    for i, (label, val) in enumerate(boxes):
        x = x0 + i * (bw + gap)
        c.setStrokeColor(GOLD); c.setLineWidth(1); c.setFillColor(colors.HexColor("#faf6ec"))
        c.roundRect(x, y0, bw, bh, 6, fill=1, stroke=1)
        c.setFillColor(NAVY); c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(x + bw / 2, y0 + 30, val)
        c.setFillColor(GREY); c.setFont("Helvetica", 10)
        c.drawCentredString(x + bw / 2, y0 + 13, label)

    date = _fmt_date(completed_at)
    c.setFillColor(GREY); c.setFont("Helvetica", 11)
    c.drawCentredString(cx, 72, f"Completed on {date}" if date else "Completion date not available")

    c.showPage()
    c.save()
    return buf.getvalue()
