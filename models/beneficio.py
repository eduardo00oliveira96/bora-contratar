from database.conexao_supabase import get_supabase_client, get_tenant_id

def listar_beneficios():
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    result = client.table("beneficios").select("*").eq("tenant_id", tenant_id).order("nome", desc=False).execute()
    return result.data if result.data else []

def get_beneficio_by_id(beneficio_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()
    result = client.table("beneficios").select("*").eq("id", beneficio_id).eq("tenant_id", tenant_id).limit(1).execute()
    return result.data[0] if result.data else None

def criar_beneficio(nome):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()
    payload = {"tenant_id": tenant_id, "nome": nome}
    result = client.table("beneficios").insert(payload).execute()
    return result.data[0] if result.data else None

def atualizar_beneficio(beneficio_id, nome):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("beneficios").update({"nome": nome}).eq("id", beneficio_id).eq("tenant_id", tenant_id).execute()

def excluir_beneficio(beneficio_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("beneficios").delete().eq("id", beneficio_id).eq("tenant_id", tenant_id).execute()
