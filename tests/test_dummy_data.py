"""
Dummy data generators and mocks for end-to-end workflow testing

This module provides:
- Realistic Brazilian dummy data (valid CPFs, CNPJs, names, addresses)
- Mock functions for OCR and AI services
- Test data generators for all document types
"""
import json
import random
from typing import Dict, Any
from datetime import datetime, timedelta


# ============================================================================
# BRAZILIAN REALISTIC DATA GENERATORS
# ============================================================================

def generate_valid_cpf() -> str:
    """Generate a valid Brazilian CPF with correct checksum"""
    def calculate_digit(cpf_digits, weight):
        total = sum(int(cpf_digits[i]) * weight[i] for i in range(len(cpf_digits)))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    # Generate first 9 digits
    cpf = [random.randint(0, 9) for _ in range(9)]

    # Calculate first check digit
    weight1 = list(range(10, 1, -1))
    cpf.append(calculate_digit(cpf, weight1))

    # Calculate second check digit
    weight2 = list(range(11, 1, -1))
    cpf.append(calculate_digit(cpf, weight2))

    # Format: XXX.XXX.XXX-XX
    cpf_str = ''.join(map(str, cpf))
    return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}"


def generate_valid_cnpj() -> str:
    """Generate a valid Brazilian CNPJ with correct checksum"""
    def calculate_digit(cnpj_digits, weights):
        total = sum(int(cnpj_digits[i]) * weights[i] for i in range(len(cnpj_digits)))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    # Generate base: 8 digits + 0001 + XX
    base = [random.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]

    # Calculate first check digit
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    base.append(calculate_digit(base, weights1))

    # Calculate second check digit
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    base.append(calculate_digit(base, weights2))

    # Format: XX.XXX.XXX/0001-XX
    cnpj_str = ''.join(map(str, base))
    return f"{cnpj_str[:2]}.{cnpj_str[2:5]}.{cnpj_str[5:8]}/{cnpj_str[8:12]}-{cnpj_str[12:]}"


FIRST_NAMES_M = ["João", "Carlos", "Pedro", "Lucas", "Rafael", "Fernando", "Roberto", "Paulo", "Marcos", "André"]
FIRST_NAMES_F = ["Maria", "Ana", "Carla", "Cecília", "Fernanda", "Juliana", "Patricia", "Renata", "Beatriz", "Claudia"]
LAST_NAMES = ["Silva", "Santos", "Oliveira", "Souza", "Lima", "Costa", "Pereira", "Rodrigues", "Almeida", "Nascimento"]

def generate_name(gender: str = "Masculino") -> str:
    """Generate a realistic Brazilian name"""
    first_names = FIRST_NAMES_M if gender == "Masculino" else FIRST_NAMES_F
    first = random.choice(first_names)
    middle = random.choice(LAST_NAMES)
    last = random.choice(LAST_NAMES)
    return f"{first} {middle} {last}"


def generate_date(years_back_min: int = 25, years_back_max: int = 70) -> str:
    """Generate a date in ISO format (YYYY-MM-DD)"""
    days_back = random.randint(years_back_min * 365, years_back_max * 365)
    date = datetime.now() - timedelta(days=days_back)
    return date.strftime("%Y-%m-%d")


def generate_rg() -> str:
    """Generate a realistic RG number"""
    return f"{random.randint(10, 99)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(0, 9)}"


def generate_cnh() -> str:
    """Generate a realistic CNH number"""
    return f"{random.randint(10000000000, 99999999999)}"


def generate_address() -> str:
    """Generate a realistic Brazilian address"""
    streets = ["Rua das Flores", "Avenida Paulista", "Rua dos Três Irmãos", "Avenida Brasil", "Rua XV de Novembro"]
    cities = ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Curitiba", "Porto Alegre"]
    states = ["SP", "RJ", "MG", "PR", "RS"]

    street = random.choice(streets)
    number = random.randint(100, 9999)
    city = random.choice(cities)
    state = random.choice(states)
    cep = f"{random.randint(10000, 99999)}-{random.randint(100, 999)}"

    return f"{street}, {number}, {city} - {state}, CEP {cep}"


def generate_empresa_name() -> str:
    """Generate a realistic company name"""
    prefixes = ["Construtora", "Incorporadora", "Empreendimentos", "Desenvolvimento", "Comercial"]
    suffixes = ["Ltda", "S.A.", "EIRELI", "ME"]

    prefix = random.choice(prefixes)
    name = random.choice(LAST_NAMES)
    suffix = random.choice(suffixes)

    return f"{prefix} {name} {suffix}"


# ============================================================================
# DOCUMENT DATA GENERATORS - Return structured JSON like Gemini would
# ============================================================================

def generate_rg_data(gender: str = "Masculino") -> Dict[str, Any]:
    """Generate RG document data"""
    return {
        "Nome Completo": generate_name(gender),
        "Data de Nascimento": generate_date(25, 70),
        "Número do CPF": generate_valid_cpf(),
        "Gênero": gender
    }


def generate_cnh_data(gender: str = "Masculino") -> Dict[str, Any]:
    """Generate CNH document data"""
    return {
        "Nome Completo": generate_name(gender),
        "Data de Nascimento": generate_date(25, 70),
        "Número da CNH": generate_cnh(),
        "Órgão de Expedição da CNH": "DETRAN/SP",
        "Gênero": gender
    }


def generate_ctps_data(gender: str = "Masculino") -> Dict[str, Any]:
    """Generate CTPS document data"""
    return {
        "Nome Completo": generate_name(gender),
        "Série da Carteira": f"{random.randint(1000, 9999)}",
        "Número da Carteira": f"{random.randint(100000, 999999)}",
        "Gênero": gender
    }


def generate_empresa_data() -> Dict[str, Any]:
    """Generate empresa (CNPJ) document data"""
    return {
        "Razão Social": generate_empresa_name(),
        "CNPJ": generate_valid_cnpj(),
        "Endereço completo": generate_address(),
        "Nome do Representante Legal": generate_name("Masculino")
    }


def generate_certidao_casamento_data() -> Dict[str, Any]:
    """Generate certidão de casamento data"""
    regimes = ["Comunhão Parcial de Bens", "Comunhão Universal de Bens", "Separação Total de Bens"]
    return {
        "Nome Completo do Cônjuge": generate_name(random.choice(["Masculino", "Feminino"])),
        "Data do Casamento": generate_date(1, 40),
        "Regime de Bens": random.choice(regimes),
        "Cartório de Registro": f"Cartório do {random.randint(1, 20)}º Subdistrito de São Paulo"
    }


def generate_certidao_nascimento_data() -> Dict[str, Any]:
    """Generate certidão de nascimento data"""
    return {
        "Nome do Pai": generate_name("Masculino"),
        "Nome da Mãe": generate_name("Feminino")
    }


def generate_certidao_negativa_data() -> Dict[str, Any]:
    """Generate certidão negativa (federal/estadual/municipal/trabalhista) data"""
    return {
        "Nome do Titular": generate_name(random.choice(["Masculino", "Feminino"])),
        "CPF/CNPJ": generate_valid_cpf() if random.random() > 0.3 else generate_valid_cnpj(),
        "Data de Emissão": generate_date(0, 1),  # Recent (last year)
        "Validade": (datetime.now() + timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d")
    }


def generate_certidao_onus_data() -> Dict[str, Any]:
    """Generate certidão de ônus reais data"""
    possui_onus = random.choice(["Sim", "Não"])
    return {
        "Data de Emissão": generate_date(0, 1),
        "Validade": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
        "Matrícula do Imóvel": f"{random.randint(10000, 99999)}",
        "Possui Ônus?": possui_onus,
        "Descrição dos Ônus (se houver)": "Hipoteca Banco XYZ" if possui_onus == "Sim" else "Nada consta"
    }


def generate_certidao_matricula_data() -> Dict[str, Any]:
    """Generate matrícula do imóvel data"""
    return {
        "Número da Matrícula": f"{random.randint(10000, 99999)}",
        "Cartório de Registro": f"{random.randint(1, 20)}º Registro de Imóveis de São Paulo",
        "Proprietário Atual": generate_name(random.choice(["Masculino", "Feminino"])),
        "Área do Imóvel": f"{random.randint(50, 500)}m²",
        "Endereço Completo": generate_address()
    }


def generate_certidao_iptu_data() -> Dict[str, Any]:
    """Generate certidão de IPTU data"""
    possui_debitos = random.choice(["Sim", "Não"])
    return {
        "Inscrição Imobiliária": f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(1000, 9999)}-{random.randint(0, 9)}",
        "Endereço do Imóvel": generate_address(),
        "Último Ano Pago": str(datetime.now().year - 1),
        "Débitos Pendentes (Sim/Não)": possui_debitos,
        "Valor dos Débitos (se houver)": f"R$ {random.randint(500, 5000)},00" if possui_debitos == "Sim" else "R$ 0,00"
    }


def generate_certidao_condominio_data() -> Dict[str, Any]:
    """Generate certidão de condomínio data"""
    possui_debitos = random.choice(["Sim", "Não"])
    return {
        "Número da Matrícula": f"{random.randint(10000, 99999)}",
        "Data de Emissão": generate_date(0, 1),
        "Débitos Pendentes (Sim/Não)": possui_debitos,
        "Valor dos Débitos (se houver)": f"R$ {random.randint(200, 2000)},00" if possui_debitos == "Sim" else "R$ 0,00"
    }


def generate_certidao_objeto_pe_data() -> Dict[str, Any]:
    """Generate certidão de objeto e pé data"""
    return {
        "Número da Matrícula": f"{random.randint(10000, 99999)}",
        "Unidade/Apartamento": f"{random.randint(1, 20)}{random.randint(1, 4)}",
        "Bloco/Torre": random.choice(["A", "B", "C", "Torre 1", "Torre 2"]),
        "Data de Emissão": generate_date(0, 1),
        "Validade": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    }


# ============================================================================
# RURAL CERTIDÕES
# ============================================================================

def generate_certidao_itr_data() -> Dict[str, Any]:
    """Generate ITR data"""
    possui_debitos = random.choice(["Sim", "Não"])
    return {
        "NIRF": f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(0, 9)}",
        "Área Total (hectares)": f"{random.randint(10, 500)} hectares",
        "Último Ano Pago": str(datetime.now().year - 1),
        "Débitos Pendentes (Sim/Não)": possui_debitos
    }


def generate_certidao_ccir_data() -> Dict[str, Any]:
    """Generate CCIR data"""
    return {
        "Código CCIR": f"{random.randint(100000000, 999999999)}",
        "NIRF": f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(0, 9)}",
        "Área Total (hectares)": f"{random.randint(10, 500)} hectares",
        "Data de Emissão": generate_date(0, 2),
        "Situação (Regular/Irregular)": "Regular"
    }


def generate_certidao_incra_data() -> Dict[str, Any]:
    """Generate INCRA data"""
    possui_debitos = random.choice(["Sim", "Não"])
    return {
        "NIRF": f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(0, 9)}",
        "Data de Emissão": generate_date(0, 1),
        "Validade": (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d"),
        "Débitos (Sim/Não)": possui_debitos
    }


def generate_certidao_ibama_data() -> Dict[str, Any]:
    """Generate IBAMA data"""
    possui_infracoes = random.choice(["Sim", "Não"])
    return {
        "Proprietário": generate_name(random.choice(["Masculino", "Feminino"])),
        "CPF/CNPJ": generate_valid_cpf(),
        "Data de Emissão": generate_date(0, 1),
        "Validade": (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d"),
        "Infrações (Sim/Não)": possui_infracoes
    }


def generate_art_desmembramento_data() -> Dict[str, Any]:
    """Generate ART de desmembramento data"""
    return {
        "Número ART": f"{random.randint(1000000, 9999999)}",
        "Responsável Técnico": generate_name("Masculino"),
        "CREA": f"CREA/SP {random.randint(100000, 999999)}",
        "Data de Emissão": generate_date(0, 2),
        "Área Total Desmembrada (hectares)": f"{random.randint(10, 200)} hectares"
    }


def generate_planta_desmembramento_data() -> Dict[str, Any]:
    """Generate planta de desmembramento data"""
    return {
        "Área do Lote (hectares)": f"{random.randint(5, 100)} hectares",
        "Confrontações/Divisas": "Norte: Fazenda São José, Sul: Rodovia BR-101, Leste: Rio Paraíba, Oeste: Fazenda Santa Clara",
        "Número do Lote": f"Lote {random.randint(1, 50)}",
        "Responsável Técnico": generate_name("Masculino")
    }


# ============================================================================
# MOCK FUNCTIONS - Replace OCR and AI services
# ============================================================================

class MockOCRService:
    """Mock OCR service that returns dummy text"""

    @staticmethod
    async def extract_text_from_file_async(file_data: bytes, filename: str, vision_client=None) -> str:
        """Return mock OCR text based on document type"""
        # In real scenario, this would call Vision API
        # For testing, we return a simple placeholder text
        return f"[MOCK OCR TEXT FROM {filename}]"


class MockAIService:
    """Mock AI service that returns structured data based on document type"""

    # Store mapping of prompts to generators
    PROMPT_GENERATORS = {
        # Comprador/Vendedor documents
        "Número do CPF": lambda: generate_rg_data(),
        "Número da CNH": lambda: generate_cnh_data(),
        "Série da Carteira": lambda: generate_ctps_data(),
        "Razão Social": lambda: generate_empresa_data(),

        # Certidões
        "Nome Completo do Cônjuge": lambda: generate_certidao_casamento_data(),
        "Nome do Pai": lambda: generate_certidao_nascimento_data(),  # Certidão de nascimento
        "Nome do Titular": lambda: generate_certidao_negativa_data(),
        "Matrícula do Imóvel": lambda: generate_certidao_onus_data(),
        "Número da Matrícula": lambda: generate_certidao_matricula_data(),
        "Inscrição Imobiliária": lambda: generate_certidao_iptu_data(),
        "Débitos Pendentes": lambda: generate_certidao_condominio_data(),
        "Unidade/Apartamento": lambda: generate_certidao_objeto_pe_data(),

        # Rural certidões
        "NIRF": lambda: generate_certidao_itr_data(),
        "Código CCIR": lambda: generate_certidao_ccir_data(),
        "Número ART": lambda: generate_art_desmembramento_data(),
        "Área do Lote": lambda: generate_planta_desmembramento_data(),
    }

    @staticmethod
    async def extract_data_with_gemini_async(text: str, prompt: str, gemini_model=None) -> Dict[str, Any]:
        """Return mock structured data based on prompt"""
        # Determine which generator to use based on prompt content
        for keyword, generator in MockAIService.PROMPT_GENERATORS.items():
            if keyword in prompt:
                return generator()

        # Default: return empty dict
        return {}


# ============================================================================
# HELPER: Create mock clients
# ============================================================================

def get_mock_clients():
    """Return mock vision and gemini clients for testing"""
    return MockOCRService(), MockAIService()


# ============================================================================
# TEST DATA SCENARIOS
# ============================================================================

SCENARIO_LOTE_SIMPLES = {
    "tipo_escritura": "Escritura de Lote",
    "compradores": [
        {
            "tipo": "Pessoa Física",
            "documento_tipo": "Carteira de Identidade",
            "casado": False,
            "gender": "Masculino"
        }
    ],
    "vendedores": [
        {
            "tipo": "Pessoa Física",
            "documento_tipo": "CNH",
            "casado": False,
            "gender": "Masculino",
            "certidoes_option": "Apresentar"  # All certidões presented
        }
    ],
    "certidoes_imovel": {
        "matricula": "Apresentar",
        "iptu": "Apresentar",
        "onus": "Apresentar"
    },
    "eh_apartamento": False,
    "valor": "R$ 250.000,00",
    "forma_pagamento": "À VISTA",
    "meio_pagamento": "transferência bancária/pix"
}

SCENARIO_APTO_COMPLEXO = {
    "tipo_escritura": "Escritura de Apto",
    "compradores": [
        {
            "tipo": "Pessoa Física",
            "documento_tipo": "Carteira de Identidade",
            "casado": True,
            "conjuge_assina": True,
            "conjuge_doc_tipo": "CNH",
            "gender": "Masculino",
            "conjuge_gender": "Feminino"
        },
        {
            "tipo": "Pessoa Física",
            "documento_tipo": "CNH",
            "casado": False,
            "gender": "Feminino"
        }
    ],
    "vendedores": [
        {
            "tipo": "Pessoa Jurídica",
            "certidoes_option": ["Apresentar", "Dispensar", "Apresentar", "Dispensar"]  # Mix
        }
    ],
    "certidoes_imovel": {
        "matricula": "Apresentar",
        "iptu": "Dispensar",
        "onus": "Apresentar",
        "condominio": "Apresentar",
        "objeto_pe": "Apresentar"
    },
    "eh_apartamento": True,
    "valor": "R$ 450.000,00",
    "forma_pagamento": "ANTERIORMENTE",
    "meio_pagamento": "transferência bancária/pix"
}

SCENARIO_RURAL_SEM_DESMEMBRAMENTO = {
    "tipo_escritura": "Escritura Rural",
    "compradores": [
        {
            "tipo": "Pessoa Física",
            "documento_tipo": "Carteira de Identidade",
            "casado": True,
            "conjuge_assina": True,
            "conjuge_doc_tipo": "Carteira de Identidade",
            "gender": "Masculino",
            "conjuge_gender": "Feminino"
        }
    ],
    "vendedores": [
        {
            "tipo": "Pessoa Física",
            "documento_tipo": "CNH",
            "casado": False,
            "gender": "Masculino",
            "certidoes_option": "Apresentar"
        },
        {
            "tipo": "Pessoa Física",
            "documento_tipo": "Carteira de Identidade",
            "casado": False,
            "gender": "Feminino",
            "certidoes_option": "Apresentar"
        }
    ],
    "certidoes_rurais": {
        "itr": "Apresentar",
        "ccir": "Apresentar",
        "incra": "Apresentar",
        "ibama": "Apresentar"
    },
    "tem_desmembramento": False,
    "valor": "R$ 1.200.000,00",
    "forma_pagamento": "À VISTA",
    "meio_pagamento": "transferência bancária/pix"
}

SCENARIO_RURAL_COM_DESMEMBRAMENTO = {
    "tipo_escritura": "Escritura Rural com Desmembramento de Área",
    "compradores": [
        {
            "tipo": "Pessoa Física",
            "documento_tipo": "CNH",
            "casado": False,
            "gender": "Masculino"
        }
    ],
    "vendedores": [
        {
            "tipo": "Pessoa Física",
            "documento_tipo": "Carteira de Identidade",
            "casado": True,
            "conjuge_assina": True,
            "conjuge_doc_tipo": "CNH",
            "gender": "Masculino",
            "conjuge_gender": "Feminino",
            "certidoes_option": "Apresentar"
        }
    ],
    "certidoes_rurais": {
        "itr": "Apresentar",
        "ccir": "Apresentar",
        "incra": "Dispensar",
        "ibama": "Apresentar"
    },
    "tem_desmembramento": True,
    "desmembramento": {
        "art": "Apresentar",
        "planta": "Apresentar"
    },
    "valor": "R$ 850.000,00",
    "forma_pagamento": "À VISTA",
    "meio_pagamento": "dinheiro"
}
