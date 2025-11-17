"""Validators for extracted data - CPF, CNPJ, dates, etc."""
import re
from datetime import datetime
from typing import Optional, Tuple


def validate_cpf(cpf: str) -> Tuple[bool, Optional[str]]:
    """Validate CPF format and checksum.

    Args:
        cpf: CPF string (can have dots and dash)

    Returns:
        Tuple of (is_valid, cleaned_cpf or None)
    """
    if not cpf:
        return False, None

    # Remove non-digits
    cpf_clean = re.sub(r'\D', '', cpf)

    # Check length
    if len(cpf_clean) != 11:
        return False, None

    # Check if all digits are the same (invalid CPFs like 111.111.111-11)
    if cpf_clean == cpf_clean[0] * 11:
        return False, None

    # Validate checksum
    def calc_digit(cpf_partial: str, multiplier: int) -> int:
        soma = sum(int(cpf_partial[i]) * (multiplier - i) for i in range(len(cpf_partial)))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    # First digit
    first_digit = calc_digit(cpf_clean[:9], 10)
    if first_digit != int(cpf_clean[9]):
        return False, None

    # Second digit
    second_digit = calc_digit(cpf_clean[:10], 11)
    if second_digit != int(cpf_clean[10]):
        return False, None

    # Format as XXX.XXX.XXX-XX
    cpf_formatted = f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
    return True, cpf_formatted


def validate_cnpj(cnpj: str) -> Tuple[bool, Optional[str]]:
    """Validate CNPJ format and checksum.

    Args:
        cnpj: CNPJ string (can have dots, slash and dash)

    Returns:
        Tuple of (is_valid, cleaned_cnpj or None)
    """
    if not cnpj:
        return False, None

    # Remove non-digits
    cnpj_clean = re.sub(r'\D', '', cnpj)

    # Check length
    if len(cnpj_clean) != 14:
        return False, None

    # Check if all digits are the same
    if cnpj_clean == cnpj_clean[0] * 14:
        return False, None

    # Validate checksum
    def calc_digit(cnpj_partial: str, positions: list) -> int:
        soma = sum(int(cnpj_partial[i]) * positions[i] for i in range(len(cnpj_partial)))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    # First digit
    positions_first = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    first_digit = calc_digit(cnpj_clean[:12], positions_first)
    if first_digit != int(cnpj_clean[12]):
        return False, None

    # Second digit
    positions_second = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    second_digit = calc_digit(cnpj_clean[:13], positions_second)
    if second_digit != int(cnpj_clean[13]):
        return False, None

    # Format as XX.XXX.XXX/XXXX-XX
    cnpj_formatted = f"{cnpj_clean[:2]}.{cnpj_clean[2:5]}.{cnpj_clean[5:8]}/{cnpj_clean[8:12]}-{cnpj_clean[12:]}"
    return True, cnpj_formatted


def validate_date(date_str: str, allow_future: bool = True) -> Tuple[bool, Optional[str]]:
    """Validate date format and value.

    Args:
        date_str: Date string in various formats
        allow_future: If False, reject future dates

    Returns:
        Tuple of (is_valid, formatted_date YYYY-MM-DD or None)
    """
    if not date_str:
        return False, None

    # Try common Brazilian date formats
    formats = [
        "%d/%m/%Y",     # 31/12/2023
        "%d-%m-%Y",     # 31-12-2023
        "%Y-%m-%d",     # 2023-12-31
        "%d/%m/%y",     # 31/12/23
        "%d.%m.%Y",     # 31.12.2023
    ]

    parsed_date = None
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str.strip(), fmt)
            break
        except ValueError:
            continue

    if not parsed_date:
        return False, None

    # Check if future date (optional)
    if not allow_future and parsed_date > datetime.now():
        return False, None

    # Format as YYYY-MM-DD
    formatted = parsed_date.strftime("%Y-%m-%d")
    return True, formatted


def validate_monetary_value(value_str: str) -> Tuple[bool, Optional[float]]:
    """Validate and parse monetary value.

    Args:
        value_str: Monetary value string (e.g., "R$ 1.234,56" or "1234.56")

    Returns:
        Tuple of (is_valid, parsed_float or None)
    """
    if not value_str:
        return False, None

    # Remove currency symbols and spaces
    clean_str = value_str.replace("R$", "").replace(" ", "").strip()

    # Try Brazilian format first (1.234,56)
    if "," in clean_str and "." in clean_str:
        # Brazilian: dots are thousands, comma is decimal
        clean_str = clean_str.replace(".", "").replace(",", ".")
    elif "," in clean_str:
        # Only comma, assume decimal
        clean_str = clean_str.replace(",", ".")

    try:
        value = float(clean_str)
        if value < 0:
            return False, None
        return True, value
    except ValueError:
        return False, None


def sanitize_extracted_data(data: dict) -> dict:
    """Sanitize and validate extracted data from AI.

    Args:
        data: Dictionary of extracted fields

    Returns:
        Sanitized dictionary with valid data only
    """
    sanitized = {}

    for key, value in data.items():
        if not value or value == "":
            continue

        # Detect field type and validate
        key_lower = key.lower()

        # CPF validation
        if "cpf" in key_lower and "cnpj" not in key_lower:
            is_valid, cleaned = validate_cpf(str(value))
            if is_valid:
                sanitized[key] = cleaned
            else:
                sanitized[key] = str(value)  # Keep original if invalid

        # CNPJ validation
        elif "cnpj" in key_lower:
            is_valid, cleaned = validate_cnpj(str(value))
            if is_valid:
                sanitized[key] = cleaned
            else:
                sanitized[key] = str(value)  # Keep original if invalid

        # Date validation
        elif any(word in key_lower for word in ["data", "validade", "emissão", "emissao", "nascimento", "casamento"]):
            is_valid, formatted = validate_date(str(value), allow_future=True)
            if is_valid:
                sanitized[key] = formatted
            else:
                sanitized[key] = str(value)  # Keep original if invalid

        # Monetary value validation
        elif any(word in key_lower for word in ["valor", "débito", "debito"]):
            is_valid, parsed = validate_monetary_value(str(value))
            if is_valid:
                sanitized[key] = parsed
            else:
                sanitized[key] = str(value)  # Keep original if invalid

        else:
            # No validation needed, keep as is
            sanitized[key] = str(value).strip()

    return sanitized
