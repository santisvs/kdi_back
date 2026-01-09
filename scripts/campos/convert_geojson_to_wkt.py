"""
Script para convertir GeoJSON (de geojson.io) al formato JSON con WKT
usado en la base de datos (formato de las_rejas.json).

El GeoJSON usa coordenadas [lon, lat] y las convierte directamente a WKT.
"""
import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import List, Tuple, Any, Dict


def point_to_wkt_from_geojson(coords: List[float]) -> str:
    """
    Convierte coordenadas GeoJSON [lon, lat] a WKT POINT.
    """
    if len(coords) < 2:
        raise ValueError("Un punto necesita al menos 2 coordenadas [lon, lat]")
    lon, lat = coords[0], coords[1]
    return f"SRID=4326;POINT({lon} {lat})"


def polygon_to_wkt_from_geojson(coords: List[List[List[float]]]) -> str:
    """
    Convierte coordenadas GeoJSON Polygon a WKT POLYGON.
    GeoJSON Polygon: [[[lon, lat], [lon, lat], ...]]
    WKT: SRID=4326;POLYGON((lon lat, lon lat, ...))
    """
    if not coords or not coords[0]:
        raise ValueError("Un polígono necesita coordenadas")
    
    # GeoJSON Polygon tiene el primer elemento como el anillo exterior
    ring = coords[0]
    if len(ring) < 3:
        raise ValueError("Un polígono necesita al menos 3 puntos")
    
    # Asegurar que el polígono está cerrado
    first = ring[0]
    last = ring[-1]
    if first[0] != last[0] or first[1] != last[1]:
        ring = ring + [first]
    
    # WKT usa "lon lat" (ya está en el formato correcto del GeoJSON)
    pts = ", ".join(f"{point[0]} {point[1]}" for point in ring)
    return f"SRID=4326;POLYGON(({pts}))"


def linestring_to_wkt_from_geojson(coords: List[List[float]]) -> str:
    """
    Convierte coordenadas GeoJSON LineString a WKT LINESTRING.
    GeoJSON LineString: [[lon, lat], [lon, lat], ...]
    WKT: SRID=4326;LINESTRING(lon lat, lon lat, ...)
    """
    if len(coords) < 2:
        raise ValueError("Un LINESTRING necesita al menos 2 puntos")
    
    # WKT usa "lon lat" (ya está en el formato correcto del GeoJSON)
    pts = ", ".join(f"{point[0]} {point[1]}" for point in coords)
    return f"SRID=4326;LINESTRING({pts})"


def convert_geojson_to_wkt_format(input_file: Path, output_file: Path) -> Dict[str, Any]:
    """
    Convierte GeoJSON al formato JSON con WKT usado en la base de datos.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        geojson = json.load(f)
    
    # Estructura base del resultado
    result = {
        "name": "",
        "location_wkt": None,
        "holes": []
    }
    
    # Agrupar features por hole_number
    holes_data = defaultdict(lambda: {
        "hole_number": None,
        "par": None,
        "length": None,
        "fairway_polygon_wkt": None,
        "green_polygon_wkt": None,
        "bbox_polygon_wkt": None,
        "points": [],
        "obstacles": [],
        "optimal_shots": [],
        "strategic_points": []
    })
    
    # Procesar cada feature
    for feature in geojson.get('features', []):
        props = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        geom_type = geometry.get('type')
        coords = geometry.get('coordinates', [])
        
        feature_type = props.get('type', '')
        # Buscar hole_number (puede estar escrito como hole_number o hole_numer por typos)
        hole_num = props.get('hole_number') or props.get('hole_numer')
        
        # Ubicación del campo
        if feature_type == 'course_location':
            result['name'] = props.get('name', '')
            if geom_type == 'Point' and coords:
                result['location_wkt'] = point_to_wkt_from_geojson(coords)
            continue
        
        # Si no tiene hole_number, saltar
        if hole_num is None:
            continue
        
        hole = holes_data[hole_num]
        hole['hole_number'] = hole_num
        if props.get('par'):
            hole['par'] = props.get('par')
        if props.get('length'):
            hole['length'] = props.get('length')
        
        # Fairway
        if feature_type == 'fairway' and geom_type == 'Polygon':
            try:
                hole['fairway_polygon_wkt'] = polygon_to_wkt_from_geojson(coords)
            except Exception as e:
                print(f"⚠️  Error procesando fairway del hoyo {hole_num}: {e}")
        
        # Green
        elif feature_type == 'green' and geom_type == 'Polygon':
            try:
                hole['green_polygon_wkt'] = polygon_to_wkt_from_geojson(coords)
            except Exception as e:
                print(f"⚠️  Error procesando green del hoyo {hole_num}: {e}")
        
        # Bbox
        elif feature_type == 'bbox' and geom_type == 'Polygon':
            try:
                hole['bbox_polygon_wkt'] = polygon_to_wkt_from_geojson(coords)
            except Exception as e:
                print(f"⚠️  Error procesando bbox del hoyo {hole_num}: {e}")
        
        # Puntos (tee, flag, etc.)
        elif geom_type == 'Point' and feature_type in ['tee', 'flag', 'tee_white', 'tee_yellow']:
            try:
                wkt = point_to_wkt_from_geojson(coords)
                hole['points'].append({
                    "type": feature_type,
                    "wkt": wkt
                })
            except Exception as e:
                print(f"⚠️  Error procesando punto {feature_type} del hoyo {hole_num}: {e}")
        
        # Obstáculos (bunkers, trees, water, etc.)
        elif feature_type in ['bunker', 'trees', 'water'] and geom_type == 'Polygon':
            try:
                wkt = polygon_to_wkt_from_geojson(coords)
                obstacle = {
                    "type": feature_type,
                    "wkt": wkt
                }
                if props.get('name'):
                    obstacle['name'] = props.get('name')
                hole['obstacles'].append(obstacle)
            except Exception as e:
                print(f"⚠️  Error procesando obstáculo {feature_type} del hoyo {hole_num}: {e}")
        
        # Golpes óptimos (líneas)
        elif feature_type == 'optimal_shot' and geom_type == 'LineString':
            try:
                wkt = linestring_to_wkt_from_geojson(coords)
                hole['optimal_shots'].append({
                    "description": props.get('description', ''),
                    "wkt": wkt
                })
            except Exception as e:
                print(f"⚠️  Error procesando golpe óptimo del hoyo {hole_num}: {e}")
        
        # Puntos estratégicos
        elif feature_type in ['fairway_center_far', 'fairway_center_mid', 'layup_zone', 
                             'approach_zone', 'strategic_point'] and geom_type == 'Point':
            try:
                wkt = point_to_wkt_from_geojson(coords)
                strategic_point = {
                    "type": feature_type,
                    "wkt": wkt
                }
                if props.get('name'):
                    strategic_point['name'] = props.get('name')
                if props.get('description') is not None:
                    strategic_point['description'] = props.get('description')
                if props.get('distance_to_flag') is not None:
                    strategic_point['distance_to_flag'] = props.get('distance_to_flag')
                if props.get('priority') is not None:
                    strategic_point['priority'] = props.get('priority')
                hole['strategic_points'].append(strategic_point)
            except Exception as e:
                print(f"⚠️  Error procesando punto estratégico del hoyo {hole_num}: {e}")
    
    # Convertir el diccionario a lista ordenada
    result['holes'] = []
    for hole_num, data in sorted(holes_data.items()):
        hole = {
            "hole_number": data['hole_number'],
            "par": data['par'],
            "length": data['length']
        }
        
        # Agregar campos solo si existen
        if data['fairway_polygon_wkt']:
            hole['fairway_polygon_wkt'] = data['fairway_polygon_wkt']
        if data['green_polygon_wkt']:
            hole['green_polygon_wkt'] = data['green_polygon_wkt']
        if data['bbox_polygon_wkt']:
            hole['bbox_polygon_wkt'] = data['bbox_polygon_wkt']
        if data['points']:
            hole['points'] = data['points']
        if data['obstacles']:
            hole['obstacles'] = data['obstacles']
        if data['optimal_shots']:
            hole['optimal_shots'] = data['optimal_shots']
        if data['strategic_points']:
            hole['strategic_points'] = data['strategic_points']
        
        result['holes'].append(hole)
    
    # Guardar archivo
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON con WKT generado exitosamente: {output_file}")
    print(f"   Campo: {result['name']}")
    print(f"   Hoyos procesados: {len(result['holes'])}")
    
    return result


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    if len(sys.argv) > 1:
        # Si se proporciona un archivo como argumento
        input_file = Path(sys.argv[1])
        if len(sys.argv) > 2:
            output_file = Path(sys.argv[2])
        else:
            # Si no se especifica salida, usar el mismo nombre pero .json en carpeta campos
            output_file = project_root / "data" / "campos" / input_file.stem.replace("_info", "").replace("_geojson", "") + ".json"
    else:
        # Valores por defecto
        input_file = project_root / "data" / "campos_info" / "las_rejas_info.geojson"
        output_file = project_root / "data" / "campos" / "las_rejas.json"
    
    if not input_file.exists():
        print(f"❌ Error: No se encontró el archivo {input_file}")
        print(f"   Por favor, asegúrate de que el archivo GeoJSON existe.")
        print(f"\n💡 Uso:")
        print(f"   python scripts/campos/convert_geojson_to_wkt.py [archivo_geojson] [archivo_salida.json]")
        print(f"   Ejemplo: python scripts/campos/convert_geojson_to_wkt.py mi_archivo.geojson")
        sys.exit(1)
    
    # Crear directorio de salida si no existe
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    convert_geojson_to_wkt_format(input_file, output_file)
    print(f"\n📌 Archivo JSON con WKT generado en: {output_file}")
    print(f"   Este archivo está listo para importar a la base de datos.")

