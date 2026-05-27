from database.conexao_supabase import get_supabase_client, get_tenant_id

def criar_usuario(data):
    client = get_supabase_client()
    payload = {
        "tenant_id": data["tenant_id"],
        "auth_user_id": data.get("auth_user_id"),
        "nome": data["nome"],
        "email": data["email"],
        "papel": data["papel"],
        "ativo": data.get("ativo", True),
    }
    result = client.table("usuarios").insert(payload).execute()
    return result.data[0] if result.data else None

def buscar_usuario_por_auth(auth_user_id):
    client = get_supabase_client()
    result = client.table("usuarios").select("*, tenants(nome, slug)").eq("auth_user_id", auth_user_id).limit(1).execute()
    return result.data[0] if result.data else None

def buscar_usuario_por_email(email):
    client = get_supabase_client()
    result = client.table("usuarios").select("*").eq("email", email).limit(1).execute()
    return result.data[0] if result.data else None

def listar_usuarios_do_tenant(tenant_id):
    client = get_supabase_client()
    result = client.table("usuarios").select("*").eq("tenant_id", tenant_id).order("created_at", desc=True).execute()
    return result.data if result.data else []

def buscar_usuario_por_id(usuario_id):
    client = get_supabase_client()
    result = client.table("usuarios").select("*").eq("id", usuario_id).limit(1).execute()
    return result.data[0] if result.data else None

def atualizar_usuario(usuario_id, data):
    client = get_supabase_client()
    client.table("usuarios").update(data).eq("id", usuario_id).execute()

def listar_tenants():
    client = get_supabase_client()
    result = client.table("tenants").select("*").order("created_at", desc=True).execute()
    return result.data if result.data else []

def criar_tenant(data):
    client = get_supabase_client()
    result = client.table("tenants").insert(data).execute()
    return result.data[0] if result.data else None
