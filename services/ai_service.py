"""AI service using Google Gemini for data extraction"""
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def extract_data_with_gemini(text: str, prompt: str, gemini_model=None) -> Dict[str, Any]:
    """Use Gemini to extract structured data from text"""
    try:
        logger.info(f"DEBUG: Starting Gemini extraction. Text length: {len(text)}")
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
            raise Exception("Gemini AI client is not available. Check GEMINI_API_KEY configuration.")

        response = gemini_model.generate_content(full_prompt)
        logger.info(f"DEBUG: Gemini response received: {response.text[:100]}...")

        json_str = response.text.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]

        result = json.loads(json_str.strip())
        logger.info(f"DEBUG: Gemini extraction successful: {result}")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"ERROR: Failed to parse Gemini response as JSON: {e}")
        logger.error(f"ERROR: Gemini response was: {response.text}")
        raise Exception("Failed to parse Gemini response as JSON")
    except Exception as e:
        logger.error(f"ERROR: Exception in extract_data_with_gemini: {str(e)}")
        raise
