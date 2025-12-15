# -*- coding: utf-8 -*-
"""
Implementación SQL del repositorio de jugadores usando PostgreSQL.
"""
from typing import Optional, Dict, Any, List
from kdi_back.domain.ports.player_repository import PlayerRepository
from kdi_back.infrastructure.db.database import Database
import psycopg2


class PlayerRepositorySQL(PlayerRepository):
    """
    Implementación concreta del repositorio de jugadores usando SQL.
    """
    
    def create_user(self, email: str, username: str, first_name: Optional[str] = None,
                   last_name: Optional[str] = None, phone: Optional[str] = None,
                   date_of_birth: Optional[str] = None) -> Dict[str, Any]:
        """
        Crea un nuevo usuario en la base de datos.
        
        Args:
            email: Email del usuario (debe ser único)
            username: Nombre de usuario (debe ser único)
            first_name: Nombre del usuario
            last_name: Apellido del usuario
            phone: Teléfono de contacto
            date_of_birth: Fecha de nacimiento (formato YYYY-MM-DD)
            
        Returns:
            Diccionario con la información del usuario creado
            
        Raises:
            ValueError: Si el email o username ya existen
        """
        try:
            with Database.get_cursor(commit=True) as (conn, cur):
                cur.execute("""
                    INSERT INTO "user" (email, username, first_name, last_name, phone, date_of_birth)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, email, username, first_name, last_name, phone, date_of_birth, created_at, updated_at;
                """, (email.lower().strip(), username.strip(), first_name, last_name, phone, date_of_birth))
                
                result = cur.fetchone()
                return dict(result)
                
        except psycopg2.IntegrityError as e:
            if 'user_email_key' in str(e) or 'email' in str(e).lower():
                raise ValueError(f"Ya existe un usuario con el email: {email}")
            elif 'user_username_key' in str(e) or 'username' in str(e).lower():
                raise ValueError(f"Ya existe un usuario con el username: {username}")
            else:
                raise ValueError(f"Error de integridad al crear el usuario: {e}")
        except psycopg2.Error as e:
            raise ValueError(f"Error al crear el usuario: {e}")
    
    def create_player_profile(self, user_id: int, handicap: Optional[float] = None,
                            gender: Optional[str] = None,
                            preferred_hand: Optional[str] = None, years_playing: Optional[int] = None,
                            skill_level: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Crea un perfil de jugador asociado a un usuario.
        
        Args:
            user_id: ID del usuario al que pertenece el perfil
            handicap: Handicap del jugador
            gender: Género del jugador (male, female)
            preferred_hand: Mano preferida (right, left, ambidextrous)
            years_playing: Años de experiencia jugando golf
            skill_level: Nivel de habilidad (beginner, intermediate, advanced, professional)
            notes: Notas adicionales
            
        Returns:
            Diccionario con la información del perfil creado
            
        Raises:
            ValueError: Si el usuario no existe o ya tiene un perfil
        """
        try:
            # Verificar que el usuario existe
            user = self.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"No existe un usuario con el ID: {user_id}")
            
            # Normalizar gender, preferred_hand y skill_level si se proporcionan
            if gender:
                gender = gender.lower()
            
            if preferred_hand:
                preferred_hand = preferred_hand.lower()
            
            if skill_level:
                skill_level = skill_level.lower()
            
            with Database.get_cursor(commit=True) as (conn, cur):
                cur.execute("""
                    INSERT INTO player_profile (user_id, handicap, gender, preferred_hand, years_playing, skill_level, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, user_id, handicap, gender, preferred_hand, years_playing, skill_level, notes, created_at, updated_at;
                """, (user_id, handicap, gender, preferred_hand, years_playing, skill_level, notes))
                
                result = cur.fetchone()
                return dict(result)
                
        except psycopg2.IntegrityError as e:
            if 'player_profile_user_id_key' in str(e) or 'unique' in str(e).lower():
                raise ValueError(f"El usuario con ID {user_id} ya tiene un perfil de jugador")
            else:
                raise ValueError(f"Error de integridad al crear el perfil: {e}")
        except psycopg2.Error as e:
            raise ValueError(f"Error al crear el perfil de jugador: {e}")
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por su ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Diccionario con la información del usuario si existe, None si no
        """
        try:
            with Database.get_cursor(commit=False) as (conn, cur):
                cur.execute("""
                    SELECT id, email, username, first_name, last_name, phone, date_of_birth, created_at, updated_at
                    FROM "user"
                    WHERE id = %s;
                """, (user_id,))
                
                result = cur.fetchone()
                if result:
                    return dict(result)
                return None
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al obtener el usuario: {e}")
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por su email.
        
        Args:
            email: Email del usuario
            
        Returns:
            Diccionario con la información del usuario si existe, None si no
        """
        try:
            with Database.get_cursor(commit=False) as (conn, cur):
                cur.execute("""
                    SELECT id, email, username, first_name, last_name, phone, date_of_birth, created_at, updated_at
                    FROM "user"
                    WHERE email = %s;
                """, (email.lower().strip(),))
                
                result = cur.fetchone()
                if result:
                    return dict(result)
                return None
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al obtener el usuario: {e}")
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por su username.
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Diccionario con la información del usuario si existe, None si no
        """
        try:
            with Database.get_cursor(commit=False) as (conn, cur):
                cur.execute("""
                    SELECT id, email, username, first_name, last_name, phone, date_of_birth, created_at, updated_at
                    FROM "user"
                    WHERE username = %s;
                """, (username.strip(),))
                
                result = cur.fetchone()
                if result:
                    return dict(result)
                return None
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al obtener el usuario: {e}")
    
    def get_player_profile_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el perfil de jugador asociado a un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Diccionario con la información del perfil si existe, None si no
        """
        try:
            with Database.get_cursor(commit=False) as (conn, cur):
                cur.execute("""
                    SELECT id, user_id, handicap, gender, preferred_hand, years_playing, skill_level, notes, created_at, updated_at
                    FROM player_profile
                    WHERE user_id = %s;
                """, (user_id,))
                
                result = cur.fetchone()
                if result:
                    return dict(result)
                return None
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al obtener el perfil de jugador: {e}")
    
    def get_golf_club_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un palo de golf por su nombre.
        
        Args:
            name: Nombre del palo
            
        Returns:
            Diccionario con la información del palo si existe, None si no
        """
        try:
            with Database.get_cursor(commit=False) as (conn, cur):
                cur.execute("""
                    SELECT id, name, type, number, description, created_at
                    FROM golf_club
                    WHERE name = %s;
                """, (name,))
                
                result = cur.fetchone()
                if result:
                    return dict(result)
                return None
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al obtener el palo de golf: {e}")
    
    def initialize_club_statistics(self, player_profile_id: int, club_distances: Dict[str, float]) -> None:
        """
        Inicializa las estadísticas de distancia por palo para un jugador.
        
        Args:
            player_profile_id: ID del perfil de jugador
            club_distances: Diccionario con nombre de palo como clave y distancia en metros como valor
            
        Raises:
            ValueError: Si algún palo no existe en la base de datos
        """
        try:
            with Database.get_cursor(commit=True) as (conn, cur):
                # Para cada palo, crear una estadística inicial
                for club_name, distance in club_distances.items():
                    # Obtener el ID del palo
                    club = self.get_golf_club_by_name(club_name)
                    if not club:
                        raise ValueError(f"No se encontró el palo '{club_name}' en la base de datos")
                    
                    # Calcular un error inicial basado en el nivel (10% de la distancia para principiantes, 5% para profesionales)
                    # Usaremos un error promedio del 8% como valor por defecto
                    error_percentage = 0.08
                    average_error = distance * error_percentage
                    
                    # Insertar la estadística inicial
                    cur.execute("""
                        INSERT INTO player_club_statistics (
                            player_profile_id, 
                            golf_club_id, 
                            average_distance_meters,
                            min_distance_meters,
                            max_distance_meters,
                            average_error_meters,
                            error_std_deviation,
                            shots_recorded
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (player_profile_id, golf_club_id) DO NOTHING;
                    """, (
                        player_profile_id,
                        club['id'],
                        distance,
                        distance * 0.9,  # min_distance (90% de la distancia promedio)
                        distance * 1.1,  # max_distance (110% de la distancia promedio)
                        average_error,
                        average_error * 0.5,  # std_deviation (50% del error promedio)
                        0  # shots_recorded inicialmente 0
                    ))
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al inicializar estadísticas de palos: {e}")
    
    def get_player_club_statistics(self, player_profile_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todas las estadísticas de palos de un jugador.
        
        Args:
            player_profile_id: ID del perfil de jugador
            
        Returns:
            Lista de diccionarios con información de estadísticas por palo
        """
        try:
            with Database.get_cursor(commit=False) as (conn, cur):
                cur.execute("""
                    SELECT 
                        pcs.id,
                        pcs.player_profile_id,
                        pcs.golf_club_id,
                        pcs.average_distance_meters,
                        pcs.min_distance_meters,
                        pcs.max_distance_meters,
                        pcs.average_error_meters,
                        pcs.error_std_deviation,
                        pcs.shots_recorded,
                        gc.name AS club_name,
                        gc.type AS club_type,
                        gc.number AS club_number
                    FROM player_club_statistics pcs
                    INNER JOIN golf_club gc ON pcs.golf_club_id = gc.id
                    WHERE pcs.player_profile_id = %s
                    ORDER BY pcs.average_distance_meters DESC;
                """, (player_profile_id,))
                
                results = cur.fetchall()
                statistics = []
                for result in results:
                    statistics.append({
                        'id': result['id'],
                        'player_profile_id': result['player_profile_id'],
                        'golf_club_id': result['golf_club_id'],
                        'club_name': result['club_name'],
                        'club_type': result['club_type'],
                        'club_number': result['club_number'],
                        'average_distance_meters': float(result['average_distance_meters']) if result['average_distance_meters'] else None,
                        'min_distance_meters': float(result['min_distance_meters']) if result['min_distance_meters'] else None,
                        'max_distance_meters': float(result['max_distance_meters']) if result['max_distance_meters'] else None,
                        'average_error_meters': float(result['average_error_meters']) if result['average_error_meters'] else None,
                        'error_std_deviation': float(result['error_std_deviation']) if result['error_std_deviation'] else None,
                        'shots_recorded': result['shots_recorded']
                    })
                
                return statistics
                
        except psycopg2.Error as e:
            raise ValueError(f"Error al obtener estadísticas de palos: {e}")

