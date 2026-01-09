# -*- coding: utf-8 -*-
"""
Punto de entrada para AWS Elastic Beanstalk
Este archivo es requerido por Elastic Beanstalk para ejecutar la aplicación Flask
"""
from kdi_back.api.main import create_app

# Elastic Beanstalk busca una variable llamada 'application'
application = create_app()

if __name__ == '__main__':
    application.run()

