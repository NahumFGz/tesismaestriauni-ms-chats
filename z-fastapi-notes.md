# fastapi-py-practice

# Python 3.10

- Formas de ejecución - por consola
  uvicorn NOMBRE_FICHERO:app --reload

  app es el nombre de la instancia de FastAPI
  --reload reinicia el servidor si detecta cambios (solo para desarrollo)

- agregando un main
  uvicorn.run("project_01:app", host="127.0.0.1", port=8000, reload=True)

- usando fastapi-cli
  fastapi run "nombre-fichero"
  fastapi dev "nombre-fichero"

- Librerias iniciales
  pip install fastapi uvicorn pip-chill

- Para poder usar el cli + fastapi
  pip install "fastapi[standard]"

- Instalar ORM
  pip install SQLAlchemy

- Instalar herramienta de migraciones
  pip install alembic

- Instalar cifrado
  pip install passlib
  pip install bcrypt==4.0.1

- Instalar librería para manejar datos de tipo multipart/form-data
  pip install python-multipart

- JWT
  pip install "python-jose[cryptography]"

- Generar caracteres random
  openssl rand -hex 32

# Alembic -> Herramienta de migraciones

- Instalación
  pip install alembic

- Comandos básicos
  alembic init <folder_name> -> Inicializes a new, generic enviroment
  alembic revision -m <message> -> Creates a new revision of the enviroment
  alembic upgrade <revision#> -> Run or upgrade migration to out database
  alembic downgrade -1 -> Run our downgrade migration to our database
  alembic revision --autogenerate -m <message>
  alembic upgrade head
