"""OCR service using Google Cloud Vision API"""
import logging
from google.cloud import vision
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def extract_text_from_file(file_content: bytes, filename: str = "", vision_client=None) -> str:
    """Process file content, handling both PDFs and images"""
    try:
        # Determine if it's a PDF
        if filename.lower().endswith('.pdf') or file_content.startswith(b'%PDF'):
            logger.info("DEBUG: Processing PDF file - converting to image first")
            # Convert PDF to image using PyMuPDF
            try:
                # Open PDF from bytes
                pdf_document = fitz.open(stream=file_content, filetype="pdf")

                if len(pdf_document) == 0:
                    raise Exception("No pages found in PDF")

                # Get first page
                page = pdf_document[0]

                # Convert page to image (PNG format)
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")

                # Close the document
                pdf_document.close()

                logger.info("DEBUG: PDF converted to image, extracting text with Vision API")
                # Extract text from the converted image
                return extract_text_from_image(img_data, vision_client)
            except Exception as e:
                logger.error(f"ERROR: Error processing PDF: {str(e)}")
                raise Exception(f"Error processing PDF: {str(e)}")
        else:
            logger.info("DEBUG: Processing as image directly")
            # Process as image directly
            return extract_text_from_image(file_content, vision_client)
    except Exception as e:
        logger.error(f"ERROR: Exception in extract_text_from_file: {str(e)}")
        raise


def extract_text_from_image(image_content: bytes, vision_client=None) -> str:
    """Extract text from image using Google Vision API"""
    if not vision_client:
        raise Exception("Google Cloud Vision client is not available. Check credentials configuration.")

    image = vision.Image(content=image_content)
    response = vision_client.text_detection(image=image)

    if response.error.message:
        raise Exception(f"Vision API Error: {response.error.message}")

    extracted_text = response.full_text_annotation.text if response.full_text_annotation else ""
    if not extracted_text:
        logger.warning("WARNING: Vision API extracted no text from image")
    else:
        logger.info(f"DEBUG: Vision API extracted {len(extracted_text)} characters")
    return extracted_text
