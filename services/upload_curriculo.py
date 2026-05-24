import os
import time
import uuid
from werkzeug.utils import secure_filename
from database.conexao_supabase import get_supabase_client

BUCKET_NAME = "curriculos"
UPLOAD_DIR = "upload_curriculos"

def upload_curriculo(file_storage):
    """
    Faz upload de um currículo PDF para o Supabase Storage.
    Retorna a URL pública ou caminho no storage.
    """
    if not file_storage or file_storage.filename == '':
        return None
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    filename = secure_filename(file_storage.filename)
    safe_filename = f"{int(time.time())}_{uuid.uuid4().hex[:8]}_{filename}"
    
    local_path = os.path.join(UPLOAD_DIR, safe_filename)
    file_storage.save(local_path)
    
    try:
        client = get_supabase_client()
        
        with open(local_path, "rb") as f:
            file_content = f.read()
        
        result = client.storage.from_(BUCKET_NAME).upload(
            path=safe_filename,
            file=file_content,
            file_options={"content_type": "application/pdf"}
        )
        
        os.remove(local_path)
        
        return safe_filename
        
    except Exception as e:
        print(f"Erro ao fazer upload para Supabase Storage: {e}")
        return None

def get_curriculo_url(file_path, expires_in=3600):
    """
    Gera uma URL signed (temporária) para download do currículo.
    """
    if not file_path:
        return None
    
    try:
        client = get_supabase_client()
        result = client.storage.from_(BUCKET_NAME).create_signed_url(
            file_path, 
            expires_in
        )
        return result.get("signed_url")
    except Exception as e:
        print(f"Erro ao gerar URL signed: {e}")
        return None

def delete_curriculo(file_path):
    """
    Remove o currículo do Supabase Storage.
    """
    if not file_path:
        return True
    
    try:
        client = get_supabase_client()
        client.storage.from_(BUCKET_NAME).remove([file_path])
        return True
    except Exception as e:
        print(f"Erro ao remover arquivo: {e}")
        return False