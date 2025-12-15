# -*- coding: utf-8 -*-
"""
Dependencias de la API - Inicialización de servicios y repositorios.

Aquí se crean las instancias de servicios y repositorios que usa la API.
"""
from kdi_back.domain.services.golf_service import GolfService
from kdi_back.infrastructure.db.repositories.golf_repository_sql import GolfRepositorySQL
from kdi_back.domain.services.player_service import PlayerService
from kdi_back.infrastructure.db.repositories.player_repository_sql import PlayerRepositorySQL


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

