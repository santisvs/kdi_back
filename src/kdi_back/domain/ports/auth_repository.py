# -*- coding: utf-8 -*-
"""
Puerto (interfaz) para el repositorio de autenticación.

Define las operaciones que debe implementar cualquier repositorio de autenticación.
"""
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class AuthRepository(ABC):
    """
    Interfaz para el repositorio de autenticación.
    
    Define las operaciones que debe implementar cualquier repositorio de autenticación.
    """
    
    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por su email.
        
        Args:
            email: Email del usuario
            
        Returns:
            Diccionario con la información del usuario si existe, None si no
        """
        pass
    
    @abstractmethod
    def get_user_by_oauth(self, provider: str, oauth_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por su proveedor OAuth y ID de OAuth.
        
        Args:
            provider: Proveedor OAuth (google, instagram)
            oauth_id: ID del usuario en el proveedor OAuth
            
        Returns:
            Diccionario con la información del usuario si existe, None si no
        """
        pass
    
    @abstractmethod
    def create_user(self, email: str, username: str, password_hash: Optional[str] = None,
                   oauth_provider: Optional[str] = None, oauth_id: Optional[str] = None,
                   first_name: Optional[str] = None, last_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Crea un nuevo usuario en la base de datos.
        
        Args:
            email: Email del usuario (debe ser único)
            username: Nombre de usuario (debe ser único)
            password_hash: Hash de la contraseña (opcional si es OAuth)
            oauth_provider: Proveedor OAuth (google, instagram) si es registro OAuth
            oauth_id: ID del usuario en el proveedor OAuth
            first_name: Nombre del usuario
            last_name: Apellido del usuario
            
        Returns:
            Diccionario con la información del usuario creado
            
        Raises:
            ValueError: Si el email o username ya existen
        """
        pass
    
    @abstractmethod
    def update_user_password(self, user_id: int, password_hash: str) -> None:
        """
        Actualiza la contraseña de un usuario.
        
        Args:
            user_id: ID del usuario
            password_hash: Nuevo hash de la contraseña
        """
        pass
    
    @abstractmethod
    def set_password_reset_token(self, user_id: int, token: str, expires_at: str) -> None:
        """
        Establece un token de recuperación de contraseña para un usuario.
        
        Args:
            user_id: ID del usuario
            token: Token de recuperación
            expires_at: Fecha de expiración del token (formato ISO)
        """
        pass
    
    @abstractmethod
    def get_user_by_reset_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por su token de recuperación de contraseña.
        
        Args:
            token: Token de recuperación
            
        Returns:
            Diccionario con la información del usuario si el token es válido, None si no
        """
        pass
    
    @abstractmethod
    def clear_password_reset_token(self, user_id: int) -> None:
        """
        Limpia el token de recuperación de contraseña de un usuario.
        
        Args:
            user_id: ID del usuario
        """
        pass
    
    @abstractmethod
    def save_token(self, user_id: int, token: str, expires_at: str) -> None:
        """
        Guarda un token JWT en la base de datos.
        
        Args:
            user_id: ID del usuario
            token: Token JWT
            expires_at: Fecha de expiración del token (formato ISO)
        """
        pass
    
    @abstractmethod
    def get_token_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el usuario asociado a un token JWT válido.
        
        Args:
            token: Token JWT
            
        Returns:
            Diccionario con la información del usuario si el token es válido, None si no
        """
        pass
    
    @abstractmethod
    def revoke_token(self, token: str) -> None:
        """
        Revoca un token JWT.
        
        Args:
            token: Token JWT a revocar
        """
        pass
    
    @abstractmethod
    def revoke_all_user_tokens(self, user_id: int) -> None:
        """
        Revoca todos los tokens de un usuario.
        
        Args:
            user_id: ID del usuario
        """
        pass
    
    @abstractmethod
    def update_token_last_used(self, token: str) -> None:
        """
        Actualiza la fecha de último uso de un token.
        
        Args:
            token: Token JWT
        """
        pass

