from database.conexao_supabase import get_supabase_client, get_tenant_id

def create_candidatura(data):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()
    payload = {
        "tenant_id": tenant_id,
        "vaga_id": data.get("vaga_id"),
        "candidato_id": data.get("candidato_id"),
        "resumo": data.get("resumo", ""),
        "link_curriculo": data.get("link_curriculo", ""),
    }
    result = client.table("candidaturas").insert(payload).execute()
    if result.data:
        return result.data[0]["id"]
    return None

def update_candidatura_ai_eval(candidatura_id, nota, analise, fortes, gaps, recomendacao, tags=""):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    payload = {
        "status": "Avaliado",
        "nota": nota,
        "analise_detalhada": analise,
        "pontos_fortes": fortes,
        "gaps_atencao": gaps,
        "recomendacao": recomendacao,
        "tags": tags,
        "etapa_entrevista": "Pré Análise com IA",
        "updated_at": "now()",
    }
    client.table("candidaturas").update(payload).eq("id", candidatura_id).eq("tenant_id", tenant_id).execute()

def get_candidaturas_by_vaga(vaga_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    result = client.table("candidaturas").select("*, candidatos!candidaturas_candidato_id_fkey(*)").eq("vaga_id", vaga_id).eq("tenant_id", tenant_id).order("nota", desc=True).execute()
    return result.data if result.data else []

def get_candidatura_by_id(candidatura_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()
    result = client.table("candidaturas").select("*, candidatos!candidaturas_candidato_id_fkey(*), vagas!candidaturas_vaga_id_fkey(titulo)").eq("id", candidatura_id).eq("tenant_id", tenant_id).limit(1).execute()
    if result.data:
        row = result.data[0]
        candidato = row.pop("candidatos", {}) or {}
        vaga = row.pop("vagas", {}) or {}
        row["nome"] = candidato.get("nome", "")
        row["cpf"] = candidato.get("cpf", "")
        row["telefone"] = candidato.get("telefone", "")
        row["email"] = candidato.get("email", "")
        row["titulo_vaga"] = vaga.get("titulo", "")
        return row
    return None

def update_candidatura_status(candidatura_id, status):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("candidaturas").update({"status": status, "updated_at": "now()"}).eq("id", candidatura_id).eq("tenant_id", tenant_id).execute()

def get_candidatura_by_cpf(cpf, vaga_id=None):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()

    if vaga_id:
        result = client.table("candidaturas").select("*, candidatos!candidaturas_candidato_id_fkey(*)").eq("vaga_id", vaga_id).eq("tenant_id", tenant_id).execute()
        for row in result.data or []:
            candidato = row.get("candidatos") or {}
            if candidato.get("cpf") == cpf:
                row["nome"] = candidato.get("nome", "")
                row["cpf"] = candidato.get("cpf", "")
                row["telefone"] = candidato.get("telefone", "")
                row["email"] = candidato.get("email", "")
                return row

    result = client.table("candidaturas").select("*, candidatos!candidaturas_candidato_id_fkey(*)").eq("tenant_id", tenant_id).order("created_at", desc=True).execute()
    for row in result.data or []:
        candidato = row.get("candidatos") or {}
        if candidato.get("cpf") == cpf:
            row["nome"] = candidato.get("nome", "")
            row["cpf"] = candidato.get("cpf", "")
            row["telefone"] = candidato.get("telefone", "")
            row["email"] = candidato.get("email", "")
            return row
    return None

def update_candidatura_info(candidatura_id, data):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    payload = {
        "link_curriculo": data.get("link_curriculo", ""),
        "resumo": data.get("resumo", ""),
        "updated_at": "now()",
    }
    client.table("candidaturas").update(payload).eq("id", candidatura_id).eq("tenant_id", tenant_id).execute()

    candidato_id = data.get("candidato_id")
    if candidato_id:
        cand_payload = {}
        if data.get("nome"):
            cand_payload["nome"] = data["nome"]
        if data.get("telefone"):
            cand_payload["telefone"] = data["telefone"]
        if data.get("email"):
            cand_payload["email"] = data["email"]
        if cand_payload:
            client.table("candidatos").update(cand_payload).eq("id", candidato_id).eq("tenant_id", tenant_id).execute()

def get_all_candidaturas():
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    result = client.table("candidaturas").select("*, candidatos!candidaturas_candidato_id_fkey(*)").eq("tenant_id", tenant_id).order("created_at", desc=True).execute()

    data = result.data if result.data else []
    for row in data:
        cand = row.pop("candidatos", {}) or {}
        row["nome"] = cand.get("nome", "")
        row["cpf"] = cand.get("cpf", "")
        row["telefone"] = cand.get("telefone", "")
        row["email_candidato"] = cand.get("email", "")
    return data


def get_all_candidaturas_with_vaga():
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    result = client.table("candidaturas").select("*, candidatos!candidaturas_candidato_id_fkey(*), vagas!candidaturas_vaga_id_fkey(titulo)").eq("tenant_id", tenant_id).order("created_at", desc=True).execute()

    data = result.data if result.data else []
    for row in data:
        cand = row.pop("candidatos", {}) or {}
        vg = row.pop("vagas", {}) or {}
        row["nome"] = cand.get("nome", "")
        row["cpf"] = cand.get("cpf", "")
        row["telefone"] = cand.get("telefone", "")
        row["email_candidato"] = cand.get("email", "")
        row["titulo_vaga"] = vg.get("titulo", "—")
    return data
