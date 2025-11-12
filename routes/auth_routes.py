"""Authentication routes"""
from flask import Blueprint, request, jsonify, session
from auth import authenticate_user

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = authenticate_user(username, password)
        if user:
            session['user'] = user['username']
            session['authenticated'] = True
            session['user_data'] = user
            return jsonify({
                "success": True,
                "message": "Login successful",
                "user": {"username": username}
            })
        else:
            return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    session.pop('user', None)
    session.pop('authenticated', None)
    return jsonify({"success": True, "message": "Logout successful"})


@auth_bp.route('/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status"""
    authenticated = session.get('authenticated', False)
    user = session.get('user')

    if authenticated and user:
        return jsonify({
            "authenticated": True,
            "user": {"username": user}
        })
    else:
        return jsonify({"authenticated": False, "user": None})
