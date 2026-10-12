import io
import os
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from utils import setup_logging

logger = setup_logging(__name__)


def extract_pdf_text(pdf_path, output_txt):
    reader = PdfReader(pdf_path)
    text = "\n".join(f"[Page {i}]\n{p.extract_text()}" for i, p in enumerate(reader.pages, 1))
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write(text)
    logger.info(f"Extracted {len(reader.pages)} pages -> {output_txt}")
    return len(reader.pages)


def merge_pdfs(pdf_paths, output_path):
    writer = PdfWriter()
    for path in pdf_paths:
        for page in PdfReader(path).pages:
            writer.add_page(page)
    with open(output_path, 'wb') as f:
        writer.write(f)
    logger.info(f"Merged {len(pdf_paths)} files ({len(writer.pages)} pages) -> {output_path}")
    return len(writer.pages)


def _watermark_page(text, width, height):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    c.setFont("Helvetica-Bold", 80)
    c.setFillColorRGB(0.8, 0.1, 0.1, alpha=0.25)
    c.translate(width / 2, height / 2)
    c.rotate(45)
    c.drawCentredString(0, 0, text)
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


def watermark_pdf(pdf_path, output_path, text="CONFIDENTIAL"):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    for page in reader.pages:
        w, h = float(page.mediabox.width), float(page.mediabox.height)
        page.merge_page(_watermark_page(text, w, h))
        writer.add_page(page)
    with open(output_path, 'wb') as f:
        writer.write(f)
    logger.info(f"Watermarked '{text}' on {len(reader.pages)} pages -> {output_path}")
    return len(reader.pages)
