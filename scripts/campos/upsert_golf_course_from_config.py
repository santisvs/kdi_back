# -*- coding: utf-8 -*-
"""
Función para hacer upsert (update/insert) de campos de golf desde ficheros JSON.

Esta función actualiza los registros existentes o los crea si no existen.
"""

import json
from pathlib import Path

try:
    from kdi_back.infrastructure.db.database import Database, init_database
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from kdi_back.infrastructure.db.database import Database, init_database


def upsert_golf_course_from_file(config_path: Path):
    """
    Hace upsert (update si existe, insert si no) de un campo de golf desde un fichero JSON.
    
    Estrategia:
    - Campo de golf: busca por nombre, actualiza si existe, crea si no
    - Hoyos: busca por course_id + hole_number, actualiza si existe, crea si no
    - Puntos, obstáculos, golpes óptimos, puntos estratégicos: elimina los existentes del hoyo y crea nuevos
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
        # 1) Upsert del campo de golf
        print("\nProcesando campo de golf...")
        
        # Buscar si existe el campo por nombre
        cur.execute(
            """
            SELECT id FROM golf_course WHERE name = %s;
            """,
            (name,),
        )
        existing_course = cur.fetchone()
        
        if existing_course:
            course_id = existing_course["id"]
            print(f"  - Campo existente encontrado (id={course_id}), actualizando...")
            if location_wkt:
                cur.execute(
                    """
                    UPDATE golf_course 
                    SET location = ST_GeogFromText(%s)
                    WHERE id = %s;
                    """,
                    (location_wkt, course_id),
                )
            print(f"  - golf_course.id = {course_id} (actualizado)")
        else:
            print(f"  - Campo no encontrado, creando nuevo...")
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
            print(f"  - golf_course.id = {course_id} (creado)")

        # 2) Upsert de hoyos y estructuras relacionadas
        for hole_cfg in holes:
            hole_number = hole_cfg.get("hole_number")
            par = hole_cfg.get("par")
            length = hole_cfg.get("length")
            fairway_wkt = hole_cfg.get("fairway_polygon_wkt")
            green_wkt = hole_cfg.get("green_polygon_wkt")
            bbox_wkt = hole_cfg.get("bbox_polygon_wkt")

            print(f"\nProcesando hoyo {hole_number}...")

            # Buscar si existe el hoyo
            cur.execute(
                """
                SELECT id FROM hole 
                WHERE course_id = %s AND hole_number = %s;
                """,
                (course_id, hole_number),
            )
            existing_hole = cur.fetchone()

            if existing_hole:
                hole_id = existing_hole["id"]
                print(f"  - Hoyo existente encontrado (id={hole_id}), actualizando...")
                
                # Actualizar el hoyo
                # Construir la query dinámicamente según qué polígonos están disponibles
                update_fields = []
                update_values = []
                
                if par is not None:
                    update_fields.append("par = %s")
                    update_values.append(par)
                if length is not None:
                    update_fields.append("length = %s")
                    update_values.append(length)
                
                if fairway_wkt:
                    update_fields.append("fairway_polygon = ST_GeogFromText(%s)")
                    update_values.append(fairway_wkt)
                else:
                    update_fields.append("fairway_polygon = NULL")
                
                if green_wkt:
                    update_fields.append("green_polygon = ST_GeogFromText(%s)")
                    update_values.append(green_wkt)
                else:
                    update_fields.append("green_polygon = NULL")
                
                if bbox_wkt:
                    update_fields.append("bbox_polygon = ST_GeogFromText(%s)")
                    update_values.append(bbox_wkt)
                else:
                    update_fields.append("bbox_polygon = NULL")
                
                update_values.append(hole_id)
                
                query = f"""
                    UPDATE hole 
                    SET {', '.join(update_fields)}
                    WHERE id = %s;
                """
                cur.execute(query, tuple(update_values))
                
                # Eliminar datos relacionados existentes para recrearlos
                print(f"  - Eliminando datos relacionados del hoyo...")
                cur.execute("DELETE FROM hole_point WHERE hole_id = %s;", (hole_id,))
                cur.execute("DELETE FROM obstacle WHERE hole_id = %s;", (hole_id,))
                cur.execute("DELETE FROM optimal_shot WHERE hole_id = %s;", (hole_id,))
                cur.execute("DELETE FROM strategic_point WHERE hole_id = %s;", (hole_id,))
                
            else:
                print(f"  - Hoyo no encontrado, creando nuevo...")
                # Crear nuevo hoyo
                # Construir la query dinámicamente según qué polígonos están disponibles
                insert_fields = ["course_id", "hole_number"]
                insert_placeholders = ["%s", "%s"]
                insert_values = [course_id, hole_number]
                
                if par is not None:
                    insert_fields.append("par")
                    insert_placeholders.append("%s")
                    insert_values.append(par)
                if length is not None:
                    insert_fields.append("length")
                    insert_placeholders.append("%s")
                    insert_values.append(length)
                
                if fairway_wkt:
                    insert_fields.append("fairway_polygon")
                    insert_placeholders.append("ST_GeogFromText(%s)")
                    insert_values.append(fairway_wkt)
                else:
                    insert_fields.append("fairway_polygon")
                    insert_placeholders.append("NULL")
                
                if green_wkt:
                    insert_fields.append("green_polygon")
                    insert_placeholders.append("ST_GeogFromText(%s)")
                    insert_values.append(green_wkt)
                else:
                    insert_fields.append("green_polygon")
                    insert_placeholders.append("NULL")
                
                if bbox_wkt:
                    insert_fields.append("bbox_polygon")
                    insert_placeholders.append("ST_GeogFromText(%s)")
                    insert_values.append(bbox_wkt)
                else:
                    insert_fields.append("bbox_polygon")
                    insert_placeholders.append("NULL")
                
                query = f"""
                    INSERT INTO hole ({', '.join(insert_fields)})
                    VALUES ({', '.join(insert_placeholders)})
                    RETURNING id;
                """
                # Solo incluir valores para los placeholders que no son NULL
                final_values = []
                for i, placeholder in enumerate(insert_placeholders):
                    if placeholder != "NULL":
                        final_values.append(insert_values[i])
                cur.execute(query, tuple(final_values))
                hole_id = cur.fetchone()["id"]
                print(f"  - hole.id = {hole_id} (creado)")

            # 2.a) Insertar puntos (tee, bandera, etc.)
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

            # 2.b) Insertar obstáculos
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

            # 2.c) Insertar golpes óptimos
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

            # 2.d) Insertar puntos estratégicos
            strategic_points = hole_cfg.get("strategic_points", [])
            if strategic_points:
                print(f"  - Insertando {len(strategic_points)} puntos estratégicos...")
            for sp in strategic_points:
                sp_type = sp.get("type")
                sp_name = sp.get("name")
                sp_description = sp.get("description")
                sp_distance_to_flag = sp.get("distance_to_flag")
                sp_priority = sp.get("priority", 5)
                sp_wkt = sp.get("wkt")
                if not sp_type or not sp_wkt:
                    continue

                cur.execute(
                    """
                    INSERT INTO strategic_point (
                        hole_id, type, name, description, 
                        position, distance_to_flag, priority
                    )
                    VALUES (
                        %s, %s, %s, %s,
                        ST_GeogFromText(%s), %s, %s
                    );
                    """,
                    (hole_id, sp_type, sp_name, sp_description, 
                     sp_wkt, sp_distance_to_flag, sp_priority),
                )

    print("\n✓ Upsert completado correctamente.")

