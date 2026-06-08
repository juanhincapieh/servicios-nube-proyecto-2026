"""
Lambda - Punto 4: insertar un estudiante en la RDS PostgreSQL.

La app web (lambda/form.tsx -> api/sendForm2Db) hace POST con JSON:
  { "nombre", "apellido", "fecha_nacimiento", "direccion",
    "correo_electronico", "carrera" }
y esta funcion lo INSERTA en la tabla public.estudiante.

Esta Lambda corre DENTRO de la VPC (subredes privadas) para alcanzar la RDS.
Usa pg8000 (driver PostgreSQL en Python puro: no requiere compilar ni layer).

Variables de entorno:
  - DB_HOST     : endpoint de la RDS (sin puerto)
  - DB_PORT     : 9876
  - DB_NAME     : nexacloud
  - DB_USER     : usuario maestro
  - DB_PASSWORD : password maestro
"""

import json
import os
import ssl
import base64
import pg8000.native

DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ.get("DB_PORT", "9876"))
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]

# Contexto SSL permisivo (equivale al rejectUnauthorized:false que usa la app)
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


def lambda_handler(event, context):
    try:
        raw = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            raw = base64.b64decode(raw).decode("utf-8")
        data = json.loads(raw)

        conn = pg8000.native.Connection(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            ssl_context=_ssl_ctx,
        )
        conn.run(
            """
            INSERT INTO public.estudiante
                (nombre, apellido, fecha_nacimiento, direccion, correo_electronico, carrera)
            VALUES
                (:nombre, :apellido, :fecha_nacimiento, :direccion, :correo, :carrera)
            """,
            nombre=data.get("nombre"),
            apellido=data.get("apellido"),
            fecha_nacimiento=data.get("fecha_nacimiento"),
            direccion=data.get("direccion"),
            correo=data.get("correo_electronico"),
            carrera=data.get("carrera"),
        )
        conn.close()

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Estudiante insertado con exito"}),
        }
    except Exception as e:  # noqa
        print("ERROR:", str(e))
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)}),
        }
