# document-automator/main.py
import sys
import os
import datetime

# Add the 'src' directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from pdf_processor import PDFProcessor
from word_processor import WordProcessor
from utils import ensure_directory_exists, setup_logging

logger = setup_logging(__name__)


def main():
    """Main entry point for the document automation application."""
    documents_dir = os.path.join(os.path.dirname(__file__), 'documents')
    ensure_directory_exists(documents_dir)

    input_pdf_path = os.path.join(documents_dir, 'input_article.pdf')
    output_docx_path = os.path.join(documents_dir, 'output_report.docx')
    merged_pdf_output_path = os.path.join(documents_dir, 'merged_output.pdf')
    dummy_pdf1 = os.path.join(documents_dir, 'dummy_doc1.pdf')
    dummy_pdf2 = os.path.join(documents_dir, 'dummy_doc2.pdf')

    if not os.path.exists(input_pdf_path):
        logger.critical(f"Required input PDF '{input_pdf_path}' not found.")
        logger.info("Please create this PDF in the 'documents' folder with some text content.")
        return

    dummy_pdfs_exist = os.path.exists(dummy_pdf1) and os.path.exists(dummy_pdf2)
    if not dummy_pdfs_exist:
        logger.warning("Dummy PDFs for merging example not found. Skipping PDF merge task.")

    pdf_proc = PDFProcessor()
    word_proc = WordProcessor()

    logger.info("--- Starting Document Automation Workflow ---")

    # --- Task 1: Extract Text from PDF and Create Word Report ---
    logger.info("Task 1: Extracting text from PDF and generating Word report.")
    extracted_text = pdf_proc.extract_text_from_pdf(input_pdf_path)

    if extracted_text:
        doc = word_proc.create_document()
        word_proc.add_heading(doc, "Automated Document Report", level=1)
        word_proc.add_paragraph(doc, "This report was automatically generated from PDF content and structured data.", bold=True, font_size=12)
        word_proc.add_paragraph(doc, "--- Extracted Content from PDF ---", italic=True, font_size=10, align='center')
        word_proc.add_paragraph(doc, extracted_text)

        word_proc.add_heading(doc, "Summary Data", level=2)

        table_data = [
            ["Metric", "Value", "Notes"],
            ["Total Pages Processed", str(extracted_text.count("--- Page End ---")), "From Input PDF"],
            ["Document Type", "PDF/Word Hybrid", ""],
            ["Generated Date", datetime.date.today().isoformat(), ""]
        ]
        word_proc.add_table(doc, table_data, col_widths=[1.5, 1.5, 3.0])

        word_proc.save_document(doc, output_docx_path)
    else:
        logger.error("Could not extract text from PDF. Skipping Word document generation.")

    # --- Task 2: Merge Multiple PDFs ---
    if dummy_pdfs_exist:
        logger.info("Task 2: Merging dummy PDFs.")
        pdf_proc.merge_pdfs([dummy_pdf1, dummy_pdf2], merged_pdf_output_path)
    else:
        logger.warning("Skipping PDF merge task as dummy PDFs were not found.")

    logger.info("--- Document Automation Workflow Completed ---")


if __name__ == "__main__":
    main()
