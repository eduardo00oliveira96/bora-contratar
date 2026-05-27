from database.conexao_supabase import get_supabase_client, get_tenant_id

def criar_ou_buscar_candidato(data):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()
    cpf = data.get("cpf", "")

    if cpf:
        existing = client.table("candidatos").select("*").eq("tenant_id", tenant_id).eq("cpf", cpf).limit(1).execute()
        if existing.data:
            return existing.data[0]["id"]

    payload = {
        "tenant_id": tenant_id,
        "nome": data.get("nome"),
        "cpf": cpf,
        "telefone": data.get("telefone"),
        "email": data.get("email"),
    }
    result = client.table("candidatos").insert(payload).execute()
    if result.data:
        return result.data[0]["id"]
    return None

def get_candidato_by_cpf(cpf):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()
    result = client.table("candidatos").select("*").eq("tenant_id", tenant_id).eq("cpf", cpf).limit(1).execute()
    return result.data[0] if result.data else None
