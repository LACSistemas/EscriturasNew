"""Enums used throughout the application"""
from enum import Enum


class TipoEscritura(str, Enum):
    LOTE = "Escritura de Lote"
    APTO = "Escritura de Apto"
    RURAL = "Escritura Rural"
    RURAL_DESMEMBRAMENTO = "Escritura Rural com Desmembramento de Área"


class TipoPessoa(str, Enum):
    FISICA = "Pessoa Física"
    JURIDICA = "Pessoa Jurídica"


class TipoDocumento(str, Enum):
    IDENTIDADE = "Carteira de Identidade"
    CNH = "CNH"
    CTPS = "Carteira de Trabalho"


class CertificateTypeRural(str, Enum):
    EXECUCOES_FISCAIS = "Certidão de Execuções Fiscais"
    DISTRIBUICAO_ACOES = "Certidão de Distribuição de Ações"
    ITR = "Certidão do ITR"
    CCIR = "CCIR 2025"
    IBAMA = "Certidão do IBAMA"
    ART = "ART"
    PLANTA_TERRENO = "Planta do Terreno"
