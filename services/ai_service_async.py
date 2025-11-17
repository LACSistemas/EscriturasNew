"""Async AI service using Google Gemini for data extraction"""
import json
import logging
import asyncio
from typing import Dict, Any
from utils.error_handler import async_retry, AIExtractionError, log_processing_step, log_error, log_success

logger = logging.getLogger(__name__)


@async_retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(Exception,))
async def extract_data_with_gemini_async(text: str, prompt: str, gemini_model=None) -> Dict[str, Any]:
    """Use Gemini to extract structured data from text asynchronously with retry logic"""
    try:
        log_processing_step("AI Extraction", {"text_length": len(text), "prompt": prompt[:50] + "..."})

        full_prompt = f"""
        Analyze the following text and extract the requested information.
        Return ONLY a valid JSON object with the requested fields.

        Text to analyze:
        {text}

        Extract the following in JSON format:
        {prompt}

        Important: Return only the JSON object, no additional text or explanation.
        """

        if not gemini_model:
            raise AIExtractionError("Gemini AI client is not available. Check GEMINI_API_KEY configuration.")

        # Gemini API calls are I/O-bound, run in executor
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            gemini_model.generate_content,
            full_prompt
        )

        logger.debug(f"Gemini response received: {response.text[:100]}...")

        # Parse JSON from response
        json_str = response.text.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]

        result = json.loads(json_str.strip())

        log_success(f"AI extraction successful: {len(result)} fields extracted")
        logger.debug(f"Extracted data: {result}")

        return result

    except json.JSONDecodeError as e:
        log_error(e, "AI JSON parsing")
        logger.error(f"Gemini response was: {response.text}")
        raise AIExtractionError("Failed to parse Gemini response as JSON") from e
    except AIExtractionError:
        raise  # Re-raise AIExtractionError to trigger retry
    except Exception as e:
        log_error(e, "AI extraction")
        raise AIExtractionError(f"AI extraction failed: {str(e)}") from e
