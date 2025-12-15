# -*- coding: utf-8 -*-
"""Health and basic routes"""
from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)


@health_bp.route('/hola-mundo', methods=['GET'])
def hola_mundo():
    """
    Endpoint GET que responde 'adios mundo'
    """
    return jsonify({"mensaje": "adios mundo"}), 200


@health_bp.route('/health', methods=['GET'])
def health():
    """
    Endpoint de salud para verificar que el servicio está corriendo
    """
    return jsonify({"status": "ok"}), 200

