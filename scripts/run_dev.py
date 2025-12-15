# -*- coding: utf-8 -*-
"""
Script para ejecutar el servidor en modo desarrollo
"""
import sys
from pathlib import Path

# Añadir src al path para importar kdi_back
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from kdi_back.api.main import create_app

if __name__ == '__main__':
    app = create_app()
    print("=" * 50)
    print("Servidor iniciado en modo desarrollo")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)

