"""
Rotas para Templates de Escrituras
CRUD completo + preview + duplicação
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_sync_db
from models.user import User
from models.escritura_template import EscrituraTemplate
from models.escritura_template_schemas import (
    TemplateCreate,
    TemplateUpdate,
    TemplateRead,
    TemplateResponse,
    TemplateListResponse,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
    TIPOS_ESCRITURA
)
from auth.dependencies import get_current_approved_user

router = APIRouter(prefix="/templates", tags=["templates"])


# ============================================================================
# CRUD BÁSICO
# ============================================================================

@router.get("", response_model=TemplateListResponse)
async def list_templates(
    tipo_escritura: Optional[str] = Query(None, description="Filtrar por tipo de escritura"),
    current_user: User = Depends(get_current_approved_user),
    db: Session = Depends(get_sync_db)
):
    """
    📋 Listar templates do usuário atual

    Opcionalmente filtrar por tipo de escritura.
    Retorna apenas templates do usuário autenticado.
    """
    query = db.query(EscrituraTemplate).filter(
        EscrituraTemplate.user_id == current_user.id,
        EscrituraTemplate.is_active == True
    )

    # Filtro opcional por tipo
    if tipo_escritura:
        if tipo_escritura not in TIPOS_ESCRITURA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo inválido. Use um de: {', '.join(TIPOS_ESCRITURA)}"
            )
        query = query.filter(EscrituraTemplate.tipo_escritura == tipo_escritura)

    templates = query.order_by(
        EscrituraTemplate.is_default.desc(),
        EscrituraTemplate.created_at.desc()
    ).all()

    return TemplateListResponse(
        success=True,
        total=len(templates),
        templates=templates
    )


@router.get("/{template_id}", response_model=TemplateRead)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_approved_user),
    db: Session = Depends(get_sync_db)
):
    """
    📄 Obter template específico por ID

    Apenas o dono do template pode acessá-lo.
    """
    template = db.query(EscrituraTemplate).filter(
        EscrituraTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} não encontrado"
        )

    # Verificar ownership (apenas dono ou admin)
    if template.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar este template"
        )

    return template


@router.get("/default/{tipo_escritura}", response_model=TemplateRead)
async def get_default_template(
    tipo_escritura: str,
    current_user: User = Depends(get_current_approved_user),
    db: Session = Depends(get_sync_db)
):
    """
    ⭐ Obter template padrão para um tipo de escritura

    Retorna o template marcado como padrão do usuário para o tipo especificado.
    Se não houver template padrão, retorna erro 404.
    """
    if tipo_escritura not in TIPOS_ESCRITURA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo inválido. Use um de: {', '.join(TIPOS_ESCRITURA)}"
        )

    template = db.query(EscrituraTemplate).filter(
        EscrituraTemplate.user_id == current_user.id,
        EscrituraTemplate.tipo_escritura == tipo_escritura,
        EscrituraTemplate.is_default == True,
        EscrituraTemplate.is_active == True
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhum template padrão encontrado para tipo '{tipo_escritura}'"
        )

    return template


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    current_user: User = Depends(get_current_approved_user),
    db: Session = Depends(get_sync_db)
):
    """
    ✨ Criar novo template

    Cria um novo template para o usuário atual.
    Se is_default=True, remove o flag de outros templates do mesmo tipo.
    """
    # Se está marcando como padrão, remover flag de outros templates do mesmo tipo
    if template_data.is_default:
        db.query(EscrituraTemplate).filter(
            EscrituraTemplate.user_id == current_user.id,
            EscrituraTemplate.tipo_escritura == template_data.tipo_escritura,
            EscrituraTemplate.is_default == True
        ).update({"is_default": False})
        db.commit()

    # Criar novo template
    new_template = EscrituraTemplate(
        user_id=current_user.id,
        tipo_escritura=template_data.tipo_escritura,
        nome_template=template_data.nome_template,
        template_json=template_data.template_json.model_dump(),
        configuracoes_json=template_data.configuracoes_json.model_dump() if template_data.configuracoes_json else None,
        is_default=template_data.is_default,
        is_active=True
    )

    db.add(new_template)
    db.commit()
    db.refresh(new_template)

    return TemplateResponse(
        success=True,
        message=f"Template '{template_data.tipo_escritura}' criado com sucesso",
        template=new_template
    )


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_data: TemplateUpdate,
    current_user: User = Depends(get_current_approved_user),
    db: Session = Depends(get_sync_db)
):
    """
    ✏️ Atualizar template existente

    Atualiza campos fornecidos. Apenas o dono pode atualizar.
    """
    template = db.query(EscrituraTemplate).filter(
        EscrituraTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} não encontrado"
        )

    # Verificar ownership
    if template.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para editar este template"
        )

    # Se está marcando como padrão, remover flag de outros templates do mesmo tipo
    if template_data.is_default and not template.is_default:
        db.query(EscrituraTemplate).filter(
            EscrituraTemplate.user_id == current_user.id,
            EscrituraTemplate.tipo_escritura == template.tipo_escritura,
            EscrituraTemplate.is_default == True,
            EscrituraTemplate.id != template_id
        ).update({"is_default": False})

    # Atualizar campos fornecidos
    update_dict = template_data.model_dump(exclude_unset=True)

    # Converter Pydantic models para dict se necessário
    if "template_json" in update_dict and update_dict["template_json"]:
        update_dict["template_json"] = update_dict["template_json"].model_dump()
    if "configuracoes_json" in update_dict and update_dict["configuracoes_json"]:
        update_dict["configuracoes_json"] = update_dict["configuracoes_json"].model_dump()

    for field, value in update_dict.items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)

    return TemplateResponse(
        success=True,
        message=f"Template atualizado com sucesso",
        template=template
    )


@router.delete("/{template_id}", response_model=TemplateResponse)
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_approved_user),
    db: Session = Depends(get_sync_db)
):
    """
    🗑️ Deletar template (soft delete)

    Marca template como inativo ao invés de deletar.
    Apenas o dono pode deletar.
    """
    template = db.query(EscrituraTemplate).filter(
        EscrituraTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} não encontrado"
        )

    # Verificar ownership
    if template.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para deletar este template"
        )

    # Soft delete
    template.is_active = False
    db.commit()

    return TemplateResponse(
        success=True,
        message=f"Template deletado com sucesso",
        template=None
    )


# ============================================================================
# FUNÇÕES ESPECIAIS
# ============================================================================

@router.patch("/{template_id}/set-default", response_model=TemplateResponse)
async def set_as_default(
    template_id: int,
    current_user: User = Depends(get_current_approved_user),
    db: Session = Depends(get_sync_db)
):
    """
    ⭐ Definir template como padrão

    Marca este template como padrão para seu tipo de escritura.
    Remove flag de outros templates do mesmo tipo.
    """
    template = db.query(EscrituraTemplate).filter(
        EscrituraTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} não encontrado"
        )

    # Verificar ownership
    if template.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para modificar este template"
        )

    # Remover flag de outros templates do mesmo tipo
    db.query(EscrituraTemplate).filter(
        EscrituraTemplate.user_id == current_user.id,
        EscrituraTemplate.tipo_escritura == template.tipo_escritura,
        EscrituraTemplate.is_default == True,
        EscrituraTemplate.id != template_id
    ).update({"is_default": False})

    # Marcar este como padrão
    template.is_default = True
    db.commit()
    db.refresh(template)

    return TemplateResponse(
        success=True,
        message=f"Template definido como padrão para '{template.tipo_escritura}'",
        template=template
    )


@router.post("/{template_id}/duplicate", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_template(
    template_id: int,
    current_user: User = Depends(get_current_approved_user),
    db: Session = Depends(get_sync_db)
):
    """
    📋 Duplicar template

    Cria uma cópia do template para o usuário atual.
    O template duplicado não será marcado como padrão.
    """
    original = db.query(EscrituraTemplate).filter(
        EscrituraTemplate.id == template_id
    ).first()

    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} não encontrado"
        )

    # Verificar ownership
    if original.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para duplicar este template"
        )

    # Criar cópia
    nome_copia = f"{original.nome_template or original.tipo_escritura} (Cópia)"

    duplicate = EscrituraTemplate(
        user_id=current_user.id,
        tipo_escritura=original.tipo_escritura,
        nome_template=nome_copia,
        template_json=original.template_json.copy(),  # Deep copy do JSON
        configuracoes_json=original.configuracoes_json.copy() if original.configuracoes_json else None,
        is_default=False,  # Cópia nunca é padrão
        is_active=True
    )

    db.add(duplicate)
    db.commit()
    db.refresh(duplicate)

    return TemplateResponse(
        success=True,
        message=f"Template duplicado com sucesso",
        template=duplicate
    )


@router.post("/{template_id}/preview", response_model=TemplatePreviewResponse)
async def preview_template(
    template_id: int,
    preview_data: TemplatePreviewRequest,
    current_user: User = Depends(get_current_approved_user),
    db: Session = Depends(get_sync_db)
):
    """
    👁️ Preview do template com dados de exemplo

    Renderiza o template substituindo variáveis pelos dados de exemplo fornecidos.
    Retorna HTML e texto plano.
    """
    template = db.query(EscrituraTemplate).filter(
        EscrituraTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} não encontrado"
        )

    # Verificar ownership
    if template.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para visualizar este template"
        )

    # Gerar preview (função auxiliar - será implementada)
    preview_html, preview_text = generate_preview(template, preview_data.dados_exemplo)

    return TemplatePreviewResponse(
        success=True,
        preview_html=preview_html,
        preview_text=preview_text
    )


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def generate_preview(template: EscrituraTemplate, dados: dict) -> tuple[str, str]:
    """
    Gera preview do template substituindo variáveis

    Returns:
        (html, text): Tupla com HTML renderizado e texto plano
    """
    blocos_ordenados = sorted(
        template.template_json.get("blocos", []),
        key=lambda b: b.get("ordem", 0)
    )

    html_parts = []
    text_parts = []

    for bloco in blocos_ordenados:
        conteudo = bloco.get("conteudo", "")
        formatacao = bloco.get("formatacao", {})

        # Substituir variáveis
        for var, valor in dados.items():
            conteudo = conteudo.replace(f"[{var}]", str(valor))

        # Aplicar formatação HTML
        html_content = conteudo
        if formatacao.get("negrito"):
            html_content = f"<strong>{html_content}</strong>"
        if formatacao.get("italico"):
            html_content = f"<em>{html_content}</em>"
        if formatacao.get("sublinhado"):
            html_content = f"<u>{html_content}</u>"

        align = formatacao.get("alinhamento", "justify")
        html_content = f'<p style="text-align: {align};">{html_content}</p>'

        html_parts.append(html_content)
        text_parts.append(conteudo)

    html = "\n".join(html_parts)
    text = "\n\n".join(text_parts)

    return html, text
