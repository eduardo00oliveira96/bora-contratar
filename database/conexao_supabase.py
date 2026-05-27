import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

_supabase: Client = None

def get_supabase_client() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase

TENANT_SLUG_PADRAO = "bora-contratar"

def get_tenant_id() -> str:
    client = get_supabase_client()
    result = client.table("tenants").select("id").eq("slug", TENANT_SLUG_PADRAO).limit(1).execute()
    if result.data:
        return result.data[0]["id"]
    return None

def supabase_select(table: str, columns: str = "*", filters: dict = None, order_by: str = None, ascending: bool = False):
    client = get_supabase_client()
    query = client.table(table).select(columns)
    if filters:
        for key, value in filters.items():
            query = query.eq(key, value)
    if order_by:
        query = query.order(order_by, desc=not ascending)
    return query.execute()

def supabase_insert(table: str, data: dict):
    client = get_supabase_client()
    return client.table(table).insert(data).execute()

def supabase_update(table: str, data: dict, filters: dict):
    client = get_supabase_client()
    query = client.table(table).update(data)
    for key, value in filters.items():
        query = query.eq(key, value)
    return query.execute()

def supabase_delete(table: str, filters: dict):
    client = get_supabase_client()
    query = client.table(table).delete()
    for key, value in filters.items():
        query = query.eq(key, value)
    return query.execute()

def supabase_upload_file(bucket: str, file_path: str, file_content: bytes, content_type: str = "application/pdf"):
    client = get_supabase_client()
    return client.storage.from_(bucket).upload(
        path=file_path,
        file=file_content,
        file_options={"content-type": content_type}
    )

def supabase_get_signed_url(bucket: str, file_path: str, expires_in: int = 3600):
    client = get_supabase_client()
    result = client.storage.from_(bucket).create_signed_url(file_path, expires_in)
    return result.get("signedURL")
