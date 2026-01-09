# -*- coding: utf-8 -*-
"""
Configuración del servicio - Carga de variables de entorno
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Detectar si estamos en AWS Elastic Beanstalk
# En EB, esta variable de entorno está siempre presente
IS_AWS_ENVIRONMENT = os.getenv('ELASTIC_BEANSTALK_ENVIRONMENT') is not None

# Variables de entorno de AWS
# En AWS: No se usan credenciales explícitas, se usa IAM Role
# En local: Se usan credenciales del .env
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID') if not IS_AWS_ENVIRONMENT else None
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY') if not IS_AWS_ENVIRONMENT else None
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# Variables de entorno de PostgreSQL/PostGIS
# En AWS: Se usan las variables de entorno configuradas en Elastic Beanstalk
# En local: Se usan valores por defecto o del .env
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'db_kdi_test')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

# Variables de entorno de AWS Bedrock Knowledge Base
AWS_KNOWLEDGE_BASE_ID = os.getenv('AWS_KNOWLEDGE_BASE_ID', None)
# La Knowledge Base se encuentra en la región eu-south-2
AWS_KNOWLEDGE_BASE_REGION = os.getenv('AWS_KNOWLEDGE_BASE_REGION', 'eu-south-2')

# Variables de entorno de autenticación JWT
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))

# Variables de entorno para OAuth
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', None)
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', None)
INSTAGRAM_CLIENT_ID = os.getenv('INSTAGRAM_CLIENT_ID', None)
INSTAGRAM_CLIENT_SECRET = os.getenv('INSTAGRAM_CLIENT_SECRET', None)

