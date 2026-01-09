# -*- coding: utf-8 -*-
"""
Servicio de dominio para lógica de negocio relacionada con autenticación.

Contiene los casos de uso del dominio sin depender de implementaciones técnicas.
"""
from typing import Optional, Dict, Any
from kdi_back.domain.ports.auth_repository import AuthRepository
from kdi_back.infrastructure.config import settings
import jwt
import bcrypt
import secrets
import re
from datetime import datetime, timedelta


class AuthService:
    """
    Servicio de dominio para operaciones de autenticación.
    
    Contiene la lógica de negocio pura, sin dependencias técnicas.
    """
    
    def __init__(self, auth_repository: AuthRepository):
        """
        Inicializa el servicio con un repositorio.
        
        Args:
            auth_repository: Implementación del repositorio de autenticación
        """
        self.auth_repository = auth_repository
    
    def register_user(self, email: str, username: str, password: str,
                      first_name: Optional[str] = None, last_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Registra un nuevo usuario con email y contraseña.
        
        Args:
            email: Email del usuario
            username: Nombre de usuario
            password: Contraseña en texto plano
            first_name: Nombre del usuario
            last_name: Apellido del usuario
            
        Returns:
            Diccionario con la información del usuario y el token JWT
            
        Raises:
            ValueError: Si los datos no son válidos o el usuario ya existe
        """
        # Validaciones
        self._validate_email(email)
        self._validate_username(username)
        self._validate_password(password)
        
        # Verificar que el usuario no exista
        existing_user = self.auth_repository.get_user_by_email(email)
        if existing_user:
            raise ValueError(f"Ya existe un usuario con el email: {email}")
        
        # Hash de la contraseña
        password_hash = self._hash_password(password)
        
        # Crear el usuario
        user = self.auth_repository.create_user(
            email=email,
            username=username,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name
        )
        
        # Generar token JWT
        token = self._generate_token(user['id'], user['email'])
        
        return {
            "user": {
                "id": user['id'],
                "email": user['email'],
                "username": user['username'],
                "first_name": user.get('first_name'),
                "last_name": user.get('last_name'),
            },
            "token": token
        }
    
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Autentica un usuario con email y contraseña.
        
        Args:
            email: Email del usuario
            password: Contraseña en texto plano
            
        Returns:
            Diccionario con la información del usuario y el token JWT
            
        Raises:
            ValueError: Si las credenciales son incorrectas
        """
        # Obtener usuario
        user = self.auth_repository.get_user_by_email(email)
        if not user:
            raise ValueError("Email o contraseña incorrectos")
        
        # Verificar que tenga contraseña (no es OAuth)
        if not user.get('password_hash'):
            raise ValueError("Este usuario se registró con OAuth. Usa el método de inicio de sesión correspondiente.")
        
        # Verificar contraseña
        if not self._verify_password(password, user['password_hash']):
            raise ValueError("Email o contraseña incorrectos")
        
        # Generar token JWT
        token = self._generate_token(user['id'], user['email'])
        
        return {
            "user": {
                "id": user['id'],
                "email": user['email'],
                "username": user['username'],
                "first_name": user.get('first_name'),
                "last_name": user.get('last_name'),
            },
            "token": token
        }
    
    def register_oauth_user(self, provider: str, oauth_id: str, email: str,
                           username: Optional[str] = None, first_name: Optional[str] = None,
                           last_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Registra o autentica un usuario mediante OAuth.
        
        Args:
            provider: Proveedor OAuth (google, instagram)
            oauth_id: ID del usuario en el proveedor OAuth
            email: Email del usuario
            username: Nombre de usuario (opcional, se genera si no se proporciona)
            first_name: Nombre del usuario
            last_name: Apellido del usuario
            
        Returns:
            Diccionario con la información del usuario y el token JWT
            
        Raises:
            ValueError: Si los datos no son válidos
        """
        # Validar proveedor
        if provider.lower() not in ['google', 'instagram']:
            raise ValueError(f"Proveedor OAuth no válido: {provider}")
        
        # Validar email
        self._validate_email(email)
        
        # Verificar si el usuario ya existe por OAuth
        user = self.auth_repository.get_user_by_oauth(provider.lower(), oauth_id)
        
        if not user:
            # Verificar si existe por email (puede ser que se registró con email/password)
            user = self.auth_repository.get_user_by_email(email)
            if user:
                # Actualizar con información OAuth
                raise ValueError("Ya existe un usuario con este email. Por favor, inicia sesión con tu contraseña.")
            
            # Generar username si no se proporciona
            if not username:
                username = self._generate_username_from_email(email)
            
            # Verificar que el username no exista
            existing_user = self.auth_repository.get_user_by_email(username)  # Reutilizamos para verificar username
            if existing_user and existing_user.get('username') == username:
                username = f"{username}_{secrets.token_hex(4)}"
            
            # Crear nuevo usuario
            user = self.auth_repository.create_user(
                email=email,
                username=username,
                password_hash=None,
                oauth_provider=provider.lower(),
                oauth_id=oauth_id,
                first_name=first_name,
                last_name=last_name
            )
        
        # Generar token JWT
        token = self._generate_token(user['id'], user['email'])
        
        return {
            "user": {
                "id": user['id'],
                "email": user['email'],
                "username": user['username'],
                "first_name": user.get('first_name'),
                "last_name": user.get('last_name'),
            },
            "token": token
        }
    
    def request_password_reset(self, email: str) -> str:
        """
        Solicita un reset de contraseña para un usuario.
        
        Args:
            email: Email del usuario
            
        Returns:
            Token de recuperación de contraseña
            
        Raises:
            ValueError: Si el usuario no existe
        """
        user = self.auth_repository.get_user_by_email(email)
        if not user:
            # Por seguridad, no revelamos si el usuario existe o no
            return "Si el email existe, se enviará un correo con instrucciones."
        
        # Generar token de recuperación
        reset_token = secrets.token_urlsafe(32)
        expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        
        # Guardar token
        self.auth_repository.set_password_reset_token(user['id'], reset_token, expires_at)
        
        # En producción, aquí se enviaría un email con el token
        # Por ahora, retornamos el token (en producción no debería hacerlo)
        return reset_token
    
    def reset_password(self, token: str, new_password: str) -> None:
        """
        Restablece la contraseña de un usuario usando un token de recuperación.
        
        Args:
            token: Token de recuperación de contraseña
            new_password: Nueva contraseña
            
        Raises:
            ValueError: Si el token es inválido o ha expirado
        """
        # Validar contraseña
        self._validate_password(new_password)
        
        # Obtener usuario por token
        user = self.auth_repository.get_user_by_reset_token(token)
        if not user:
            raise ValueError("Token de recuperación inválido o expirado")
        
        # Hash de la nueva contraseña
        password_hash = self._hash_password(new_password)
        
        # Actualizar contraseña
        self.auth_repository.update_user_password(user['id'], password_hash)
        
        # Limpiar token de recuperación
        self.auth_repository.clear_password_reset_token(user['id'])
        
        # Revocar todos los tokens existentes del usuario
        self.auth_repository.revoke_all_user_tokens(user['id'])
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verifica un token JWT y retorna el usuario asociado.
        
        Args:
            token: Token JWT
            
        Returns:
            Diccionario con la información del usuario si el token es válido, None si no
        """
        try:
            # Decodificar token
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get('user_id')
            
            if not user_id:
                return None
            
            # Verificar en la base de datos
            user = self.auth_repository.get_token_user(token)
            return user
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def _hash_password(self, password: str) -> str:
        """
        Genera el hash de una contraseña.
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Hash de la contraseña
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verifica una contraseña contra su hash.
        
        Args:
            password: Contraseña en texto plano
            password_hash: Hash de la contraseña
            
        Returns:
            True si la contraseña es correcta, False si no
        """
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _generate_token(self, user_id: int, email: str) -> str:
        """
        Genera un token JWT para un usuario.
        
        Args:
            user_id: ID del usuario
            email: Email del usuario
            
        Returns:
            Token JWT
        """
        expires_at = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': expires_at,
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        # Guardar token en la base de datos
        self.auth_repository.save_token(user_id, token, expires_at.isoformat())
        
        return token
    
    def _validate_email(self, email: str):
        """
        Valida que el email tenga un formato válido.
        """
        if not email or not isinstance(email, str):
            raise ValueError("El email es requerido y debe ser una cadena de texto")
        
        email = email.strip().lower()
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValueError(f"El email '{email}' no tiene un formato válido")
    
    def _validate_username(self, username: str):
        """
        Valida que el username sea válido.
        """
        if not username or not isinstance(username, str):
            raise ValueError("El username es requerido y debe ser una cadena de texto")
        
        username = username.strip()
        
        if len(username) < 3:
            raise ValueError("El username debe tener al menos 3 caracteres")
        
        if len(username) > 50:
            raise ValueError("El username no puede tener más de 50 caracteres")
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValueError("El username solo puede contener letras, números, guiones y guiones bajos")
    
    def _validate_password(self, password: str):
        """
        Valida que la contraseña sea válida.
        """
        if not password or not isinstance(password, str):
            raise ValueError("La contraseña es requerida")
        
        if len(password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        
        if len(password) > 128:
            raise ValueError("La contraseña no puede tener más de 128 caracteres")
    
    def logout_user(self, token: str) -> None:
        """
        Cierra sesión de un usuario revocando su token JWT.
        
        Args:
            token: Token JWT a revocar
            
        Raises:
            ValueError: Si el token es inválido
        """
        # Verificar que el token sea válido antes de revocarlo
        user = self.verify_token(token)
        if not user:
            raise ValueError("Token inválido o expirado")
        
        # Revocar el token
        self.auth_repository.revoke_token(token)
    
    def _generate_username_from_email(self, email: str) -> str:
        """
        Genera un username a partir de un email.
        """
        username = email.split('@')[0]
        # Limpiar caracteres no permitidos
        username = re.sub(r'[^a-zA-Z0-9_-]', '', username)
        # Asegurar longitud mínima
        if len(username) < 3:
            username = f"user_{username}"
        # Asegurar longitud máxima
        if len(username) > 50:
            username = username[:50]
        return username

