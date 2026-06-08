"""
Lambda - Punto 3: extraer imagenes de un bucket S3 privado.

La app web (imagesBucket/page.tsx) hace GET a esta funcion (via API Gateway)
y espera JSON:  { "images": ["<url>", "<url>", ...] }  para usar como <img src>.

Como el bucket es PRIVADO (regla del enunciado), devolvemos URLs PREFIRMADAS
(presigned): acceso temporal de solo lectura sin exponer el bucket.

CLAVE: forzamos el endpoint REGIONAL (endpoint_url=https://s3.<region>.amazonaws.com)
para que el host de la URL coincida con la region de la firma. Si no, boto3 puede
resolver el endpoint global (us-east-1) mientras firma para us-east-2 -> esa
discrepancia provoca SignatureDoesNotMatch.

Variables de entorno:
  - BUCKET_NAME : nombre del bucket (requerida)
  - URL_EXPIRES : segundos de validez de la presigned URL (opcional, default 3600)
"""

import json
import os
import boto3
from botocore.config import Config

BUCKET = os.environ["BUCKET_NAME"]
REGION = os.environ.get("AWS_REGION", "us-east-2")
EXPIRES = int(os.environ.get("URL_EXPIRES", "3600"))

s3 = boto3.client(
    "s3",
    region_name=REGION,
    endpoint_url=f"https://s3.{REGION}.amazonaws.com",
    config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
)


def lambda_handler(event, context):
    try:
        urls = []
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=BUCKET):
            for obj in sorted(page.get("Contents", []), key=lambda o: o["Key"]):
                key = obj["Key"]
                if key.endswith("/"):
                    continue
                urls.append(
                    s3.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": BUCKET, "Key": key},
                        ExpiresIn=EXPIRES,
                    )
                )

        print(f"generadas {len(urls)} presigned URLs (region={REGION})")
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"images": urls}),
        }
    except Exception as e:  # noqa
        print("ERROR:", str(e))
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"images": [], "error": str(e)}),
        }
