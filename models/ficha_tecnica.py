from database.conexao_supabase import get_supabase_client, get_tenant_id

def listar_fichas(apenas_ativas=True):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    query = client.table("fichas_tecnicas").select("*").eq("tenant_id", tenant_id)
    if apenas_ativas:
        query = query.eq("ativo", True)
    query = query.order("titulo", desc=False)
    result = query.execute()
    return result.data if result.data else []

def get_ficha_by_id(ficha_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()
    result = client.table("fichas_tecnicas").select("*").eq("id", ficha_id).eq("tenant_id", tenant_id).limit(1).execute()
    return result.data[0] if result.data else None

def criar_ficha(data):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()
    payload = {
        "tenant_id": tenant_id,
        "titulo": data.get("titulo"),
        "descricao": data.get("descricao"),
        "local_trabalho": data.get("local_trabalho"),
        "tipo_contrato": data.get("tipo_contrato") or data.get("contrato_trabalho"),
        "requisitos": data.get("requisitos"),
        "habilidades": data.get("habilidades"),
        "salario": data.get("salario"),
        "beneficios": data.get("beneficios"),
    }
    result = client.table("fichas_tecnicas").insert(payload).execute()
    return result.data[0] if result.data else None

def atualizar_ficha(ficha_id, data):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    payload = {k: v for k, v in data.items() if v is not None}
    payload["updated_at"] = "now()"
    client.table("fichas_tecnicas").update(payload).eq("id", ficha_id).eq("tenant_id", tenant_id).execute()

def arquivar_ficha(ficha_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("fichas_tecnicas").update({"ativo": False, "updated_at": "now()"}).eq("id", ficha_id).eq("tenant_id", tenant_id).execute()
