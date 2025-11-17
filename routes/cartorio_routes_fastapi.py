"""FastAPI Cartório configuration routes"""
from fastapi import APIRouter, HTTPException, Request
from models.schemas import CartorioConfigRequest, CartorioConfigResponse, MessageResponse
from database import get_cartorio_config, update_cartorio_config
from gender_concordance import validate_gender_concordance, get_cartorio_template_data
from typing import Dict, Any

router = APIRouter(tags=["cartorio"])


def require_auth(request: Request):
    """Check if user is authenticated"""
    if not request.session.get('authenticated'):
        raise HTTPException(status_code=401, detail="Authentication required")
    user_id = request.session.get('user')
    if not user_id:
        raise HTTPException(status_code=401, detail="User not found in session")
    return user_id


@router.get("/cartorio/config", response_model=CartorioConfigResponse)
async def get_config(request: Request):
    """Get cartório configuration for authenticated user"""
    try:
        user_id = require_auth(request)

        config = get_cartorio_config(user_id)
        if not config:
            config = {
                'distrito': 'Campo Grande / Jardim América',
                'municipio': 'Cariacica',
                'comarca': 'Vitória',
                'estado': 'Espírito Santo',
                'endereco': 'Avenida Campo Grande, nº. 432, Campo Grande, Cariacica/ES',
                'quem_assina': 'Tabeliã'
            }

        return CartorioConfigResponse(
            success=True,
            config=config,
            user_id=user_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Config fetch error: {str(e)}")


@router.post("/cartorio/config", response_model=MessageResponse)
async def update_config(data: CartorioConfigRequest, request: Request):
    """Update cartório configuration for authenticated user"""
    try:
        user_id = require_auth(request)

        # Validate gender concordance
        is_valid, error_message = validate_gender_concordance(data.quem_assina)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid signatory: {error_message}")

        # Update configuration in database
        config_dict = data.dict()
        success = update_cartorio_config(config_dict, user_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update configuration in database")

        return MessageResponse(
            success=True,
            message=f"Configuration updated successfully for {user_id}",
            user_id=user_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Config update error: {str(e)}")


@router.get("/cartorio/test")
async def test_system(request: Request):
    """Test cartório system configuration"""
    try:
        user_id = require_auth(request)

        config = get_cartorio_config(user_id)
        if not config:
            config = {
                'distrito': 'Campo Grande / Jardim América',
                'municipio': 'Cariacica',
                'comarca': 'Vitória',
                'estado': 'Espírito Santo',
                'endereco': 'Avenida Campo Grande, nº. 432, Campo Grande, Cariacica/ES',
                'quem_assina': 'Tabeliã'
            }

        # Generate template data with gender concordance
        template_data = get_cartorio_template_data(config)

        return {
            "success": True,
            "config": config,
            "template_data": template_data,
            "message": "Cartório system working correctly"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")
