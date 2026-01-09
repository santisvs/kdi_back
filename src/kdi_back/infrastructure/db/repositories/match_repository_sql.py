# -*- coding: utf-8 -*-
"""
Implementación SQL del repositorio de partidos.

Implementa las operaciones de base de datos para partidos usando PostgreSQL.
"""
from typing import Optional, Dict, Any, List
from kdi_back.domain.ports.match_repository import MatchRepository
from kdi_back.infrastructure.db.database import Database
from datetime import datetime


class MatchRepositorySQL(MatchRepository):
    """
    Implementación SQL del repositorio de partidos.
    """
    
    def create_match(self, course_id: int, name: Optional[str] = None) -> Dict[str, Any]:
        """Crea un nuevo partido en la base de datos."""
        # Verificar que el campo existe
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("SELECT id FROM golf_course WHERE id = %s;", (course_id,))
            if not cur.fetchone():
                raise ValueError(f"No existe un campo de golf con ID {course_id}")
        
        # Crear el partido
        with Database.get_cursor(commit=True) as (conn, cur):
            cur.execute("""
                INSERT INTO match (course_id, name, status, started_at)
                VALUES (%s, %s, 'in_progress', CURRENT_TIMESTAMP)
                RETURNING id, course_id, name, status, started_at, completed_at, created_at, updated_at;
            """, (course_id, name))
            
            result = cur.fetchone()
            return dict(result)
    
    def add_player_to_match(self, match_id: int, user_id: int, starting_hole_number: int = 1) -> Dict[str, Any]:
        """Añade un jugador a un partido."""
        # Verificar que el partido existe
        match = self.get_match_by_id(match_id)
        if not match:
            raise ValueError(f"No existe un partido con ID {match_id}")
        
        # Verificar que el usuario existe
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute('SELECT id FROM "user" WHERE id = %s;', (user_id,))
            if not cur.fetchone():
                raise ValueError(f"No existe un usuario con ID {user_id}")
        
        # Verificar que el jugador no esté ya en el partido
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT id FROM match_player 
                WHERE match_id = %s AND user_id = %s;
            """, (match_id, user_id))
            if cur.fetchone():
                raise ValueError(f"El jugador {user_id} ya está en el partido {match_id}")
        
        # Añadir el jugador al partido
        with Database.get_cursor(commit=True) as (conn, cur):
            # Verificar si la columna current_hole_number existe
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'match_player' 
                AND column_name = 'current_hole_number';
            """)
            has_current_hole = cur.fetchone() is not None
            
            if has_current_hole:
                cur.execute("""
                    INSERT INTO match_player (match_id, user_id, starting_hole_number, current_hole_number, total_strokes)
                    VALUES (%s, %s, %s, %s, 0)
                    RETURNING id, match_id, user_id, starting_hole_number, current_hole_number, total_strokes, created_at;
                """, (match_id, user_id, starting_hole_number, starting_hole_number))
            else:
                cur.execute("""
                    INSERT INTO match_player (match_id, user_id, starting_hole_number, total_strokes)
                    VALUES (%s, %s, %s, 0)
                    RETURNING id, match_id, user_id, starting_hole_number, total_strokes, created_at;
                """, (match_id, user_id, starting_hole_number))
            
            result = cur.fetchone()
            return dict(result)
    
    def get_match_by_id(self, match_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un partido por su ID."""
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT id, course_id, name, status, started_at, completed_at, created_at, updated_at
                FROM match
                WHERE id = %s;
            """, (match_id,))
            
            result = cur.fetchone()
            return dict(result) if result else None
    
    def get_match_players(self, match_id: int) -> List[Dict[str, Any]]:
        """Obtiene todos los jugadores de un partido."""
        with Database.get_cursor(commit=False) as (conn, cur):
            # Verificar si la columna current_hole_number existe
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'match_player' 
                AND column_name = 'current_hole_number';
            """)
            has_current_hole = cur.fetchone() is not None
            
            if has_current_hole:
                cur.execute("""
                    SELECT 
                        mp.id,
                        mp.match_id,
                        mp.user_id,
                        mp.starting_hole_number,
                        mp.current_hole_number,
                        mp.total_strokes,
                        mp.created_at,
                        u.username,
                        u.first_name,
                        u.last_name,
                        u.email
                    FROM match_player mp
                    JOIN "user" u ON mp.user_id = u.id
                    WHERE mp.match_id = %s
                    ORDER BY mp.id;
                """, (match_id,))
            else:
                cur.execute("""
                    SELECT 
                        mp.id,
                        mp.match_id,
                        mp.user_id,
                        mp.starting_hole_number,
                        mp.total_strokes,
                        mp.created_at,
                        u.username,
                        u.first_name,
                        u.last_name,
                        u.email
                    FROM match_player mp
                    JOIN "user" u ON mp.user_id = u.id
                    WHERE mp.match_id = %s
                    ORDER BY mp.id;
                """, (match_id,))
            
            results = cur.fetchall()
            return [dict(row) for row in results]
    
    def record_hole_score(self, match_id: int, user_id: int, hole_id: int, strokes: int) -> Dict[str, Any]:
        """
        Registra la puntuación de un jugador en un hoyo.
        
        Cuando se setea el total de golpes de un hoyo (en lugar de incrementar uno a uno),
        se eliminan todos los strokes pendientes de evaluación de ese hoyo, ya que el hoyo
        está finalizado y no se necesitan evaluar golpes individuales.
        """
        # Verificar que el jugador está en el partido
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT id FROM match_player 
                WHERE match_id = %s AND user_id = %s;
            """, (match_id, user_id))
            match_player = cur.fetchone()
            if not match_player:
                raise ValueError(f"El jugador {user_id} no está en el partido {match_id}")
            
            match_player_id = match_player['id']
        
        # Verificar que el hoyo existe
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("SELECT id FROM hole WHERE id = %s;", (hole_id,))
            if not cur.fetchone():
                raise ValueError(f"No existe un hoyo con ID {hole_id}")
        
        # Insertar o actualizar el score y eliminar strokes pendientes
        with Database.get_cursor(commit=True) as (conn, cur):
            # Insertar o actualizar el score
            cur.execute("""
                INSERT INTO match_hole_score (match_player_id, hole_id, strokes, completed_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (match_player_id, hole_id) 
                DO UPDATE SET strokes = EXCLUDED.strokes, completed_at = CURRENT_TIMESTAMP
                RETURNING id, match_player_id, hole_id, strokes, completed_at, created_at;
            """, (match_player_id, hole_id, strokes))
            
            result = cur.fetchone()
            
            # Eliminar todos los strokes pendientes de evaluación de este hoyo
            # Cuando se setea el total, el hoyo está finalizado y no se necesitan evaluar golpes individuales
            cur.execute("""
                DELETE FROM match_stroke
                WHERE match_player_id = %s 
                  AND hole_id = %s 
                  AND evaluated = FALSE;
            """, (match_player_id, hole_id))
            
            deleted_count = cur.rowcount
            if deleted_count > 0:
                print(f"✅ Eliminados {deleted_count} strokes pendientes del hoyo {hole_id} al setear el total de golpes")
            
            # Actualizar el total de golpes del jugador
            self._update_player_total_strokes(match_id, user_id)
            
            return dict(result)
    
    def increment_hole_strokes(self, match_id: int, user_id: int, hole_id: int, strokes: int = 1) -> Dict[str, Any]:
        """Incrementa el número de golpes de un jugador en un hoyo."""
        # Verificar que el jugador está en el partido
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT id FROM match_player 
                WHERE match_id = %s AND user_id = %s;
            """, (match_id, user_id))
            match_player = cur.fetchone()
            if not match_player:
                raise ValueError(f"El jugador {user_id} no está en el partido {match_id}")
            
            match_player_id = match_player['id']
        
        # Verificar que el hoyo existe
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("SELECT id FROM hole WHERE id = %s;", (hole_id,))
            if not cur.fetchone():
                raise ValueError(f"No existe un hoyo con ID {hole_id}")
        
        # Incrementar los golpes (o crear registro si no existe)
        with Database.get_cursor(commit=True) as (conn, cur):
            # Primero intentar actualizar si existe
            cur.execute("""
                UPDATE match_hole_score
                SET strokes = strokes + %s,
                    completed_at = CURRENT_TIMESTAMP
                WHERE match_player_id = %s AND hole_id = %s
                RETURNING id, match_player_id, hole_id, strokes, completed_at, created_at;
            """, (strokes, match_player_id, hole_id))
            
            result = cur.fetchone()
            
            # Si no existe registro, crear uno nuevo
            if not result:
                cur.execute("""
                    INSERT INTO match_hole_score (match_player_id, hole_id, strokes, completed_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    RETURNING id, match_player_id, hole_id, strokes, completed_at, created_at;
                """, (match_player_id, hole_id, strokes))
                result = cur.fetchone()
            
            # Actualizar el total de golpes del jugador
            self._update_player_total_strokes(match_id, user_id)
            
            return dict(result)
    
    def _update_player_total_strokes(self, match_id: int, user_id: int):
        """Actualiza el total de golpes de un jugador en un partido."""
        with Database.get_cursor(commit=True) as (conn, cur):
            cur.execute("""
                UPDATE match_player mp
                SET total_strokes = (
                    SELECT COALESCE(SUM(mhs.strokes), 0)
                    FROM match_hole_score mhs
                    WHERE mhs.match_player_id = mp.id
                )
                WHERE mp.match_id = %s AND mp.user_id = %s;
            """, (match_id, user_id))
    
    def get_player_scores(self, match_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Obtiene todas las puntuaciones de un jugador en un partido."""
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT 
                    mhs.id,
                    mhs.match_player_id,
                    mhs.hole_id,
                    mhs.strokes,
                    mhs.completed_at,
                    mhs.created_at,
                    h.hole_number,
                    h.par,
                    h.length
                FROM match_hole_score mhs
                JOIN match_player mp ON mhs.match_player_id = mp.id
                JOIN hole h ON mhs.hole_id = h.id
                WHERE mp.match_id = %s AND mp.user_id = %s
                ORDER BY h.hole_number;
            """, (match_id, user_id))
            
            results = cur.fetchall()
            return [dict(row) for row in results]
    
    def get_hole_strokes_for_player(self, match_id: int, user_id: int, hole_id: int) -> int:
        """Obtiene el número de golpes de un jugador en un hoyo específico."""
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT COALESCE(mhs.strokes, 0) as strokes
                FROM match_player mp
                LEFT JOIN match_hole_score mhs ON mhs.match_player_id = mp.id AND mhs.hole_id = %s
                WHERE mp.match_id = %s AND mp.user_id = %s;
            """, (hole_id, match_id, user_id))
            
            result = cur.fetchone()
            return int(result['strokes']) if result else 0
    
    def get_player_ranking(self, match_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene el ranking de un jugador en un partido."""
        leaderboard = self.get_match_leaderboard(match_id)
        
        for index, player in enumerate(leaderboard, start=1):
            if player['user_id'] == user_id:
                return {
                    "position": index,
                    "total_strokes": player['total_strokes'],
                    "holes_completed": player.get('holes_completed', 0),
                    "user_id": player['user_id'],
                    "username": player.get('username'),
                    "first_name": player.get('first_name'),
                    "last_name": player.get('last_name')
                }
        
        return None
    
    def calculate_player_total_strokes(self, match_id: int, user_id: int) -> int:
        """Calcula el total de golpes de un jugador en un partido."""
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT COALESCE(SUM(mhs.strokes), 0) as total
                FROM match_hole_score mhs
                JOIN match_player mp ON mhs.match_player_id = mp.id
                WHERE mp.match_id = %s AND mp.user_id = %s;
            """, (match_id, user_id))
            
            result = cur.fetchone()
            return int(result['total']) if result else 0
    
    def get_match_leaderboard(self, match_id: int) -> List[Dict[str, Any]]:
        """Obtiene el ranking de jugadores de un partido ordenado por total de golpes."""
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT 
                    mp.id,
                    mp.match_id,
                    mp.user_id,
                    mp.starting_hole_number,
                    mp.total_strokes,
                    u.username,
                    u.first_name,
                    u.last_name,
                    u.email,
                    COUNT(mhs.id) as holes_completed
                FROM match_player mp
                JOIN "user" u ON mp.user_id = u.id
                LEFT JOIN match_hole_score mhs ON mhs.match_player_id = mp.id
                WHERE mp.match_id = %s
                GROUP BY mp.id, mp.match_id, mp.user_id, mp.starting_hole_number, 
                         mp.total_strokes, u.username, u.first_name, u.last_name, u.email
                ORDER BY mp.total_strokes ASC, mp.id ASC;
            """, (match_id,))
            
            results = cur.fetchall()
            return [dict(row) for row in results]
    
    def complete_match(self, match_id: int) -> Dict[str, Any]:
        """Marca un partido como completado y calcula los totales de golpes."""
        # Verificar que el partido existe y no está completado
        match = self.get_match_by_id(match_id)
        if not match:
            raise ValueError(f"No existe un partido con ID {match_id}")
        
        if match['status'] == 'completed':
            raise ValueError(f"El partido {match_id} ya está completado")
        
        # Actualizar totales de golpes de todos los jugadores
        players = self.get_match_players(match_id)
        for player in players:
            self._update_player_total_strokes(match_id, player['user_id'])
        
        # Marcar el partido como completado
        with Database.get_cursor(commit=True) as (conn, cur):
            cur.execute("""
                UPDATE match
                SET status = 'completed',
                    completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, course_id, name, status, started_at, completed_at, created_at, updated_at;
            """, (match_id,))
            
            result = cur.fetchone()
            return dict(result)
    
    def get_matches_by_course(self, course_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene todos los partidos de un campo de golf."""
        with Database.get_cursor(commit=False) as (conn, cur):
            if status:
                cur.execute("""
                    SELECT id, course_id, name, status, started_at, completed_at, created_at, updated_at
                    FROM match
                    WHERE course_id = %s AND status = %s
                    ORDER BY started_at DESC;
                """, (course_id, status))
            else:
                cur.execute("""
                    SELECT id, course_id, name, status, started_at, completed_at, created_at, updated_at
                    FROM match
                    WHERE course_id = %s
                    ORDER BY started_at DESC;
                """, (course_id,))
            
            results = cur.fetchall()
            return [dict(row) for row in results]
    
    def get_matches_by_player(self, user_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene todos los partidos de un jugador."""
        with Database.get_cursor(commit=False) as (conn, cur):
            if status:
                cur.execute("""
                    SELECT DISTINCT
                        m.id,
                        m.course_id,
                        m.name,
                        m.status,
                        m.started_at,
                        m.completed_at,
                        m.created_at,
                        m.updated_at
                    FROM match m
                    JOIN match_player mp ON m.id = mp.match_id
                    WHERE mp.user_id = %s AND m.status = %s
                    ORDER BY m.started_at DESC;
                """, (user_id, status))
            else:
                cur.execute("""
                    SELECT DISTINCT
                        m.id,
                        m.course_id,
                        m.name,
                        m.status,
                        m.started_at,
                        m.completed_at,
                        m.created_at,
                        m.updated_at
                    FROM match m
                    JOIN match_player mp ON m.id = mp.match_id
                    WHERE mp.user_id = %s
                    ORDER BY m.started_at DESC;
                """, (user_id,))
            
            results = cur.fetchall()
            return [dict(row) for row in results]
    
    def create_stroke(self, match_id: int, user_id: int, hole_id: int, stroke_number: int,
                     ball_start_latitude: float, ball_start_longitude: float,
                     club_used_id: Optional[int] = None, trajectory_type: Optional[str] = None,
                     proposed_distance_meters: Optional[float] = None,
                     proposed_club_id: Optional[int] = None) -> Dict[str, Any]:
        """Crea un registro de golpe individual para evaluación posterior."""
        from typing import Optional
        
        # Verificar que el jugador está en el partido
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT id FROM match_player 
                WHERE match_id = %s AND user_id = %s;
            """, (match_id, user_id))
            match_player = cur.fetchone()
            if not match_player:
                raise ValueError(f"El jugador {user_id} no está en el partido {match_id}")
            
            match_player_id = match_player['id']
        
        # Validar trajectory_type si se proporciona
        if trajectory_type and trajectory_type not in ('conservadora', 'riesgo', 'optima'):
            raise ValueError(f"trajectory_type debe ser 'conservadora', 'riesgo' o 'optima', recibido: {trajectory_type}")
        
        # Crear el golpe
        with Database.get_cursor(commit=True) as (conn, cur):
            cur.execute("""
                INSERT INTO match_stroke (
                    match_player_id, hole_id, stroke_number,
                    ball_start_latitude, ball_start_longitude,
                    club_used_id, trajectory_type,
                    proposed_distance_meters, proposed_club_id,
                    evaluated
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
                RETURNING id, match_player_id, hole_id, stroke_number,
                    ball_start_latitude, ball_start_longitude,
                    club_used_id, trajectory_type,
                    proposed_distance_meters, proposed_club_id,
                    evaluated, evaluation_quality, evaluation_distance_error,
                    evaluation_direction_error, ball_end_latitude, ball_end_longitude,
                    ball_end_distance_meters, created_at, evaluated_at;
            """, (
                match_player_id, hole_id, stroke_number,
                ball_start_latitude, ball_start_longitude,
                club_used_id, trajectory_type,
                proposed_distance_meters, proposed_club_id
            ))
            
            result = cur.fetchone()
            return dict(result)
    
    def get_last_unevaluated_stroke(self, match_id: int, user_id: int, hole_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene el último golpe no evaluado de un jugador en un hoyo."""
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT 
                    ms.id, ms.match_player_id, ms.hole_id, ms.stroke_number,
                    ms.ball_start_latitude, ms.ball_start_longitude,
                    ms.club_used_id, ms.trajectory_type,
                    ms.proposed_distance_meters, ms.proposed_club_id,
                    ms.evaluated, ms.evaluation_quality, ms.evaluation_distance_error,
                    ms.evaluation_direction_error, ms.ball_end_latitude, ms.ball_end_longitude,
                    ms.ball_end_distance_meters, ms.created_at, ms.evaluated_at
                FROM match_stroke ms
                JOIN match_player mp ON ms.match_player_id = mp.id
                WHERE mp.match_id = %s AND mp.user_id = %s 
                    AND ms.hole_id = %s AND ms.evaluated = FALSE
                ORDER BY ms.created_at DESC
                LIMIT 1;
            """, (match_id, user_id, hole_id))
            
            result = cur.fetchone()
            return dict(result) if result else None
    
    def evaluate_stroke(self, stroke_id: int, ball_end_latitude: float, ball_end_longitude: float,
                      ball_end_distance_meters: float, evaluation_quality: Optional[float],
                      evaluation_distance_error: float, evaluation_direction_error: float) -> Dict[str, Any]:
        """Evalúa un golpe con la posición final de la bola."""
        with Database.get_cursor(commit=True) as (conn, cur):
            cur.execute("""
                UPDATE match_stroke
                SET evaluated = TRUE,
                    ball_end_latitude = %s,
                    ball_end_longitude = %s,
                    ball_end_distance_meters = %s,
                    evaluation_quality = %s,
                    evaluation_distance_error = %s,
                    evaluation_direction_error = %s,
                    evaluated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, match_player_id, hole_id, stroke_number,
                    ball_start_latitude, ball_start_longitude,
                    club_used_id, trajectory_type,
                    proposed_distance_meters, proposed_club_id,
                    evaluated, evaluation_quality, evaluation_distance_error,
                    evaluation_direction_error, ball_end_latitude, ball_end_longitude,
                    ball_end_distance_meters, created_at, evaluated_at;
            """, (
                ball_end_latitude, ball_end_longitude, ball_end_distance_meters,
                evaluation_quality, evaluation_distance_error, evaluation_direction_error,
                stroke_id
            ))
            
            result = cur.fetchone()
            if not result:
                raise ValueError(f"No existe un golpe con ID {stroke_id}")
            
            return dict(result)
    
    def get_last_stroke_in_hole(self, match_id: int, user_id: int, hole_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el último golpe (evaluado o no) de un jugador en un hoyo.
        Útil para evaluar el golpe que metió la bola en el hoyo.
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT 
                    ms.id, ms.match_player_id, ms.hole_id, ms.stroke_number,
                    ms.ball_start_latitude, ms.ball_start_longitude,
                    ms.club_used_id, ms.trajectory_type,
                    ms.proposed_distance_meters, ms.proposed_club_id,
                    ms.evaluated, ms.evaluation_quality, ms.evaluation_distance_error,
                    ms.evaluation_direction_error, ms.ball_end_latitude, ms.ball_end_longitude,
                    ms.ball_end_distance_meters, ms.created_at, ms.evaluated_at
                FROM match_stroke ms
                JOIN match_player mp ON ms.match_player_id = mp.id
                WHERE mp.match_id = %s AND mp.user_id = %s 
                    AND ms.hole_id = %s
                ORDER BY ms.created_at DESC
                LIMIT 1;
            """, (match_id, user_id, hole_id))
            
            result = cur.fetchone()
            return dict(result) if result else None
    
    def get_all_strokes_in_hole(self, match_id: int, user_id: int, hole_id: int) -> List[Dict[str, Any]]:
        """Obtiene todos los golpes de un jugador en un hoyo, ordenados por fecha de creación."""
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT 
                    ms.id, ms.match_player_id, ms.hole_id, ms.stroke_number,
                    ms.ball_start_latitude, ms.ball_start_longitude,
                    ms.club_used_id, ms.trajectory_type,
                    ms.proposed_distance_meters, ms.proposed_club_id,
                    ms.evaluated, ms.evaluation_quality, ms.evaluation_distance_error,
                    ms.evaluation_direction_error, ms.ball_end_latitude, ms.ball_end_longitude,
                    ms.ball_end_distance_meters, ms.created_at, ms.evaluated_at
                FROM match_stroke ms
                JOIN match_player mp ON ms.match_player_id = mp.id
                WHERE mp.match_id = %s AND mp.user_id = %s 
                    AND ms.hole_id = %s
                ORDER BY ms.created_at ASC;
            """, (match_id, user_id, hole_id))
            
            results = cur.fetchall()
            return [dict(row) for row in results]
    
    def get_match_state(self, match_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado actual del partido para un jugador.
        
        Incluye:
        - course_id: ID del campo
        - current_hole_number: Hoyo actual en el que está jugando
        - strokes_in_current_hole: Número de golpes en el hoyo actual
        - completed_holes: Lista de hoyos completados con sus puntuaciones
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            
        Returns:
            Diccionario con el estado del partido o None si no existe
        """
        with Database.get_cursor(commit=False) as (conn, cur):
            # Verificar si la columna current_hole_number existe
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'match_player' 
                AND column_name = 'current_hole_number';
            """)
            has_current_hole = cur.fetchone() is not None
            
            # Obtener información del partido y jugador
            if has_current_hole:
                cur.execute("""
                    SELECT 
                        m.course_id,
                        mp.starting_hole_number,
                        mp.current_hole_number,
                        mp.total_strokes
                    FROM match_player mp
                    JOIN match m ON mp.match_id = m.id
                    WHERE mp.match_id = %s AND mp.user_id = %s;
                """, (match_id, user_id))
            else:
                # Fallback: calcular current_hole_number desde starting_hole_number y hoyos completados
                cur.execute("""
                    SELECT 
                        m.course_id,
                        mp.starting_hole_number,
                        mp.total_strokes,
                        COALESCE(MAX(h.hole_number), 0) as last_completed_hole_number
                    FROM match_player mp
                    JOIN match m ON mp.match_id = m.id
                    LEFT JOIN match_hole_score mhs ON mhs.match_player_id = mp.id
                    LEFT JOIN hole h ON mhs.hole_id = h.id
                    WHERE mp.match_id = %s AND mp.user_id = %s
                    GROUP BY mp.id, m.course_id, mp.starting_hole_number, mp.total_strokes;
                """, (match_id, user_id))
            
            result = cur.fetchone()
            if not result:
                return None
            
            match_data = dict(result)
            course_id = match_data['course_id']
            
            # Determinar current_hole_number
            if has_current_hole:
                current_hole_number = match_data['current_hole_number']
            else:
                # Calcular desde starting_hole_number y hoyos completados
                starting_hole = match_data['starting_hole_number']
                # Obtener número de hoyos completados
                cur.execute("""
                    SELECT COUNT(*) as completed_count
                    FROM match_hole_score mhs
                    JOIN match_player mp ON mhs.match_player_id = mp.id
                    WHERE mp.match_id = %s AND mp.user_id = %s;
                """, (match_id, user_id))
                completed_count = cur.fetchone()['completed_count'] or 0
                current_hole_number = starting_hole + completed_count
            
            # Obtener hole_id del hoyo actual
            cur.execute("""
                SELECT id, hole_number
                FROM hole
                WHERE course_id = %s AND hole_number = %s;
            """, (course_id, current_hole_number))
            current_hole = cur.fetchone()
            current_hole_id = current_hole['id'] if current_hole else None
            
            # Obtener golpes en el hoyo actual
            strokes_in_current_hole = 0
            if current_hole_id:
                strokes_in_current_hole = self.get_hole_strokes_for_player(match_id, user_id, current_hole_id)
            
            # Obtener hoyos completados
            cur.execute("""
                SELECT 
                    h.id as hole_id,
                    h.hole_number,
                    h.par,
                    mhs.strokes,
                    mhs.completed_at
                FROM match_hole_score mhs
                JOIN match_player mp ON mhs.match_player_id = mp.id
                JOIN hole h ON mhs.hole_id = h.id
                WHERE mp.match_id = %s AND mp.user_id = %s
                ORDER BY h.hole_number ASC;
            """, (match_id, user_id))
            
            completed_holes = [dict(row) for row in cur.fetchall()]
            
            return {
                'course_id': course_id,
                'current_hole_number': current_hole_number,
                'current_hole_id': current_hole_id,
                'strokes_in_current_hole': strokes_in_current_hole,
                'completed_holes': completed_holes,
                'total_strokes': match_data['total_strokes']
            }
    
    def update_current_hole(self, match_id: int, user_id: int, hole_number: int) -> bool:
        """
        Actualiza el hoyo actual en el que está jugando un jugador.
        
        Args:
            match_id: ID del partido
            user_id: ID del usuario/jugador
            hole_number: Número del hoyo actual
            
        Returns:
            True si se actualizó correctamente, False si no
        """
        with Database.get_cursor(commit=True) as (conn, cur):
            # Verificar si la columna existe
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'match_player' 
                AND column_name = 'current_hole_number';
            """)
            if not cur.fetchone():
                return False  # La columna no existe, no se puede actualizar
            
            # Actualizar el hoyo actual
            cur.execute("""
                UPDATE match_player
                SET current_hole_number = %s
                WHERE match_id = %s AND user_id = %s;
            """, (hole_number, match_id, user_id))
            
            return cur.rowcount > 0

