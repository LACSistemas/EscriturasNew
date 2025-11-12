"""Gender concordance utilities for Brazilian Portuguese"""
from typing import Dict, List, Any
from .helpers import count_effective_people


def determine_gender_suffix(parties: List[Dict], is_vendedor: bool) -> Dict[str, str]:
    """Determine the correct gender suffixes based on the parties"""
    if not parties:
        return {
            "title": "VENDEDOR" if is_vendedor else "COMPRADOR",
            "article": "o",
            "plural": "",
            "possessive": "or"
        }

    # Check if any party is Pessoa Jurídica (companies are feminine in Brazilian legal language)
    has_company = any(party.get("tipo") == "Pessoa Jurídica" for party in parties)

    # Count males and females (for physical persons only)
    # IMPORTANT: Include signing spouses in the count
    males = 0
    females = 0

    for p in parties:
        if p.get("tipo") == "Pessoa Física":
            # Count the main person
            gender = p.get("sexo", "").lower()
            if gender in ['masculino', 'm', 'male']:
                males += 1
            elif gender in ['feminino', 'f', 'female']:
                females += 1
            else:
                # Fallback: no explicit gender found, default to masculine
                males += 1

            # Count signing spouse
            if p.get("casado") and p.get("conjuge_assina") and p.get("conjuge_data"):
                spouse_gender = p["conjuge_data"].get("sexo", "").lower()
                if spouse_gender in ['masculino', 'm', 'male']:
                    males += 1
                elif spouse_gender in ['feminino', 'f', 'female']:
                    females += 1
                else:
                    # Fallback: no explicit gender found, default to masculine
                    males += 1

    # Use effective people count (including signing spouses)
    total_effective_people = count_effective_people(parties)
    physical_persons = sum(1 for p in parties if p.get("tipo") == "Pessoa Física")

    if total_effective_people == 1:
        # Single person (no signing spouse)
        if has_company:
            # Single company - always feminine
            return {
                "title": "VENDEDORA" if is_vendedor else "COMPRADORA",
                "article": "a",
                "plural": "",
                "possessive": "ora"
            }
        elif females > 0 and males == 0:
            # Single female person
            return {
                "title": "VENDEDORA" if is_vendedor else "COMPRADORA",
                "article": "a",
                "plural": "",
                "possessive": "ora"
            }
        else:
            # Single male person (or default)
            return {
                "title": "VENDEDOR" if is_vendedor else "COMPRADOR",
                "article": "o",
                "plural": "",
                "possessive": "or"
            }
    else:
        # Multiple people (including cases with signing spouse) - always use plural forms
        if has_company and physical_persons == 0:
            # Only companies - feminine plural
            return {
                "title": "VENDEDORAS" if is_vendedor else "COMPRADORAS",
                "article": "as",
                "plural": "s",
                "possessive": "ras"
            }
        elif males > 0:
            # At least one male (mixed or all male) - masculine plural (Brazilian grammar rule)
            return {
                "title": "VENDEDORES" if is_vendedor else "COMPRADORES",
                "article": "os",
                "plural": "s",
                "possessive": "res"
            }
        else:
            # All female persons or mix of companies and females - feminine plural
            return {
                "title": "VENDEDORAS" if is_vendedor else "COMPRADORAS",
                "article": "as",
                "plural": "s",
                "possessive": "ras"
            }


def get_gender_agreement(person: Dict[str, Any]) -> Dict[str, str]:
    """Get gender agreement for participles based on person's gender"""
    gender = person.get("sexo", "").lower()
    if gender in ['feminino', 'f', 'female']:
        return {
            "nascido": "Nascida",
            "inscrito": "Inscrita",
            "portador": "Portadora"
        }
    else:
        # Default to masculine for unknown or male
        return {
            "nascido": "Nascido",
            "inscrito": "Inscrito",
            "portador": "Portador"
        }
