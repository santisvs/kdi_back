# -*- coding: utf-8 -*-
"""
Script para borrar toda la información de un hoyo específico.

Este script elimina:
- strategic_point (puntos estratégicos)
- optimal_shot (golpes óptimos)
- obstacle (obstáculos)
- hole_point (puntos del hoyo: tee, flag, etc.)
- hole (el hoyo mismo)

Uso:
    python scripts/campos/delete_hole_data.py <hole_id>
    
Ejemplo:
    python scripts/campos/delete_hole_data.py 1
"""

import sys
from pathlib import Path

# Agregar paths necesarios
project_root = Path(__file__).parent.parent.parent
src_dir = project_root / "src"
for path_to_add in [str(project_root), str(src_dir)]:
    if path_to_add not in sys.path:
        sys.path.insert(0, path_to_add)

try:
    from kdi_back.infrastructure.db.database import Database, init_database
except ImportError as e:
    print(f"Error al importar: {e}")
    print("  Ejecuta: pip install -e .")
    sys.exit(1)


def delete_hole_data(hole_id: int, confirm: bool = False) -> bool:
    """
    Elimina toda la información de un hoyo específico.
    
    Args:
        hole_id: ID del hoyo a eliminar
        confirm: Si es True, no pide confirmación
        
    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    if not confirm:
        print(f"\n⚠️  ADVERTENCIA: Se eliminará TODA la información del hoyo {hole_id}")
        print("   Esto incluye:")
        print("   - Puntos estratégicos (strategic_point)")
        print("   - Golpes óptimos (optimal_shot)")
        print("   - Obstáculos (obstacle)")
        print("   - Puntos del hoyo (hole_point: tee, flag, etc.)")
        print("   - El hoyo mismo (hole)")
        
        respuesta = input(f"\n¿Estás seguro de que quieres eliminar el hoyo {hole_id}? (s/N): ")
        if respuesta.lower() != 's':
            print("Operación cancelada.")
            return False
    
    try:
        with Database.get_cursor(commit=True) as (conn, cur):
            # 1. Verificar que el hoyo existe
            cur.execute("""
                SELECT h.id, h.hole_number, h.par, gc.name as course_name
                FROM hole h
                INNER JOIN golf_course gc ON h.course_id = gc.id
                WHERE h.id = %s;
            """, (hole_id,))
            
            hole_info = cur.fetchone()
            if not hole_info:
                print(f"✗ No se encontró el hoyo con ID {hole_id}")
                return False
            
            print(f"\n📋 Información del hoyo a eliminar:")
            print(f"   - ID: {hole_info['id']}")
            print(f"   - Número: {hole_info['hole_number']}")
            print(f"   - Par: {hole_info['par']}")
            print(f"   - Campo: {hole_info['course_name']}")
            
            # 2. Contar registros relacionados
            counts = {}
            
            cur.execute("SELECT COUNT(*) as count FROM strategic_point WHERE hole_id = %s;", (hole_id,))
            result = cur.fetchone()
            counts['strategic_points'] = result['count'] if result else 0
            
            cur.execute("SELECT COUNT(*) as count FROM optimal_shot WHERE hole_id = %s;", (hole_id,))
            result = cur.fetchone()
            counts['optimal_shots'] = result['count'] if result else 0
            
            cur.execute("SELECT COUNT(*) as count FROM obstacle WHERE hole_id = %s;", (hole_id,))
            result = cur.fetchone()
            counts['obstacles'] = result['count'] if result else 0
            
            cur.execute("SELECT COUNT(*) as count FROM hole_point WHERE hole_id = %s;", (hole_id,))
            result = cur.fetchone()
            counts['hole_points'] = result['count'] if result else 0
            
            print(f"\n📊 Registros a eliminar:")
            print(f"   - Puntos estratégicos: {counts['strategic_points']}")
            print(f"   - Golpes óptimos: {counts['optimal_shots']}")
            print(f"   - Obstáculos: {counts['obstacles']}")
            print(f"   - Puntos del hoyo: {counts['hole_points']}")
            print(f"   - El hoyo mismo: 1")
            
            total = sum(counts.values()) + 1
            print(f"\n   TOTAL: {total} registros")
            
            # 3. Eliminar en orden (respetando foreign keys)
            # NOTA: Las foreign keys tienen ON DELETE CASCADE, por lo que si eliminamos
            # el hole directamente, se eliminarán automáticamente todos los registros
            # relacionados. Sin embargo, eliminamos manualmente para mostrar el progreso.
            print(f"\n🗑️  Eliminando datos del hoyo {hole_id}...")
            
            # 3.1. Strategic points
            if counts['strategic_points'] > 0:
                cur.execute("DELETE FROM strategic_point WHERE hole_id = %s;", (hole_id,))
                print(f"   ✓ Eliminados {counts['strategic_points']} puntos estratégicos")
            
            # 3.2. Optimal shots
            if counts['optimal_shots'] > 0:
                cur.execute("DELETE FROM optimal_shot WHERE hole_id = %s;", (hole_id,))
                print(f"   ✓ Eliminados {counts['optimal_shots']} golpes óptimos")
            
            # 3.3. Obstacles
            if counts['obstacles'] > 0:
                cur.execute("DELETE FROM obstacle WHERE hole_id = %s;", (hole_id,))
                print(f"   ✓ Eliminados {counts['obstacles']} obstáculos")
            
            # 3.4. Hole points
            if counts['hole_points'] > 0:
                cur.execute("DELETE FROM hole_point WHERE hole_id = %s;", (hole_id,))
                print(f"   ✓ Eliminados {counts['hole_points']} puntos del hoyo")
            
            # 3.5. Hole (último)
            # Con CASCADE, si eliminamos el hole, se eliminarían automáticamente
            # todos los registros relacionados, pero ya los eliminamos manualmente arriba
            cur.execute("DELETE FROM hole WHERE id = %s;", (hole_id,))
            print(f"   ✓ Eliminado el hoyo {hole_id}")
            
            print(f"\n✅ Hoyo {hole_id} eliminado correctamente")
            print(f"   Total de registros eliminados: {total}")
            
            return True
            
    except Exception as e:
        print(f"\n✗ Error al eliminar el hoyo: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 2:
        print("=" * 80)
        print(" 🗑️  ELIMINAR DATOS DE UN HOYO")
        print("=" * 80)
        print("\nUso:")
        print("  python scripts/campos/delete_hole_data.py <hole_id>")
        print("\nEjemplo:")
        print("  python scripts/campos/delete_hole_data.py 1")
        print("\nOpciones:")
        print("  --force, -f    Eliminar sin pedir confirmación")
        print("\n⚠️  ADVERTENCIA: Esta operación NO se puede deshacer!")
        sys.exit(1)
    
    # Parsear argumentos
    hole_id_str = sys.argv[1]
    force = '--force' in sys.argv or '-f' in sys.argv
    
    try:
        hole_id = int(hole_id_str)
    except ValueError:
        print(f"✗ Error: '{hole_id_str}' no es un ID válido")
        print("  El ID debe ser un número entero")
        sys.exit(1)
    
    # Inicializar base de datos
    print("=" * 80)
    print(" 🗑️  ELIMINAR DATOS DE UN HOYO")
    print("=" * 80)
    
    if not init_database():
        print("✗ Error al inicializar la base de datos")
        sys.exit(1)
    
    # Eliminar datos
    success = delete_hole_data(hole_id, confirm=force)
    
    if success:
        print("\n" + "=" * 80)
        print(" ✅ PROCESO COMPLETADO")
        print("=" * 80)
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print(" ✗ PROCESO CANCELADO O FALLIDO")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

