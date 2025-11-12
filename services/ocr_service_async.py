"""Async OCR service using Google Cloud Vision API"""
import logging
import asyncio
from google.cloud import vision
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


async def extract_text_from_file_async(file_content: bytes, filename: str = "", vision_client=None) -> str:
    """Process file content asynchronously, handling both PDFs and images"""
    try:
        # Determine if it's a PDF
        if filename.lower().endswith('.pdf') or file_content.startswith(b'%PDF'):
            logger.info("DEBUG: Processing PDF file - converting to image first")
            # PDF processing is CPU-bound, run in executor
            loop = asyncio.get_event_loop()
            img_data = await loop.run_in_executor(None, _convert_pdf_to_image, file_content)

            logger.info("DEBUG: PDF converted to image, extracting text with Vision API")
            return await extract_text_from_image_async(img_data, vision_client)
        else:
            logger.info("DEBUG: Processing as image directly")
            return await extract_text_from_image_async(file_content, vision_client)
    except Exception as e:
        logger.error(f"ERROR: Exception in extract_text_from_file_async: {str(e)}")
        raise


def _convert_pdf_to_image(file_content: bytes) -> bytes:
    """Convert PDF to image (CPU-bound operation)"""
    try:
        pdf_document = fitz.open(stream=file_content, filetype="pdf")

        if len(pdf_document) == 0:
            raise Exception("No pages found in PDF")

        page = pdf_document[0]
        pix = page.get_pixmap()
        img_data = pix.tobytes("png")
        pdf_document.close()

        return img_data
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")


async def extract_text_from_image_async(image_content: bytes, vision_client=None) -> str:
    """Extract text from image using Google Vision API asynchronously"""
    if not vision_client:
        raise Exception("Google Cloud Vision client is not available. Check credentials configuration.")

    image = vision.Image(content=image_content)

    # Vision API calls are I/O-bound, run in executor
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        vision_client.text_detection,
        image
    )

    if response.error.message:
        raise Exception(f"Vision API Error: {response.error.message}")

    extracted_text = response.full_text_annotation.text if response.full_text_annotation else ""
    if not extracted_text:
        logger.warning("WARNING: Vision API extracted no text from image")
    else:
        logger.info(f"DEBUG: Vision API extracted {len(extracted_text)} characters")

    return extracted_text
