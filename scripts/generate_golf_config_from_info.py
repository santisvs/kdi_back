# -*- coding: utf-8 -*-
"""
Generador de JSON de campos de golf a partir de ficheros de info con lat/lon.

Objetivo:
- En la carpeta `campos_info/` defines campos usando coordenadas tal y como
  las devuelve Google Maps: LATITUD, LONGITUD.
- Este script convierte esa info en el formato con WKT que usa
  `import_golf_course_from_config.py` y genera un JSON en `campos/`.

Uso:
    python scripts/generate_golf_config_from_info.py data/campos_info/mi_campo_info.json data/campos/mi_campo.json

Si no indicas salida, la genera automáticamente en `data/campos/` con el mismo nombre.
"""

import json
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any


def point_to_wkt(lat: float, lon: float) -> str:
    """
    Convierte un punto LAT, LON al WKT que usamos (SRID=4326;POINT(lon lat)).
    """
    return f"SRID=4326;POINT({lon} {lat})"


def polygon_to_wkt(coords: List[Tuple[float, float]]) -> str:
    """
    Convierte una lista de puntos [ [lat, lon], ... ] a un POLYGON WKT.
    Cierra el polígono automáticamente si el primer y último punto no coinciden.
    """
    if len(coords) < 3:
        raise ValueError("Un polígono necesita al menos 3 puntos")

    # Asegurar que el polígono está cerrado
    first = coords[0]
    last = coords[-1]
    if first[0] != last[0] or first[1] != last[1]:
        coords = coords + [first]

    # Recordar que WKT usa LON LAT
    pts = ", ".join(f"{lon} {lat}" for lat, lon in coords)
    return f"SRID=4326;POLYGON(({pts}))"


def linestring_to_wkt(coords: List[Tuple[float, float]]) -> str:
    """
    Convierte una lista de puntos [ [lat, lon], ... ] a un LINESTRING WKT.
    """
    if len(coords) < 2:
        raise ValueError("Un LINESTRING necesita al menos 2 puntos")
    pts = ", ".join(f"{lon} {lat}" for lat, lon in coords)
    return f"SRID=4326;LINESTRING({pts})"


def convert_info_to_config(info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convierte el JSON de `campos_info` (lat/lon) al JSON con WKT para `campos`.

    Formato esperado en campos_info:

    {
      "name": "Mi Campo",
      "location": { "lat": 40.44, "lon": -3.87 },
      "holes": [
        {
          "hole_number": 1,
          "par": 4,
          "length": 320,
          "fairway_polygon": [ [40.44, -3.87], ... ],
          "green_polygon": [ [40.44, -3.87], ... ],
          "points": [
            { "type": "tee", "lat": 40.44, "lon": -3.87 },
            { "type": "flag", "lat": 40.45, "lon": -3.86 }
          ],
          "obstacles": [
            {
              "type": "bunker",
              "name": "Bunker izq",
              "polygon": [ [40.44, -3.87], ... ]
            }
          ],
          "optimal_shots": [
            {
              "description": "Golpe ideal",
              "line": [ [40.44, -3.87], [40.45, -3.86] ]
            }
          ]
        }
      ]
    }
    """
    name = info.get("name")
    if not name:
        raise ValueError("El JSON de info debe incluir 'name'")

    location = info.get("location")
    location_wkt = None
    if location and "lat" in location and "lon" in location:
        location_wkt = point_to_wkt(location["lat"], location["lon"])

    holes_info = info.get("holes", [])
    holes_config = []

    for hole in holes_info:
        hole_number = hole.get("hole_number")
        par = hole.get("par")
        length = hole.get("length")

        fairway_polygon_wkt = None
        if "fairway_polygon" in hole and hole["fairway_polygon"]:
            fairway_polygon_wkt = polygon_to_wkt(hole["fairway_polygon"])

        green_polygon_wkt = None
        if "green_polygon" in hole and hole["green_polygon"]:
            green_polygon_wkt = polygon_to_wkt(hole["green_polygon"])

        # Puntos
        points_cfg = []
        for p in hole.get("points", []):
            if "lat" not in p or "lon" not in p or "type" not in p:
                continue
            wkt = point_to_wkt(p["lat"], p["lon"])
            points_cfg.append({
                "type": p["type"],
                "wkt": wkt
            })

        # Obstáculos
        obstacles_cfg = []
        for o in hole.get("obstacles", []):
            if "polygon" not in o or not o["polygon"] or "type" not in o:
                continue
            poly_wkt = polygon_to_wkt(o["polygon"])
            obstacles_cfg.append({
                "type": o["type"],
                "name": o.get("name"),
                "wkt": poly_wkt
            })

        # Golpes óptimos
        shots_cfg = []
        for s in hole.get("optimal_shots", []):
            if "line" not in s or not s["line"]:
                continue
            line_wkt = linestring_to_wkt(s["line"])
            shots_cfg.append({
                "description": s.get("description"),
                "wkt": line_wkt
            })

        hole_cfg = {
            "hole_number": hole_number,
            "par": par,
            "length": length,
            "fairway_polygon_wkt": fairway_polygon_wkt,
            "green_polygon_wkt": green_polygon_wkt,
            "points": points_cfg,
            "obstacles": obstacles_cfg,
            "optimal_shots": shots_cfg,
        }

        holes_config.append(hole_cfg)

    return {
        "name": name,
        "location_wkt": location_wkt,
        "holes": holes_config,
    }


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python generate_golf_config_from_info.py RUTA_INFO_JSON [RUTA_SALIDA_JSON]")
        print("Ejemplo:")
        print("  python generate_golf_config_from_info.py campos_info/mi_campo_info.json campos/mi_campo.json")
        sys.exit(1)

    info_path = Path(sys.argv[1])
    # Si la ruta es relativa y no existe, intentar desde la raíz del proyecto
    if not info_path.is_absolute() and not info_path.exists():
        project_root = Path(__file__).parent.parent
        info_path = project_root / info_path
    
    if not info_path.exists():
        print(f"✗ No existe el fichero de info: {info_path}")
        sys.exit(1)

    if len(sys.argv) >= 3:
        out_path = Path(sys.argv[2])
        # Si la ruta es relativa, intentar desde la raíz del proyecto
        if not out_path.is_absolute():
            project_root = Path(__file__).parent.parent
            out_path = project_root / out_path
    else:
        # Por defecto, misma base de nombre pero en carpeta data/campos/
        project_root = Path(__file__).parent.parent
        out_dir = project_root / "data" / "campos"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / info_path.name.replace("_info", "")

    with info_path.open("r", encoding="utf-8") as f:
        info_data = json.load(f)

    config_data = convert_info_to_config(info_data)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

    print(f"✓ Configuración generada en: {out_path}")


if __name__ == "__main__":
    main()


