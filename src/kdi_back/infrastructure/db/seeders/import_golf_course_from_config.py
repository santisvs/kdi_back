# -*- coding: utf-8 -*-
"""
Importador de campos de golf desde ficheros de configuración JSON.

Cada fichero JSON describe un campo (golf_course) con sus hoyos, puntos,
obstáculos y golpes óptimos.

Uso:
    python import_golf_course_from_config.py campos/mi_campo_9_hoyos.json

La conexión (test / producción) se controla desde config.py / variables
de entorno, igual que en el resto del proyecto.
"""

import json
import sys
from pathlib import Path

try:
    from ..database import Database, init_database
except ImportError:
    # Si se ejecuta directamente como script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from kdi_back.infrastructure.db.database import Database, init_database


def import_golf_course_from_file(config_path: Path):
    """
    Importa un campo de golf completo desde un fichero JSON.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"No se encontró el fichero de configuración: {config_path}")

    print(f"\nLeyendo configuración desde: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        cfg = json.load(f)

    name = cfg.get("name")
    location_wkt = cfg.get("location_wkt")
    holes = cfg.get("holes", [])

    if not name:
        raise ValueError("El JSON debe incluir el campo 'name' del campo de golf")

    print(f"Nombre del campo: {name}")
    print(f"Número de hoyos en la configuración: {len(holes)}")

    with Database.get_cursor(commit=True) as (conn, cur):
        # 1) Insertar el campo de golf
        print("\nInsertando registro en 'golf_course'...")
        if location_wkt:
            cur.execute(
                """
                INSERT INTO golf_course (name, location)
                VALUES (%s, ST_GeogFromText(%s))
                RETURNING id;
                """,
                (name, location_wkt),
            )
        else:
            cur.execute(
                """
                INSERT INTO golf_course (name, location)
                VALUES (%s, NULL)
                RETURNING id;
                """,
                (name,),
            )

        course_id = cur.fetchone()["id"]
        print(f"  - golf_course.id = {course_id}")

        # 2) Insertar hoyos y estructuras relacionadas
        for hole_cfg in holes:
            hole_number = hole_cfg.get("hole_number")
            par = hole_cfg.get("par")
            length = hole_cfg.get("length")
            fairway_wkt = hole_cfg.get("fairway_polygon_wkt")
            green_wkt = hole_cfg.get("green_polygon_wkt")

            print(f"\nInsertando hoyo {hole_number}...")

            if fairway_wkt and green_wkt:
                cur.execute(
                    """
                    INSERT INTO hole (
                        course_id, hole_number, par, length,
                        fairway_polygon, green_polygon
                    )
                    VALUES (
                        %s, %s, %s, %s,
                        ST_GeogFromText(%s),
                        ST_GeogFromText(%s)
                    )
                    RETURNING id;
                    """,
                    (
                        course_id,
                        hole_number,
                        par,
                        length,
                        fairway_wkt,
                        green_wkt,
                    ),
                )
            else:
                # Permitir hoyos sin polígonos definidos aún
                cur.execute(
                    """
                    INSERT INTO hole (
                        course_id, hole_number, par, length,
                        fairway_polygon, green_polygon
                    )
                    VALUES (
                        %s, %s, %s, %s,
                        NULL, NULL
                    )
                    RETURNING id;
                    """,
                    (
                        course_id,
                        hole_number,
                        par,
                        length,
                    ),
                )

            hole_id = cur.fetchone()["id"]
            print(f"  - hole.id = {hole_id}")

            # 2.a) Puntos (tee, bandera, etc.)
            points = hole_cfg.get("points", [])
            if points:
                print(f"  - Insertando {len(points)} puntos (hole_point)...")
            for point in points:
                point_type = point.get("type")
                point_wkt = point.get("wkt")
                if not point_type or not point_wkt:
                    continue

                cur.execute(
                    """
                    INSERT INTO hole_point (hole_id, type, position)
                    VALUES (
                        %s, %s,
                        ST_GeogFromText(%s)
                    );
                    """,
                    (hole_id, point_type, point_wkt),
                )

            # 2.b) Obstáculos
            obstacles = hole_cfg.get("obstacles", [])
            if obstacles:
                print(f"  - Insertando {len(obstacles)} obstáculos...")
            for obstacle in obstacles:
                obs_type = obstacle.get("type")
                obs_name = obstacle.get("name")
                obs_wkt = obstacle.get("wkt")
                if not obs_type or not obs_wkt:
                    continue

                cur.execute(
                    """
                    INSERT INTO obstacle (hole_id, type, shape, name)
                    VALUES (
                        %s, %s,
                        ST_GeogFromText(%s),
                        %s
                    );
                    """,
                    (hole_id, obs_type, obs_wkt, obs_name),
                )

            # 2.c) Golpes óptimos (pueden ser varios por hoyo)
            optimal_shots = hole_cfg.get("optimal_shots", [])
            if optimal_shots:
                print(f"  - Insertando {len(optimal_shots)} golpes óptimos...")
            for shot in optimal_shots:
                description = shot.get("description")
                path_wkt = shot.get("wkt")
                if not path_wkt:
                    continue

                cur.execute(
                    """
                    INSERT INTO optimal_shot (hole_id, description, path)
                    VALUES (
                        %s, %s,
                        ST_GeogFromText(%s)
                    );
                    """,
                    (hole_id, description, path_wkt),
                )

    print("\n✓ Importación completada correctamente.")


if __name__ == "__main__":
    print("=" * 60)
    print("Importador de campos de golf desde JSON")
    print("=" * 60)

    if len(sys.argv) < 2:
        print("\nUso: python import_golf_course_from_config.py RUTA_FICHERO_JSON")
        print("Ejemplo: python import_golf_course_from_config.py data/campos/ejemplo_campo_9_hoyos.json")
        sys.exit(1)

    config_file = Path(sys.argv[1])
    # Si la ruta es relativa y no existe, intentar desde la raíz del proyecto
    if not config_file.is_absolute() and not config_file.exists():
        project_root = Path(__file__).parent.parent.parent.parent
        config_file = project_root / config_file

    if not init_database():
        print("✗ No se pudo inicializar la base de datos. Revisa config.py / .env")
        sys.exit(1)

    try:
        import_golf_course_from_file(config_file)
        print("\nTodo OK.")
    except Exception as e:
        print(f"\n✗ Error durante la importación: {e}")
        sys.exit(1)


