"""Helper utility functions"""
import random
import string
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def generate_hash_code() -> str:
    """Generate random 10-character hash codes for certificates"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


def count_effective_people(parties: List[Dict]) -> int:
    """Count the effective number of people including signing spouses"""
    total_people = 0

    for party in parties:
        if party.get("tipo") == "Pessoa Física":
            total_people += 1  # The party themselves
            # Add spouse if they sign the document
            if party.get("casado") and party.get("conjuge_assina"):
                total_people += 1
        else:
            # Pessoa Jurídica counts as 1
            total_people += 1

    return total_people


def ensure_temp_data_saved(session: Dict[str, Any]) -> None:
    """Ensure any remaining temp data gets moved to final arrays"""
    temp_data = session.get("temp_data", {})

    # Save current_comprador if exists
    if "current_comprador" in temp_data and temp_data["current_comprador"]:
        logger.info("DEBUG: Saving remaining current_comprador to final array")
        session["compradores"].append(temp_data["current_comprador"])
        temp_data["current_comprador"] = None

    # Save current_vendedor if exists
    if "current_vendedor" in temp_data and temp_data["current_vendedor"]:
        logger.info("DEBUG: Saving remaining current_vendedor to final array")
        session["vendedores"].append(temp_data["current_vendedor"])
        temp_data["current_vendedor"] = None
