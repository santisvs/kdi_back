# -*- coding: utf-8 -*-
"""
Servicio de dominio para lógica de negocio relacionada con jugadores.

Contiene los casos de uso del dominio sin depender de implementaciones técnicas.
"""
from typing import Optional, Dict, Any
from kdi_back.domain.ports.player_repository import PlayerRepository
from kdi_back.domain.services.player_statistics_data import get_default_distances
import re
from datetime import datetime


class PlayerService:
    """
    Servicio de dominio para operaciones de jugadores.
    
    Contiene la lógica de negocio pura, sin dependencias técnicas.
    """
    
    def __init__(self, player_repository: PlayerRepository):
        """
        Inicializa el servicio con un repositorio.
        
        Args:
            player_repository: Implementación del repositorio de jugadores
        """
        self.player_repository = player_repository
    
    def create_user_with_profile(self, email: str, username: str,
                                 first_name: Optional[str] = None,
                                 last_name: Optional[str] = None,
                                 phone: Optional[str] = None,
                                 date_of_birth: Optional[str] = None,
                                 handicap: Optional[float] = None,
                                 gender: Optional[str] = None,
                                 preferred_hand: Optional[str] = None,
                                 years_playing: Optional[int] = None,
                                 skill_level: Optional[str] = None,
                                 notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Crea un usuario con su perfil de jugador inicial.
        
        Esta es la lógica de negocio: "crear un usuario con perfil de jugador".
        La implementación técnica (SQL) está en el repositorio.
        
        Args:
            email: Email del usuario (debe ser único)
            username: Nombre de usuario (debe ser único)
            first_name: Nombre del usuario
            last_name: Apellido del usuario
            phone: Teléfono de contacto
            date_of_birth: Fecha de nacimiento (formato YYYY-MM-DD)
            handicap: Handicap del jugador
            gender: Género del jugador (male, female)
            preferred_hand: Mano preferida (right, left, ambidextrous)
            years_playing: Años de experiencia jugando golf
            skill_level: Nivel de habilidad (beginner, intermediate, advanced, professional)
            notes: Notas adicionales
            
        Returns:
            Diccionario con la información del usuario y su perfil creados
            
        Raises:
            ValueError: Si los datos no son válidos o el usuario ya existe
        """
        # Validaciones de negocio
        self._validate_email(email)
        self._validate_username(username)
        
        if date_of_birth:
            self._validate_date_of_birth(date_of_birth)
        
        if handicap is not None:
            self._validate_handicap(handicap)
        
        if gender:
            self._validate_gender(gender)
        
        if preferred_hand:
            self._validate_preferred_hand(preferred_hand)
        
        if skill_level:
            self._validate_skill_level(skill_level)
        
        if years_playing is not None:
            self._validate_years_playing(years_playing)
        
        # Verificar que el usuario no exista
        existing_user = self.player_repository.get_user_by_email(email)
        if existing_user:
            raise ValueError(f"Ya existe un usuario con el email: {email}")
        
        existing_user = self.player_repository.get_user_by_username(username)
        if existing_user:
            raise ValueError(f"Ya existe un usuario con el username: {username}")
        
        # Crear el usuario
        user = self.player_repository.create_user(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            date_of_birth=date_of_birth
        )
        
        # Crear el perfil de jugador
        player_profile = self.player_repository.create_player_profile(
            user_id=user['id'],
            handicap=handicap,
            gender=gender,
            preferred_hand=preferred_hand,
            years_playing=years_playing,
            skill_level=skill_level,
            notes=notes
        )
        
        # Si se proporcionó gender y skill_level, inicializar estadísticas por palo
        if gender and skill_level:
            try:
                default_distances = get_default_distances(gender, skill_level)
                self.player_repository.initialize_club_statistics(
                    player_profile_id=player_profile['id'],
                    club_distances=default_distances
                )
            except Exception as e:
                # Si falla la inicialización de estadísticas, no fallar la creación del perfil
                # pero registrar el error
                print(f"Advertencia: No se pudieron inicializar las estadísticas por palo: {e}")
        
        return {
            "user": user,
            "player_profile": player_profile
        }
    
    def _validate_email(self, email: str):
        """
        Valida que el email tenga un formato válido.
        
        Args:
            email: Email a validar
            
        Raises:
            ValueError: Si el email no es válido
        """
        if not email or not isinstance(email, str):
            raise ValueError("El email es requerido y debe ser una cadena de texto")
        
        email = email.strip().lower()
        
        # Patrón básico de validación de email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValueError(f"El email '{email}' no tiene un formato válido")
    
    def _validate_username(self, username: str):
        """
        Valida que el username sea válido.
        
        Args:
            username: Username a validar
            
        Raises:
            ValueError: Si el username no es válido
        """
        if not username or not isinstance(username, str):
            raise ValueError("El username es requerido y debe ser una cadena de texto")
        
        username = username.strip()
        
        if len(username) < 3:
            raise ValueError("El username debe tener al menos 3 caracteres")
        
        if len(username) > 50:
            raise ValueError("El username no puede tener más de 50 caracteres")
        
        # Solo permitir letras, números, guiones y guiones bajos
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValueError("El username solo puede contener letras, números, guiones y guiones bajos")
    
    def _validate_date_of_birth(self, date_of_birth: str):
        """
        Valida que la fecha de nacimiento tenga un formato válido.
        
        Args:
            date_of_birth: Fecha de nacimiento en formato YYYY-MM-DD
            
        Raises:
            ValueError: Si la fecha no es válida
        """
        try:
            date_obj = datetime.strptime(date_of_birth, '%Y-%m-%d')
            # Verificar que no sea una fecha futura
            if date_obj.date() > datetime.now().date():
                raise ValueError("La fecha de nacimiento no puede ser una fecha futura")
            # Verificar que sea razonable (no más de 120 años)
            age = (datetime.now().date() - date_obj.date()).days / 365.25
            if age > 120:
                raise ValueError("La fecha de nacimiento no es válida")
        except ValueError as e:
            if "time data" in str(e) or "does not match format" in str(e):
                raise ValueError(f"La fecha de nacimiento debe estar en formato YYYY-MM-DD. Recibido: {date_of_birth}")
            raise
    
    def _validate_handicap(self, handicap: float):
        """
        Valida que el handicap sea un valor razonable.
        
        Args:
            handicap: Handicap a validar
            
        Raises:
            ValueError: Si el handicap no es válido
        """
        if not isinstance(handicap, (int, float)):
            raise ValueError("El handicap debe ser un número")
        
        if handicap < 0 or handicap > 54:
            raise ValueError("El handicap debe estar entre 0 y 54")
    
    def _validate_preferred_hand(self, preferred_hand: str):
        """
        Valida que la mano preferida sea un valor válido.
        
        Args:
            preferred_hand: Mano preferida a validar
            
        Raises:
            ValueError: Si la mano preferida no es válida
        """
        valid_hands = ['right', 'left', 'ambidextrous']
        if preferred_hand.lower() not in valid_hands:
            raise ValueError(f"La mano preferida debe ser una de: {', '.join(valid_hands)}")
    
    def _validate_skill_level(self, skill_level: str):
        """
        Valida que el nivel de habilidad sea un valor válido.
        
        Args:
            skill_level: Nivel de habilidad a validar
            
        Raises:
            ValueError: Si el nivel de habilidad no es válido
        """
        valid_levels = ['beginner', 'intermediate', 'advanced', 'professional']
        if skill_level.lower() not in valid_levels:
            raise ValueError(f"El nivel de habilidad debe ser uno de: {', '.join(valid_levels)}")
    
    def _validate_years_playing(self, years_playing: int):
        """
        Valida que los años jugando sean un valor razonable.
        
        Args:
            years_playing: Años jugando a validar
            
        Raises:
            ValueError: Si los años jugando no son válidos
        """
        if not isinstance(years_playing, int):
            raise ValueError("Los años jugando deben ser un número entero")
        
        if years_playing < 0:
            raise ValueError("Los años jugando no pueden ser negativos")
        
        if years_playing > 100:
            raise ValueError("Los años jugando no pueden ser más de 100")
    
    def _validate_gender(self, gender: str):
        """
        Valida que el género sea un valor válido.
        
        Args:
            gender: Género a validar
            
        Raises:
            ValueError: Si el género no es válido
        """
        valid_genders = ['male', 'female']
        if gender.lower() not in valid_genders:
            raise ValueError(f"El género debe ser uno de: {', '.join(valid_genders)}")

