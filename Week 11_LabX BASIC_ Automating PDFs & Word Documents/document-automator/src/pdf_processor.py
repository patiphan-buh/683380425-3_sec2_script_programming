# document-automator/src/pdf_processor.py
from PyPDF2 import PdfReader, PdfWriter
import os
from utils import setup_logging, ensure_directory_exists

logger = setup_logging(__name__)


class PDFProcessor:
    """Handles operations related to PDF files using PyPDF2."""

    def __init__(self):
        logger.info("PDFProcessor initialized.")

    def extract_text_from_pdf(self, pdf_path):
        """Extracts all text from a given PDF file."""
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return None

        text_content = ""
        try:
            reader = PdfReader(pdf_path)
            num_pages = len(reader.pages)
            logger.info(f"Extracting text from '{pdf_path}' ({num_pages} pages)...")
            for page in reader.pages:
                text_content += page.extract_text() + "\n--- Page End ---\n"
            logger.info(f"Successfully extracted text from '{pdf_path}'.")
            return text_content
        except Exception as e:
            logger.error(f"Error extracting text from '{pdf_path}': {e}")
            return None

    def merge_pdfs(self, pdf_paths, output_path):
        """Merges multiple PDF files into a single output PDF."""
        if not pdf_paths:
            logger.warning("No PDF paths provided for merging.")
            return False

        writer = PdfWriter()
        logger.info(f"Merging PDFs into '{output_path}'...")
        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                logger.warning(f"Skipping non-existent PDF for merging: {pdf_path}")
                continue
            try:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    writer.add_page(page)
                logger.info(f"Added '{pdf_path}' to merge queue.")
            except Exception as e:
                logger.error(f"Error reading PDF '{pdf_path}' for merging: {e}")
                continue

        if len(writer.pages) == 0:
            logger.warning("No pages were added to the merged PDF.")
            return False

        try:
            with open(output_path, 'wb') as f:
                writer.write(f)
            logger.info(f"PDFs successfully merged to '{output_path}'.")
            return True
        except Exception as e:
            logger.error(f"Error writing merged PDF to '{output_path}': {e}")
            return False

    def split_pdf(self, pdf_path, output_dir=".", pages_per_split=1):
        """Splits a PDF into smaller PDFs with a given number of pages each."""
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return False

        ensure_directory_exists(output_dir)

        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            logger.info(f"Splitting '{pdf_path}' ({total_pages} pages) into chunks of {pages_per_split} pages.")

            base = os.path.splitext(os.path.basename(pdf_path))[0]
            for i in range(0, total_pages, pages_per_split):  # fixed: handout had `0_int` (SyntaxError)
                writer = PdfWriter()
                output_filename = os.path.join(output_dir, f"{base}_part_{(i // pages_per_split) + 1}.pdf")
                for j in range(i, min(i + pages_per_split, total_pages)):
                    writer.add_page(reader.pages[j])
                with open(output_filename, 'wb') as f:
                    writer.write(f)
                logger.info(f"Created split PDF: {output_filename}")

            logger.info(f"Successfully split '{pdf_path}'.")
            return True
        except Exception as e:
            logger.error(f"Error splitting PDF '{pdf_path}': {e}")
            return False
