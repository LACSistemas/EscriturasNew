"""Normalized session data structure"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Pessoa:
    """Base person data"""
    tipo: str  # "Pessoa Física" or "Pessoa Jurídica"
    nome_completo: str = ""
    data_nascimento: Optional[str] = None
    documento_tipo: Optional[str] = None
    casado: bool = False
    sexo: Optional[str] = None

    # RG fields
    cpf: Optional[str] = None

    # CNH fields
    cnh_numero: Optional[str] = None
    cnh_orgao_expedidor: Optional[str] = None

    # CTPS fields
    ctps_numero: Optional[str] = None
    ctps_serie: Optional[str] = None

    # Marriage fields
    regime_bens: Optional[str] = None
    data_casamento: Optional[str] = None
    conjuge_assina: bool = False
    conjuge_data: Optional[Dict[str, Any]] = None

    # Pessoa Jurídica fields
    razao_social: Optional[str] = None
    cnpj: Optional[str] = None
    endereco: Optional[str] = None

    # Rural-specific fields
    profissao: Optional[str] = None
    naturalidade: Optional[str] = None
    pai_nome: Optional[str] = None
    mae_nome: Optional[str] = None


@dataclass
class Certidao:
    """Certificate data"""
    tipo: str  # "onus", "negativa_federal", etc
    vendedor_index: Optional[int] = None  # None for property-level certs
    dispensada: bool = False
    data: Dict[str, Any] = field(default_factory=dict)
    uploaded_at: Optional[datetime] = None


@dataclass
class SessionData:
    """Normalized session structure"""
    id: str
    current_step: str
    step_number: int = 1
    created_at: datetime = field(default_factory=datetime.now)

    # Escritura type
    tipo_escritura: Optional[str] = None
    is_rural: bool = False
    tipo_escritura_rural: Optional[str] = None

    # Parties
    compradores: List[Pessoa] = field(default_factory=list)
    vendedores: List[Pessoa] = field(default_factory=list)

    # Certificates (normalized structure)
    certidoes: List[Certidao] = field(default_factory=list)

    # Payment
    valor: Optional[str] = None
    forma_pagamento: Optional[str] = None
    meio_pagamento: Optional[str] = None

    # Temporary data (for building current person/cert)
    temp_comprador: Optional[Pessoa] = None
    temp_vendedor: Optional[Pessoa] = None
    temp_certidao: Optional[Certidao] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for compatibility with existing code)"""
        result = {
            "id": self.id,
            "current_step": self.current_step,
            "step_number": self.step_number,
            "tipo_escritura": self.tipo_escritura,
            "is_rural": self.is_rural,
            "tipo_escritura_rural": self.tipo_escritura_rural,
            "compradores": [vars(c) if not isinstance(c, dict) else c for c in self.compradores],
            "vendedores": [vars(v) if not isinstance(v, dict) else v for v in self.vendedores],
            "certidoes": self._certidoes_to_legacy_format(),
            "valor": self.valor,
            "forma_pagamento": self.forma_pagamento,
            "meio_pagamento": self.meio_pagamento,
            "temp_data": {}
        }

        # Build temp_data compatible with current code
        if self.temp_comprador:
            result["temp_data"]["current_comprador"] = vars(self.temp_comprador) if not isinstance(self.temp_comprador, dict) else self.temp_comprador
        if self.temp_vendedor:
            result["temp_data"]["current_vendedor"] = vars(self.temp_vendedor) if not isinstance(self.temp_vendedor, dict) else self.temp_vendedor

        return result

    def _certidoes_to_legacy_format(self) -> Dict[str, Any]:
        """Convert normalized certidoes to legacy dict format"""
        legacy = {}

        for cert in self.certidoes:
            if cert.vendedor_index is None:
                # Property-level certificate
                key = cert.tipo
            else:
                # Vendor-specific certificate
                key = f"{cert.tipo}_{cert.vendedor_index}"

            legacy[key] = {
                **cert.data,
                "dispensa": cert.dispensada
            }

        return legacy

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """Create from dictionary (for compatibility)"""
        session = cls(
            id=data["id"],
            current_step=data.get("current_step", "tipo_escritura"),
            step_number=data.get("step_number", 1),
            tipo_escritura=data.get("tipo_escritura"),
            is_rural=data.get("is_rural", False),
            tipo_escritura_rural=data.get("tipo_escritura_rural"),
            valor=data.get("valor"),
            forma_pagamento=data.get("forma_pagamento"),
            meio_pagamento=data.get("meio_pagamento")
        )

        # Convert compradores
        for c in data.get("compradores", []):
            session.compradores.append(Pessoa(**c))

        # Convert vendedores
        for v in data.get("vendedores", []):
            session.vendedores.append(Pessoa(**v))

        # Convert certidoes (from legacy format)
        session.certidoes = cls._certidoes_from_legacy_format(data.get("certidoes", {}))

        # Temp data
        temp_data = data.get("temp_data", {})
        if temp_data.get("current_comprador"):
            session.temp_comprador = Pessoa(**temp_data["current_comprador"])
        if temp_data.get("current_vendedor"):
            session.temp_vendedor = Pessoa(**temp_data["current_vendedor"])

        return session

    @staticmethod
    def _certidoes_from_legacy_format(legacy: Dict[str, Any]) -> List[Certidao]:
        """Convert legacy certidoes dict to normalized list"""
        certidoes = []

        for key, value in legacy.items():
            if "_" in key and key.split("_")[-1].isdigit():
                # Vendor-specific: "negativa_federal_0"
                tipo = "_".join(key.split("_")[:-1])
                vendedor_index = int(key.split("_")[-1])
            else:
                # Property-level: "onus", "condominio"
                tipo = key
                vendedor_index = None

            dispensada = value.get("dispensa", False) if isinstance(value, dict) else False
            data = {k: v for k, v in value.items() if k != "dispensa"} if isinstance(value, dict) else value

            certidoes.append(Certidao(
                tipo=tipo,
                vendedor_index=vendedor_index,
                dispensada=dispensada,
                data=data
            ))

        return certidoes

    def get_certidao(self, tipo: str, vendedor_index: Optional[int] = None) -> Optional[Certidao]:
        """Get a specific certificate"""
        for cert in self.certidoes:
            if cert.tipo == tipo and cert.vendedor_index == vendedor_index:
                return cert
        return None

    def add_certidao(self, tipo: str, data: Dict[str, Any], vendedor_index: Optional[int] = None, dispensada: bool = False):
        """Add a certificate"""
        self.certidoes.append(Certidao(
            tipo=tipo,
            vendedor_index=vendedor_index,
            dispensada=dispensada,
            data=data,
            uploaded_at=datetime.now()
        ))

    def save_temp_comprador(self):
        """Save temp comprador to list"""
        if self.temp_comprador:
            self.compradores.append(self.temp_comprador)
            self.temp_comprador = None

    def save_temp_vendedor(self):
        """Save temp vendedor to list"""
        if self.temp_vendedor:
            self.vendedores.append(self.temp_vendedor)
            self.temp_vendedor = None


# ============================================================================
# HYBRID HELPERS - Allow using dict-based sessions with normalized data
# ============================================================================

def ensure_temp_data(session: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure session has temp_data dict"""
    if "temp_data" not in session:
        session["temp_data"] = {}
    return session["temp_data"]


def get_current_comprador(session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get current comprador being built"""
    return session.get("temp_data", {}).get("current_comprador")


def set_current_comprador(session: Dict[str, Any], comprador: Dict[str, Any]):
    """Set current comprador"""
    ensure_temp_data(session)
    session["temp_data"]["current_comprador"] = comprador


def get_current_vendedor(session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get current vendedor being built"""
    return session.get("temp_data", {}).get("current_vendedor")


def set_current_vendedor(session: Dict[str, Any], vendedor: Dict[str, Any]):
    """Set current vendedor"""
    ensure_temp_data(session)
    session["temp_data"]["current_vendedor"] = vendedor


def finalize_and_add_comprador(session: Dict[str, Any]) -> None:
    """Move current comprador from temp_data to compradores list"""
    current = get_current_comprador(session)
    if current:
        if "compradores" not in session:
            session["compradores"] = []
        session["compradores"].append(current)
        session["temp_data"]["current_comprador"] = None


def finalize_and_add_vendedor(session: Dict[str, Any]) -> None:
    """Move current vendedor from temp_data to vendedores list"""
    current = get_current_vendedor(session)
    if current:
        if "vendedores" not in session:
            session["vendedores"] = []
        session["vendedores"].append(current)
        session["temp_data"]["current_vendedor"] = None


def add_certidao_to_session(
    session: Dict[str, Any],
    tipo: str,
    data: Dict[str, Any],
    vendedor_index: Optional[int] = None,
    dispensada: bool = False
) -> None:
    """Add certificate to session (legacy format)"""
    if "certidoes" not in session:
        session["certidoes"] = {}

    if vendedor_index is None:
        key = tipo
    else:
        key = f"{tipo}_{vendedor_index}"

    session["certidoes"][key] = {
        **data,
        "dispensada": dispensada
    }


def create_new_session_dict(session_id: str) -> Dict[str, Any]:
    """Create a new session dict with proper structure"""
    return {
        "id": session_id,
        "current_step": "tipo_escritura",
        "step_number": 1,
        "tipo_escritura": None,
        "is_rural": False,
        "compradores": [],
        "vendedores": [],
        "certidoes": {},
        "temp_data": {},
        "valor": None,
        "forma_pagamento": None,
        "meio_pagamento": None
    }
