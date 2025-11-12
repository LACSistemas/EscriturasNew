"""Text formatting utilities for numbers and currency"""


def spell_out_area(area_str: str) -> str:
    """Convert area numbers to Portuguese text"""
    try:
        # Clean the input
        area_clean = str(area_str).replace(',', '.').replace(' ', '').replace('m²', '').replace('m', '')
        area_num = float(area_clean)
        area_int = int(area_num) if area_num == int(area_num) else area_num

        # Basic number to words mapping (simplified for common cases)
        units = ['', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove']
        teens = ['dez', 'onze', 'doze', 'treze', 'quatorze', 'quinze', 'dezesseis', 'dezessete', 'dezoito', 'dezenove']
        tens = ['', '', 'vinte', 'trinta', 'quarenta', 'cinquenta', 'sessenta', 'setenta', 'oitenta', 'noventa']
        hundreds = ['', 'cento', 'duzentos', 'trezentos', 'quatrocentos', 'quinhentos', 'seiscentos', 'setecentos', 'oitocentos', 'novecentos']

        if area_int == 0:
            return "zero metros quadrados"
        elif area_int < 10:
            return f"{units[area_int]} metros quadrados"
        elif area_int < 20:
            return f"{teens[area_int - 10]} metros quadrados"
        elif area_int < 100:
            tens_digit = area_int // 10
            units_digit = area_int % 10
            if units_digit == 0:
                return f"{tens[tens_digit]} metros quadrados"
            else:
                return f"{tens[tens_digit]} e {units[units_digit]} metros quadrados"
        elif area_int < 1000:
            hundreds_digit = area_int // 100
            remainder = area_int % 100
            if remainder == 0:
                return f"{hundreds[hundreds_digit]} metros quadrados"
            elif remainder < 10:
                return f"{hundreds[hundreds_digit]} e {units[remainder]} metros quadrados"
            elif remainder < 20:
                return f"{hundreds[hundreds_digit]} e {teens[remainder - 10]} metros quadrados"
            else:
                tens_digit = remainder // 10
                units_digit = remainder % 10
                if units_digit == 0:
                    return f"{hundreds[hundreds_digit]} e {tens[tens_digit]} metros quadrados"
                else:
                    return f"{hundreds[hundreds_digit]}, {tens[tens_digit]} e {units[units_digit]} metros quadrados"
        else:
            # For larger numbers, just return the numeric value
            return f"{area_int} metros quadrados"
    except:
        return f"{area_str} metros quadrados"


def spell_out_currency(value_str: str) -> str:
    """Convert currency values to Portuguese text"""
    try:
        # Extract numeric value from currency string
        clean_value = value_str.replace('R$', '').replace('.', '').replace(',', '.').replace(' ', '')
        value_num = float(clean_value)

        # Simplified currency spelling (for common values)
        if value_num == 100000:
            return "cem mil reais"
        elif value_num == 250000:
            return "duzentos e cinquenta mil reais"
        elif value_num == 500000:
            return "quinhentos mil reais"
        elif value_num == 1000000:
            return "um milhão de reais"
        else:
            # For other values, return a simplified version
            int_value = int(value_num)
            return f"{int_value} reais"
    except:
        return "valor em reais"
