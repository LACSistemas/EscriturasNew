"""Date formatting utilities for Brazilian Portuguese legal documents"""
from datetime import datetime


def format_date_for_deed() -> str:
    """Format today's date for the deed in Portuguese legal format"""
    today = datetime.now()

    # Number to words mapping
    day_words = {
        1: "primeiro", 2: "dois", 3: "três", 4: "quatro", 5: "cinco",
        6: "seis", 7: "sete", 8: "oito", 9: "nove", 10: "dez",
        11: "onze", 12: "doze", 13: "treze", 14: "quatorze", 15: "quinze",
        16: "dezesseis", 17: "dezessete", 18: "dezoito", 19: "dezenove", 20: "vinte",
        21: "vinte e um", 22: "vinte e dois", 23: "vinte e três", 24: "vinte e quatro",
        25: "vinte e cinco", 26: "vinte e seis", 27: "vinte e sete", 28: "vinte e oito",
        29: "vinte e nove", 30: "trinta", 31: "trinta e um"
    }

    month_names = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }

    year_words = {
        2024: "dois mil e vinte e quatro",
        2025: "dois mil e vinte e cinco",
        2026: "dois mil e vinte e seis",
        2027: "dois mil e vinte e sete",
        2028: "dois mil e vinte e oito",
        2029: "dois mil e vinte e nove",
        2030: "dois mil e trinta"
    }

    day = today.day
    month = today.month
    year = today.year

    day_text = day_words.get(day, str(day))
    month_text = month_names.get(month, "")
    year_text = year_words.get(year, f"dois mil e {year - 2000}")

    return f"aos {day} ({day_text}) dias do mês de {month_text} do ano de {year} ({year_text})"


def format_birth_date(date_str: str) -> str:
    """Convert dates to Portuguese format like '13 de agosto de 1961'"""
    try:
        if '/' in date_str:
            day, month, year = date_str.split('/')
        elif '-' in date_str:
            year, month, day = date_str.split('-')
        else:
            return date_str

        months_pt = {
            '01': 'janeiro', '02': 'fevereiro', '03': 'março', '04': 'abril',
            '05': 'maio', '06': 'junho', '07': 'julho', '08': 'agosto',
            '09': 'setembro', '10': 'outubro', '11': 'novembro', '12': 'dezembro'
        }

        month_name = months_pt.get(month.zfill(2), 'mês')
        return f"{int(day)} de {month_name} de {year}"
    except:
        return date_str


def format_marriage_date(date_str: str) -> str:
    """Format marriage date with both written and numeric format"""
    try:
        if '/' in date_str:
            day, month, year = date_str.split('/')
        elif '-' in date_str:
            year, month, day = date_str.split('-')
        else:
            return date_str

        months_pt = {
            '01': 'janeiro', '02': 'fevereiro', '03': 'março', '04': 'abril',
            '05': 'maio', '06': 'junho', '07': 'julho', '08': 'agosto',
            '09': 'setembro', '10': 'outubro', '11': 'novembro', '12': 'dezembro'
        }

        month_name = months_pt.get(month.zfill(2), 'mês')
        formatted_date = f"{int(day)} de {month_name} de {year}"
        numeric_date = f"({day.zfill(2)}/{month.zfill(2)}/{year})"
        return f"{formatted_date} {numeric_date}"
    except:
        return date_str
