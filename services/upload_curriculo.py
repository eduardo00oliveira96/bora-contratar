import os
import time
import uuid
from werkzeug.utils import secure_filename
from database.conexao_supabase import get_supabase_client

BUCKET_NAME = "curriculos"
UPLOAD_DIR = "upload_curriculos"
ALLOWED_EXTENSIONS = {'.pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024


def upload_curriculo(file_storage):
    if not file_storage or file_storage.filename == '':
        return None

    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return None

    file_content = file_storage.read()
    if len(file_content) > MAX_FILE_SIZE:
        return None

    if file_content[:4] != b'%PDF':
        return None

    file_storage.seek(0)

    filename = secure_filename(file_storage.filename)
    safe_filename = f"{int(time.time())}_{uuid.uuid4().hex[:8]}_{filename}"

    try:
        client = get_supabase_client()
        client.storage.from_(BUCKET_NAME).upload(
            path=safe_filename,
            file=file_content,
            file_options={"content-type": "application/pdf"}
        )
        return safe_filename
    except Exception as e:
        print(f"Erro ao fazer upload para Supabase Storage: {e}")
        return None


def get_curriculo_url(file_path, expires_in=3600):
    if not file_path:
        return None
    try:
        client = get_supabase_client()
        result = client.storage.from_(BUCKET_NAME).create_signed_url(
            file_path,
            expires_in
        )
        return result.get("signedURL")
    except Exception as e:
        print(f"Erro ao gerar URL signed: {e}")
        return None


def delete_curriculo(file_path):
    if not file_path:
        return True
    try:
        client = get_supabase_client()
        client.storage.from_(BUCKET_NAME).remove([file_path])
        return True
    except Exception as e:
        print(f"Erro ao remover arquivo: {e}")
        return False
