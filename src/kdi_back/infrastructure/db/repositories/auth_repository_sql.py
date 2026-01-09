# -*- coding: utf-8 -*-
"""
Implementación SQL del repositorio de autenticación usando PostgreSQL.
"""
from typing import Optional, Dict, Any
from kdi_back.domain.ports.auth_repository import AuthRepository
from kdi_back.infrastructure.db.database import Database
import psycopg2
from datetime import datetime


class AuthRepositorySQL(AuthRepository):
    """
    Implementación concreta del repositorio de autenticación usando SQL.
    """
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por su email.
        """
        try:
            with Database.get_cursor(commit=False) as (conn, cur):
                cur.execute("""
                    SELECT id, email, username, password_hash, oauth_provider, oauth_id,
                           first_name, last_name, phone, date_of_birth, created_at, updated_at
                    FROM "user"
                    WHERE email = %s;
                """, (email.lower().strip(),))
                
                result = cur.fetchone()
                if result:
                    return dict(result)
                return None
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al obtener el usuario: {e}")
    
    def get_user_by_oauth(self, provider: str, oauth_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por su proveedor OAuth y ID de OAuth.
        """
        try:
            with Database.get_cursor(commit=False) as (conn, cur):
                cur.execute("""
                    SELECT id, email, username, password_hash, oauth_provider, oauth_id,
                           first_name, last_name, phone, date_of_birth, created_at, updated_at
                    FROM "user"
                    WHERE oauth_provider = %s AND oauth_id = %s;
                """, (provider.lower(), oauth_id))
                
                result = cur.fetchone()
                if result:
                    return dict(result)
                return None
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al obtener el usuario: {e}")
    
    def create_user(self, email: str, username: str, password_hash: Optional[str] = None,
                   oauth_provider: Optional[str] = None, oauth_id: Optional[str] = None,
                   first_name: Optional[str] = None, last_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Crea un nuevo usuario en la base de datos.
        """
        try:
            with Database.get_cursor(commit=True) as (conn, cur):
                cur.execute("""
                    INSERT INTO "user" (email, username, password_hash, oauth_provider, oauth_id, first_name, last_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, email, username, password_hash, oauth_provider, oauth_id,
                              first_name, last_name, phone, date_of_birth, created_at, updated_at;
                """, (email.lower().strip(), username.strip(), password_hash, 
                      oauth_provider.lower() if oauth_provider else None,
                      oauth_id, first_name, last_name))
                
                result = cur.fetchone()
                return dict(result)
                
        except psycopg2.IntegrityError as e:
            if 'user_email_key' in str(e) or 'email' in str(e).lower():
                raise ValueError(f"Ya existe un usuario con el email: {email}")
            elif 'user_username_key' in str(e) or 'username' in str(e).lower():
                raise ValueError(f"Ya existe un usuario con el username: {username}")
            elif 'idx_user_oauth' in str(e) or 'oauth' in str(e).lower():
                raise ValueError(f"Ya existe un usuario con este proveedor OAuth y ID")
            else:
                raise ValueError(f"Error de integridad al crear el usuario: {e}")
        except psycopg2.Error as e:
            raise ValueError(f"Error al crear el usuario: {e}")
    
    def update_user_password(self, user_id: int, password_hash: str) -> None:
        """
        Actualiza la contraseña de un usuario.
        """
        try:
            with Database.get_cursor(commit=True) as (conn, cur):
                cur.execute("""
                    UPDATE "user"
                    SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (password_hash, user_id))
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al actualizar la contraseña: {e}")
    
    def set_password_reset_token(self, user_id: int, token: str, expires_at: str) -> None:
        """
        Establece un token de recuperación de contraseña para un usuario.
        """
        try:
            with Database.get_cursor(commit=True) as (conn, cur):
                cur.execute("""
                    UPDATE "user"
                    SET password_reset_token = %s, password_reset_expires = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (token, expires_at, user_id))
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al establecer el token de recuperación: {e}")
    
    def get_user_by_reset_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por su token de recuperación de contraseña.
        """
        try:
            with Database.get_cursor(commit=False) as (conn, cur):
                cur.execute("""
                    SELECT id, email, username, password_hash, oauth_provider, oauth_id,
                           first_name, last_name, phone, date_of_birth, created_at, updated_at,
                           password_reset_expires
                    FROM "user"
                    WHERE password_reset_token = %s 
                    AND password_reset_expires > CURRENT_TIMESTAMP;
                """, (token,))
                
                result = cur.fetchone()
                if result:
                    return dict(result)
                return None
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al obtener el usuario: {e}")
    
    def clear_password_reset_token(self, user_id: int) -> None:
        """
        Limpia el token de recuperación de contraseña de un usuario.
        """
        try:
            with Database.get_cursor(commit=True) as (conn, cur):
                cur.execute("""
                    UPDATE "user"
                    SET password_reset_token = NULL, password_reset_expires = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (user_id,))
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al limpiar el token de recuperación: {e}")
    
    def save_token(self, user_id: int, token: str, expires_at: str) -> None:
        """
        Guarda un token JWT en la base de datos.
        """
        try:
            with Database.get_cursor(commit=True) as (conn, cur):
                cur.execute("""
                    INSERT INTO auth_tokens (user_id, token, expires_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (token) DO UPDATE
                    SET expires_at = EXCLUDED.expires_at, is_revoked = FALSE;
                """, (user_id, token, expires_at))
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al guardar el token: {e}")
    
    def get_token_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el usuario asociado a un token JWT válido.
        """
        try:
            with Database.get_cursor(commit=False) as (conn, cur):
                cur.execute("""
                    SELECT u.id, u.email, u.username, u.password_hash, u.oauth_provider, u.oauth_id,
                           u.first_name, u.last_name, u.phone, u.date_of_birth, u.created_at, u.updated_at
                    FROM "user" u
                    INNER JOIN auth_tokens at ON u.id = at.user_id
                    WHERE at.token = %s
                    AND at.is_revoked = FALSE
                    AND at.expires_at > CURRENT_TIMESTAMP;
                """, (token,))
                
                result = cur.fetchone()
                if result:
                    # Actualizar último uso del token
                    cur.execute("""
                        UPDATE auth_tokens
                        SET last_used_at = CURRENT_TIMESTAMP
                        WHERE token = %s;
                    """, (token,))
                    conn.commit()
                    return dict(result)
                return None
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al obtener el usuario del token: {e}")
    
    def revoke_token(self, token: str) -> None:
        """
        Revoca un token JWT.
        """
        try:
            with Database.get_cursor(commit=True) as (conn, cur):
                cur.execute("""
                    UPDATE auth_tokens
                    SET is_revoked = TRUE
                    WHERE token = %s;
                """, (token,))
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al revocar el token: {e}")
    
    def revoke_all_user_tokens(self, user_id: int) -> None:
        """
        Revoca todos los tokens de un usuario.
        """
        try:
            with Database.get_cursor(commit=True) as (conn, cur):
                cur.execute("""
                    UPDATE auth_tokens
                    SET is_revoked = TRUE
                    WHERE user_id = %s;
                """, (user_id,))
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al revocar los tokens: {e}")
    
    def update_token_last_used(self, token: str) -> None:
        """
        Actualiza la fecha de último uso de un token.
        """
        try:
            with Database.get_cursor(commit=True) as (conn, cur):
                cur.execute("""
                    UPDATE auth_tokens
                    SET last_used_at = CURRENT_TIMESTAMP
                    WHERE token = %s;
                """, (token,))
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al actualizar el último uso del token: {e}")

