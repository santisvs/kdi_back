# -*- coding: utf-8 -*-
"""
Script para actualizar un campo de golf desde GeoJSON a la base de datos.

Este script automatiza el proceso completo:
1. Convierte el archivo GeoJSON a formato JSON con WKT
2. Actualiza/guarda el archivo JSON
3. Importa los datos a la base de datos

Uso:
    python scripts/campos/update_golf_from_geojson.py [archivo.geojson]
    
Ejemplo:
    python scripts/campos/update_golf_from_geojson.py data/campos_info/las_rejas.geojson
"""

import sys
from pathlib import Path

# Agregar el proyecto al path ANTES de cualquier import
project_root = Path(__file__).parent.parent.parent
src_dir = project_root / "src"

# Agregar tanto el root como src al path
for path_to_add in [str(project_root), str(src_dir)]:
    if path_to_add not in sys.path:
        sys.path.insert(0, path_to_add)

# Importar funciones de conversión del script convert_geojson_to_wkt
try:
    # Importar funciones directamente desde el módulo
    import importlib.util
    convert_script_path = Path(__file__).parent / "convert_geojson_to_wkt.py"
    spec = importlib.util.spec_from_file_location("convert_geojson_to_wkt", convert_script_path)
    convert_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(convert_module)
    convert_geojson_to_wkt_format = convert_module.convert_geojson_to_wkt_format
except Exception as e:
    print("=" * 80)
    print("✗ ERROR: No se puede importar el módulo de conversión")
    print("=" * 80)
    print(f"\nDetalles del error: {e}")
    sys.exit(1)

# Importar función de upsert
try:
    import importlib.util
    upsert_script_path = Path(__file__).parent / "upsert_golf_course_from_config.py"
    spec = importlib.util.spec_from_file_location("upsert_golf_course_from_config", upsert_script_path)
    upsert_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(upsert_module)
    upsert_golf_course_from_file = upsert_module.upsert_golf_course_from_file
except Exception as e:
    print("=" * 80)
    print("✗ ERROR: No se puede importar el módulo de upsert")
    print("=" * 80)
    print(f"\nDetalles del error: {e}")
    sys.exit(1)

# Imports de kdi_back para inicialización de BD
try:
    from kdi_back.infrastructure.db.database import init_database
except ImportError as e:
    print("=" * 80)
    print("✗ ERROR: No se pueden importar los módulos de kdi_back")
    print("=" * 80)
    print(f"\nDetalles del error: {e}")
    print(f"\nRutas configuradas:")
    print(f"  - Project root: {project_root}")
    print(f"  - Src dir: {src_dir}")
    print(f"\nPosibles soluciones:")
    print(f"  1. Asegúrate de estar en la raíz del proyecto")
    print(f"  2. Instala el proyecto en modo desarrollo:")
    print(f"     pip install -e .")
    print("=" * 80)
    sys.exit(1)


def main():
    print("=" * 80)
    print(" 🏌️  ACTUALIZAR CAMPO DE GOLF DESDE GEOJSON")
    print("=" * 80)
    
    # Obtener archivo GeoJSON de entrada
    if len(sys.argv) > 1:
        geojson_file = Path(sys.argv[1])
        # Si la ruta es relativa y no existe, intentar desde la raíz del proyecto
        if not geojson_file.is_absolute() and not geojson_file.exists():
            geojson_file = project_root / geojson_file
    else:
        # Archivo por defecto
        geojson_file = project_root / "data" / "campos_info" / "las_rejas.geojson"
        print(f"\n💡 No se especificó archivo, usando por defecto: {geojson_file}")
    
    if not geojson_file.exists():
        print(f"\n✗ Error: No se encontró el archivo GeoJSON: {geojson_file}")
        print(f"\n💡 Uso:")
        print(f"   python scripts/campos/update_golf_from_geojson.py [archivo.geojson]")
        print(f"\n   Ejemplo:")
        print(f"   python scripts/campos/update_golf_from_geojson.py data/campos_info/las_rejas.geojson")
        return False
    
    # Determinar archivo JSON de salida
    # Si el archivo se llama las_rejas.geojson, el JSON será las_rejas.json
    json_stem = geojson_file.stem.replace("_info", "").replace("_geojson", "")
    json_file = project_root / "data" / "campos" / f"{json_stem}.json"
    
    print(f"\n📋 Archivos:")
    print(f"   GeoJSON de entrada:  {geojson_file}")
    print(f"   JSON de salida:      {json_file}")
    
    # Paso 1: Convertir GeoJSON a JSON con WKT
    print("\n" + "=" * 80)
    print(" ➤ Paso 1: Convirtiendo GeoJSON a formato JSON con WKT...")
    print("=" * 80)
    try:
        # Crear directorio de salida si no existe
        json_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convertir
        convert_geojson_to_wkt_format(geojson_file, json_file)
        print(f"✓ Conversión completada: {json_file}")
    except Exception as e:
        print(f"\n✗ Error al convertir GeoJSON: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Paso 2: Inicializar base de datos
    print("\n" + "=" * 80)
    print(" ➤ Paso 2: Inicializando conexión a base de datos...")
    print("=" * 80)
    if not init_database():
        print("✗ No se pudo inicializar la base de datos")
        print("  Revisa config.py o las variables de entorno")
        return False
    print("✓ Conexión establecida")
    
    # Paso 3: Hacer upsert de datos en la BD
    print("\n" + "=" * 80)
    print(f" ➤ Paso 3: Actualizando/insertando datos en la base de datos...")
    print("=" * 80)
    try:
        upsert_golf_course_from_file(json_file)
        print("\n✓ Datos actualizados/insertados correctamente")
    except Exception as e:
        print(f"\n✗ Error al actualizar/insertar datos: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Resumen final
    print("\n" + "=" * 80)
    print(" ✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("=" * 80)
    print(f"\n📊 Resumen:")
    print(f"  ✓ GeoJSON convertido: {geojson_file}")
    print(f"  ✓ JSON actualizado:   {json_file}")
    print(f"  ✓ Datos actualizados/insertados en la base de datos")
    print(f"  ✓ Campo de golf, hoyos, puntos, obstáculos y golpes óptimos")
    print(f"  ✓ Puntos estratégicos incluidos")
    print("\n🚀 El sistema está actualizado y listo para usar!")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

