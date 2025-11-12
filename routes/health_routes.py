"""Health check and session management routes"""
from flask import Blueprint, jsonify
from config import sessions

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Legal Document Processor",
        "version": "2.0.0",
        "framework": "Flask"
    })


@health_bp.route('/session/<session_id>', methods=['DELETE'])
def cancel_session(session_id):
    """Cancel and delete a session"""
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    del sessions[session_id]
    return jsonify({"message": "Session cancelled successfully"})
