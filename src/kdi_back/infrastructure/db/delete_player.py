# -*- coding: utf-8 -*-
"""
Script para eliminar toda la información de un jugador.

Este script elimina:
- Estadísticas de palos (player_club_statistics)
- Perfil de jugador (player_profile)
- Usuario (user)

Las eliminaciones se realizan en cascada gracias a las claves foráneas con ON DELETE CASCADE.
"""
try:
    from .database import Database, init_database
    from .repositories.player_repository_sql import PlayerRepositorySQL
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from kdi_back.infrastructure.db.database import Database, init_database
    from kdi_back.infrastructure.db.repositories.player_repository_sql import PlayerRepositorySQL
import psycopg2


def delete_player_by_id(player_repository: PlayerRepositorySQL, user_id: int) -> bool:
    """
    Elimina toda la información de un jugador por su ID de usuario.
    
    Args:
        player_repository: Instancia del repositorio de jugadores
        user_id: ID del usuario a eliminar
        
    Returns:
        bool: True si la eliminación fue exitosa, False en caso contrario
    """
    try:
        # Verificar que el usuario existe
        user = player_repository.get_user_by_id(user_id)
        if not user:
            print(f"✗ No se encontró un usuario con ID: {user_id}")
            return False
        
        print(f"\nUsuario encontrado:")
        print(f"  - ID: {user['id']}")
        print(f"  - Email: {user['email']}")
        print(f"  - Username: {user['username']}")
        print(f"  - Nombre: {user.get('first_name', '')} {user.get('last_name', '')}")
        
        # Obtener información del perfil si existe
        profile = player_repository.get_player_profile_by_user_id(user_id)
        if profile:
            print(f"\nPerfil de jugador encontrado:")
            print(f"  - ID: {profile['id']}")
            print(f"  - Handicap: {profile.get('handicap', 'N/A')}")
            print(f"  - Nivel: {profile.get('skill_level', 'N/A')}")
            
            # Contar estadísticas de palos
            with Database.get_cursor(commit=False) as (conn, cur):
                cur.execute("""
                    SELECT COUNT(*) as count
                    FROM player_club_statistics
                    WHERE player_profile_id = %s;
                """, (profile['id'],))
                stats_count = cur.fetchone()['count']
                print(f"  - Estadísticas de palos: {stats_count}")
        
        # Eliminar el usuario (esto eliminará en cascada el perfil y las estadísticas)
        with Database.get_cursor(commit=True) as (conn, cur):
            print(f"\n→ Eliminando usuario y toda su información relacionada...")
            cur.execute("DELETE FROM \"user\" WHERE id = %s;", (user_id,))
            
            if cur.rowcount == 0:
                print("✗ No se pudo eliminar el usuario")
                return False
            
            print(f"✓ Usuario eliminado exitosamente")
            print(f"  - Filas afectadas: {cur.rowcount}")
            
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error de PostgreSQL: {e}")
        print(f"  Código de error: {e.pgcode}")
        print(f"  Mensaje: {e.pgerror}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False


def delete_player_by_email(player_repository: PlayerRepositorySQL, email: str) -> bool:
    """
    Elimina toda la información de un jugador por su email.
    
    Args:
        player_repository: Instancia del repositorio de jugadores
        email: Email del usuario a eliminar
        
    Returns:
        bool: True si la eliminación fue exitosa, False en caso contrario
    """
    user = player_repository.get_user_by_email(email)
    if not user:
        print(f"✗ No se encontró un usuario con email: {email}")
        return False
    
    return delete_player_by_id(player_repository, user['id'])


def delete_player_by_username(player_repository: PlayerRepositorySQL, username: str) -> bool:
    """
    Elimina toda la información de un jugador por su username.
    
    Args:
        player_repository: Instancia del repositorio de jugadores
        username: Username del usuario a eliminar
        
    Returns:
        bool: True si la eliminación fue exitosa, False en caso contrario
    """
    user = player_repository.get_user_by_username(username)
    if not user:
        print(f"✗ No se encontró un usuario con username: {username}")
        return False
    
    return delete_player_by_id(player_repository, user['id'])


def list_all_players(player_repository: PlayerRepositorySQL) -> None:
    """
    Lista todos los jugadores en el sistema.
    
    Args:
        player_repository: Instancia del repositorio de jugadores
    """
    try:
        with Database.get_cursor(commit=False) as (conn, cur):
            cur.execute("""
                SELECT 
                    u.id,
                    u.email,
                    u.username,
                    u.first_name,
                    u.last_name,
                    pp.skill_level,
                    pp.gender
                FROM "user" u
                LEFT JOIN player_profile pp ON u.id = pp.user_id
                ORDER BY u.id;
            """)
            
            players = cur.fetchall()
            
            if not players:
                print("No hay jugadores registrados en el sistema.")
                return
            
            print(f"\n{'='*80}")
            print(f"Lista de jugadores ({len(players)} total)")
            print(f"{'='*80}")
            print(f"{'ID':<5} {'Email':<30} {'Username':<20} {'Nombre':<25} {'Nivel':<15} {'Género':<10}")
            print(f"{'-'*80}")
            
            for player in players:
                name = f"{player.get('first_name', '')} {player.get('last_name', '')}".strip()
                if not name:
                    name = "N/A"
                
                print(f"{player['id']:<5} {player['email']:<30} {player['username']:<20} {name:<25} {player.get('skill_level', 'N/A'):<15} {player.get('gender', 'N/A'):<10}")
            
            print(f"{'='*80}\n")
            
    except psycopg2.Error as e:
        print(f"✗ Error al listar jugadores: {e}")
    except Exception as e:
        print(f"✗ Error inesperado: {e}")


if __name__ == '__main__':
    """
    Script para eliminar toda la información de un jugador.
    
    Uso:
        python delete_player.py --id <user_id>
        python delete_player.py --email <email>
        python delete_player.py --username <username>
        python delete_player.py --list
    """
    import sys
    import argparse
    
    print("=" * 60)
    print("Script de Eliminación de Jugador")
    print("=" * 60)
    
    # Inicializar conexión a la base de datos
    if not init_database(install_postgis_if_missing=False):
        print("\n✗ No se pudo inicializar la base de datos correctamente")
        sys.exit(1)
    
    # Crear parser de argumentos
    parser = argparse.ArgumentParser(
        description='Elimina toda la información de un jugador del sistema',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python delete_player.py --id 1
  python delete_player.py --email jugador@example.com
  python delete_player.py --username jugador123
  python delete_player.py --list
        """
    )
    
    parser.add_argument('--id', type=int, help='ID del usuario a eliminar')
    parser.add_argument('--email', type=str, help='Email del usuario a eliminar')
    parser.add_argument('--username', type=str, help='Username del usuario a eliminar')
    parser.add_argument('--list', action='store_true', help='Lista todos los jugadores')
    parser.add_argument('--force', action='store_true', help='Elimina sin pedir confirmación')
    
    args = parser.parse_args()
    
    # Crear instancia del repositorio
    player_repository = PlayerRepositorySQL()
    
    # Si se solicita listar jugadores
    if args.list:
        list_all_players(player_repository)
        sys.exit(0)
    
    # Verificar que se proporcionó un método de identificación
    if not args.id and not args.email and not args.username:
        parser.print_help()
        print("\n✗ Debes proporcionar --id, --email, --username o --list")
        sys.exit(1)
    
    # Verificar que solo se proporcionó un método
    methods = sum([bool(args.id), bool(args.email), bool(args.username)])
    if methods > 1:
        print("✗ Solo puedes proporcionar un método de identificación (--id, --email o --username)")
        sys.exit(1)
    
    # Solicitar confirmación si no se usa --force
    if not args.force:
        print("\n⚠ ADVERTENCIA: Esta acción eliminará permanentemente:")
        print("  - El usuario")
        print("  - El perfil de jugador")
        print("  - Todas las estadísticas de palos")
        print("\nEsta acción NO se puede deshacer.\n")
        
        confirm = input("¿Estás seguro de que quieres continuar? (escribe 'SI' para confirmar): ")
        if confirm.upper() != 'SI':
            print("Operación cancelada.")
            sys.exit(0)
    
    # Eliminar según el método proporcionado
    success = False
    if args.id:
        print(f"\n→ Eliminando jugador con ID: {args.id}")
        success = delete_player_by_id(player_repository, args.id)
    elif args.email:
        print(f"\n→ Eliminando jugador con email: {args.email}")
        success = delete_player_by_email(player_repository, args.email)
    elif args.username:
        print(f"\n→ Eliminando jugador con username: {args.username}")
        success = delete_player_by_username(player_repository, args.username)
    
    if success:
        print("\n✓ Jugador eliminado exitosamente")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n✗ Error al eliminar el jugador")
        print("=" * 60)
        sys.exit(1)



