"""Cartório configuration routes"""
from flask import Blueprint, request, jsonify, session
from database import get_cartorio_config, update_cartorio_config
from gender_concordance import validate_gender_concordance, get_cartorio_template_data

cartorio_bp = Blueprint('cartorio', __name__)


@cartorio_bp.route('/cartorio/config', methods=['GET'])
def get_config():
    """Get cartório configuration for authenticated user"""
    try:
        if not session.get('authenticated'):
            return jsonify({"error": "Authentication required"}), 401

        user_id = session.get('user')
        if not user_id:
            return jsonify({"error": "User not found in session"}), 401

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

        return jsonify({
            "success": True,
            "config": config,
            "user_id": user_id
        })

    except Exception as e:
        return jsonify({"error": f"Config fetch error: {str(e)}"}), 500


@cartorio_bp.route('/cartorio/config', methods=['POST'])
def update_config():
    """Update cartório configuration for authenticated user"""
    try:
        if not session.get('authenticated'):
            return jsonify({"error": "Authentication required"}), 401

        user_id = session.get('user')
        if not user_id:
            return jsonify({"error": "User not found in session"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate required fields
        required_fields = ['distrito', 'municipio', 'comarca', 'estado', 'endereco', 'quem_assina']
        for field in required_fields:
            if not data.get(field) or not data[field].strip():
                return jsonify({"error": f"{field} é obrigatório"}), 400

        # Validate gender concordance
        is_valid, error_message = validate_gender_concordance(data['quem_assina'])
        if not is_valid:
            return jsonify({"error": f"Invalid signatory: {error_message}"}), 400

        # Update configuration in database
        success = update_cartorio_config(data, user_id)
        if not success:
            return jsonify({"error": "Failed to update configuration in database"}), 500

        return jsonify({
            "success": True,
            "message": f"Configuration updated successfully for {user_id}",
            "user_id": user_id
        })

    except Exception as e:
        return jsonify({"error": f"Config update error: {str(e)}"}), 500


@cartorio_bp.route('/cartorio/test', methods=['GET'])
def test_system():
    """Test cartório system configuration"""
    try:
        if not session.get('authenticated'):
            return jsonify({"error": "Authentication required"}), 401

        user_id = session.get('user')
        if not user_id:
            return jsonify({"error": "User not found in session"}), 401

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

        return jsonify({
            "success": True,
            "config": config,
            "template_data": template_data,
            "message": "Cartório system working correctly"
        })

    except Exception as e:
        return jsonify({"error": f"Test error: {str(e)}"}), 500
