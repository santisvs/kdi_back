# -*- coding: utf-8 -*-
"""
Script sencillo para rellenar datos de ejemplo de un campo de golf de 9 hoyos.

Usa las tablas:
- golf_course
- hole
- hole_point
- obstacle
- optimal_shot

La base de datos (test / prod) se controla desde config.py / variables de entorno,
igual que en el resto del proyecto.
"""

try:
    from ..database import Database, init_database
except ImportError:
    # Si se ejecuta directamente como script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from kdi_back.infrastructure.db.database import Database, init_database


def seed_golf_course_9_holes():
    """
    Inserta un campo de golf de 9 hoyos con datos de ejemplo muy simples.
    Ajusta coordenadas, pars, longitudes, etc. a tu caso real.
    """
    print("\n=== Seed: campo de golf de 9 hoyos ===")

    with Database.get_cursor(commit=True) as (conn, cur):
        # 1) Crear el campo de golf principal
        print("Insertando campo de golf...")
        cur.execute(
            """
            INSERT INTO golf_course (name, location)
            VALUES (%s, ST_GeogFromText(%s))
            RETURNING id;
            """,
            (
                "Mi Campo de 9 Hoyos",
                "SRID=4326;POINT(-3.91623 40.54727)",  # lon lat
            ),
        )
        course_id = cur.fetchone()["id"]
        print(f"  - golf_course.id = {course_id}")

        # 2) Crear 9 hoyos muy sencillos
        print("Insertando hoyos...")
        hole_ids = []
        for hole_number in range(1, 10):
            par = 3 if hole_number <= 3 else 4  # ejemplo tonto
            length = 150 if hole_number <= 3 else 320

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
                    # Polígonos de ejemplo MUY simplificados (no reales)
                    "SRID=4326;POLYGON((-3.9165 40.5470, -3.9159 40.5470, -3.9159 40.5474, -3.9165 40.5474, -3.9165 40.5470))",
                    "SRID=4326;POLYGON((-3.9162 40.5472, -3.9160 40.5472, -3.9160 40.5473, -3.9162 40.5473, -3.9162 40.5472))",
                ),
            )
            hole_id = cur.fetchone()["id"]
            hole_ids.append(hole_id)
            print(f"  - hole {hole_number}: id = {hole_id}")

        # 3) Puntos clave por hoyo (tee y bandera)
        print("Insertando puntos (hole_point)...")
        for idx, hole_id in enumerate(hole_ids, start=1):
            # tee
            cur.execute(
                """
                INSERT INTO hole_point (hole_id, type, position)
                VALUES (
                    %s, 'tee',
                    ST_GeogFromText(%s)
                );
                """,
                (
                    hole_id,
                    "SRID=4326;POINT(-3.9164 40.5471)",
                ),
            )

            # bandera
            cur.execute(
                """
                INSERT INTO hole_point (hole_id, type, position)
                VALUES (
                    %s, 'flag',
                    ST_GeogFromText(%s)
                );
                """,
                (
                    hole_id,
                    "SRID=4326;POINT(-3.9161 40.54725)",
                ),
            )

        # 4) Obstáculos simples (p.ej. bunker en algunos hoyos)
        print("Insertando obstáculos (obstacle)...")
        for idx, hole_id in enumerate(hole_ids, start=1):
            if idx in (3, 6, 9):
                cur.execute(
                    """
                    INSERT INTO obstacle (hole_id, type, shape, name)
                    VALUES (
                        %s, 'bunker',
                        ST_GeogFromText(%s),
                        %s
                    );
                    """,
                    (
                        hole_id,
                        "SRID=4326;POLYGON((-3.9163 40.54715, -3.9162 40.54715, -3.9162 40.54720, -3.9163 40.54720, -3.9163 40.54715))",
                        f"Bunker hoyo {idx}",
                    ),
                )

        # 5) Golpe óptimo muy básico (línea recta tee -> bandera)
        print("Insertando golpes óptimos (optimal_shot)...")
        for idx, hole_id in enumerate(hole_ids, start=1):
            cur.execute(
                """
                INSERT INTO optimal_shot (hole_id, description, path)
                VALUES (
                    %s,
                    %s,
                    ST_GeogFromText(%s)
                );
                """,
                (
                    hole_id,
                    f"Golpe ideal del tee a la bandera en el hoyo {idx}",
                    "SRID=4326;LINESTRING(-3.9164 40.5471, -3.9161 40.54725)",
                ),
            )

        print("✓ Seed de campo de 9 hoyos completado.")


if __name__ == "__main__":
    print("=" * 60)
    print("Seed de datos de golf (9 hoyos)")
    print("=" * 60)

    if init_database():
        seed_golf_course_9_holes()
        print("\nTodo OK.")
    else:
        print("✗ No se pudo inicializar la base de datos. Revisa config.py / .env")


