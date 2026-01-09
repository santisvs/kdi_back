# -*- coding: utf-8 -*-
"""
Dependencias de la API - Inicialización de servicios y repositorios.

Aquí se crean las instancias de servicios y repositorios que usa la API.
"""
from kdi_back.domain.services.golf_service import GolfService
from kdi_back.infrastructure.db.repositories.golf_repository_sql import GolfRepositorySQL
from kdi_back.domain.services.player_service import PlayerService
from kdi_back.infrastructure.db.repositories.player_repository_sql import PlayerRepositorySQL
from kdi_back.domain.services.match_service import MatchService
from kdi_back.infrastructure.db.repositories.match_repository_sql import MatchRepositorySQL
from kdi_back.infrastructure.db.repositories.golf_repository_sql import GolfRepositorySQL
from kdi_back.domain.services.auth_service import AuthService
from kdi_back.infrastructure.db.repositories.auth_repository_sql import AuthRepositorySQL
from kdi_back.domain.services.voice_service import VoiceService


def get_golf_service() -> GolfService:
    """
    Factory function para crear el servicio de golf con sus dependencias.
    
    Returns:
        Instancia de GolfService configurada con el repositorio SQL
    """
    golf_repository = GolfRepositorySQL()
    return GolfService(golf_repository)


def get_player_service() -> PlayerService:
    """
    Factory function para crear el servicio de jugadores con sus dependencias.
    
    Returns:
        Instancia de PlayerService configurada con el repositorio SQL
    """
    player_repository = PlayerRepositorySQL()
    return PlayerService(player_repository)


def get_match_service() -> MatchService:
    """
    Factory function para crear el servicio de partidos con sus dependencias.
    
    Returns:
        Instancia de MatchService configurada con el repositorio SQL y golf repository
    """
    match_repository = MatchRepositorySQL()
    golf_repository = GolfRepositorySQL()
    return MatchService(match_repository, golf_repository)


def get_auth_service() -> AuthService:
    """
    Factory function para crear el servicio de autenticación con sus dependencias.
    
    Returns:
        Instancia de AuthService configurada con el repositorio SQL
    """
    auth_repository = AuthRepositorySQL()
    return AuthService(auth_repository)


def get_voice_service() -> VoiceService:
    """
    Factory function para crear el servicio de voz con sus dependencias.
    
    Returns:
        Instancia de VoiceService configurada con los servicios necesarios
    """
    golf_service = get_golf_service()
    match_service = get_match_service()
    player_service = get_player_service()
    return VoiceService(golf_service, match_service, player_service)

