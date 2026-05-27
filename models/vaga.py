from database.conexao_supabase import get_supabase_client, get_tenant_id

def get_all_vagas(active_only=False, papel=None, usuario_id=None):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    query = client.table("vagas").select("*").eq("tenant_id", tenant_id)

    if papel == "gestor" and usuario_id:
        query = query.eq("gestor_owner_id", usuario_id)
    elif papel == "rh":
        pass
    elif active_only:
        query = query.eq("status_vaga", "publicada")

    query = query.order("created_at", desc=True)
    result = query.execute()
    return result.data if result.data else []

def get_vaga_by_id(vaga_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()
    result = client.table("vagas").select("*").eq("id", vaga_id).eq("tenant_id", tenant_id).limit(1).execute()
    return result.data[0] if result.data else None

def create_vaga(data):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()

    papel = data.get("papel_criador", "rh")
    status_vaga = "solicitada" if papel == "gestor" else "rascunho"

    payload = {
        "tenant_id": tenant_id,
        "titulo": data.get("titulo"),
        "descricao": data.get("descricao"),
        "local_trabalho": data.get("local_trabalho"),
        "tipo_contrato": data.get("tipo_contrato") or data.get("contrato_trabalho"),
        "requisitos": data.get("requisitos"),
        "habilidades": data.get("habilidades"),
        "salario": data.get("salario"),
        "divulgar_salario": data.get("divulgar_salario") is not None,
        "beneficios": data.get("beneficios"),
        "user_created": data.get("user_created", "Admin"),
        "criado_por": data.get("criado_por"),
        "gestor_owner_id": data.get("gestor_owner_id"),
        "status_vaga": status_vaga,
    }
    result = client.table("vagas").insert(payload).execute()
    if result.data:
        return result.data[0]["id"]
    return None

def update_vaga(vaga_id, data):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    payload = {
        "titulo": data.get("titulo"),
        "descricao": data.get("descricao"),
        "local_trabalho": data.get("local_trabalho"),
        "tipo_contrato": data.get("tipo_contrato") or data.get("contrato_trabalho"),
        "requisitos": data.get("requisitos"),
        "habilidades": data.get("habilidades"),
        "salario": data.get("salario"),
        "divulgar_salario": data.get("divulgar_salario") is not None,
        "beneficios": data.get("beneficios"),
        "updated_at": "now()",
    }
    client.table("vagas").update(payload).eq("id", vaga_id).eq("tenant_id", tenant_id).execute()

def close_vaga(vaga_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("vagas").update({"ativo": False, "status_vaga": "encerrada", "updated_at": "now()"}).eq("id", vaga_id).eq("tenant_id", tenant_id).execute()

def publicar_vaga(vaga_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("vagas").update({"status_vaga": "publicada", "ativo": True, "updated_at": "now()"}).eq("id", vaga_id).eq("tenant_id", tenant_id).execute()

def get_vagas_solicitadas():
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    result = client.table("vagas").select("*").eq("tenant_id", tenant_id).eq("status_vaga", "solicitada").order("created_at", desc=True).execute()
    return result.data if result.data else []

# ===== NOVO FLUXO DE SOLICITAÇÃO =====

def criar_solicitacao(data):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()
    payload = {
        "tenant_id": tenant_id,
        "titulo": data.get("titulo"),
        "user_created": data.get("user_created", "Gestor"),
        "criado_por": data.get("criado_por"),
        "gestor_owner_id": data.get("gestor_owner_id"),
        "tipo_solicitacao": data.get("tipo_solicitacao"),
        "justificativa": data.get("justificativa"),
        "centro_custo": data.get("centro_custo"),
        "previsao_inicio": data.get("previsao_inicio"),
        "ficha_tecnica_link": data.get("ficha_tecnica_link"),
        "status_vaga": "solicitada",
    }
    result = client.table("vagas").insert(payload).execute()
    if result.data:
        return result.data[0]["id"]
    return None

def preencher_ficha_tecnica(vaga_id, data):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    payload = {k: v for k, v in data.items() if v is not None and v != ""}
    if not payload:
        return
    payload["updated_at"] = "now()"
    client.table("vagas").update(payload).eq("id", vaga_id).eq("tenant_id", tenant_id).execute()

def triar_solicitacao(vaga_id, parecer_rh, observacoes=""):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    payload = {
        "parecer_rh": parecer_rh,
        "observacoes_rh": observacoes,
        "updated_at": "now()",
    }
    if parecer_rh == "validada":
        payload["status_vaga"] = "em_triagem"
    elif parecer_rh == "ajustes":
        payload["status_vaga"] = "solicitada"
    elif parecer_rh == "reprovada_rh":
        payload["status_vaga"] = "encerrada"
        payload["ativo"] = False
    client.table("vagas").update(payload).eq("id", vaga_id).eq("tenant_id", tenant_id).execute()

def encaminhar_para_aprovacao(vaga_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("vagas").update({"status_vaga": "aguardando_aprovacao", "updated_at": "now()"}).eq("id", vaga_id).eq("tenant_id", tenant_id).execute()

def atualizar_status_vaga(vaga_id, status, extra=None):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    payload = {"status_vaga": status, "updated_at": "now()"}
    if extra:
        payload.update(extra)
    if status == "encerrada":
        payload["ativo"] = False
    client.table("vagas").update(payload).eq("id", vaga_id).eq("tenant_id", tenant_id).execute()

def get_solicitacoes_por_papel(papel, usuario_id, tenant_id=None):
    if not tenant_id:
        tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    query = client.table("vagas").select("*").eq("tenant_id", tenant_id)

    if papel == "gestor":
        query = query.eq("gestor_owner_id", usuario_id)
    elif papel == "aprovador":
        vagas_com_aprovacao = client.table("aprovacoes_solicitacao").select("vaga_id").eq("usuario_id", usuario_id).eq("parecer", "pendente").execute()
        vaga_ids = [r["vaga_id"] for r in vagas_com_aprovacao.data] if vagas_com_aprovacao.data else []
        if vaga_ids:
            query = query.in_("id", vaga_ids)
        else:
            return []

    query = query.order("created_at", desc=True)
    result = query.execute()
    return result.data if result.data else []

def get_solicitacoes_em_triagem():
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    result = client.table("vagas").select("*").eq("tenant_id", tenant_id).eq("status_vaga", "em_triagem").order("created_at", desc=True).execute()
    return result.data if result.data else []

def get_solicitacoes_aguardando_aprovacao():
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    result = client.table("vagas").select("*").eq("tenant_id", tenant_id).eq("status_vaga", "aguardando_aprovacao").order("created_at", desc=True).execute()
    return result.data if result.data else []

def get_solicitacoes_aprovadas():
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    result = client.table("vagas").select("*").eq("tenant_id", tenant_id).in_("status_vaga", ["aprovada", "aprovada_ressalvas", "em_recrutamento"]).order("created_at", desc=True).execute()
    return result.data if result.data else []

def get_all_vagas_status(status_list):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    result = client.table("vagas").select("*").eq("tenant_id", tenant_id).in_("status_vaga", status_list).order("created_at", desc=True).execute()
    return result.data if result.data else []
