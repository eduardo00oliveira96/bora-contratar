from database.conexao_supabase import get_supabase_client, get_tenant_id


def _sanitizar(valor):
    if isinstance(valor, str):
        return valor.replace("\u0000", "").strip()
    return valor


def create_candidatura(data):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()
    payload = {
        "tenant_id": tenant_id,
        "vaga_id": data.get("vaga_id"),
        "candidato_id": data.get("candidato_id"),
        "resumo": _sanitizar(data.get("resumo", "")),
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

def selecionar_candidato(candidatura_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("candidaturas").update({"status": "Selecionado", "updated_at": "now()"}).eq("id", candidatura_id).eq("tenant_id", tenant_id).execute()

def update_candidatura_status(candidatura_id, status):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("candidaturas").update({"status": status, "updated_at": "now()"}).eq("id", candidatura_id).eq("tenant_id", tenant_id).execute()


def contratar_candidato(candidatura_id, vaga_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return False
    client = get_supabase_client()
    candidatura = client.table("candidaturas").select("status, nome").eq("id", candidatura_id).eq("tenant_id", tenant_id).limit(1).execute()
    if not candidatura.data or candidatura.data[0]["status"] != "Aprovado_Entrevistas":
        return False
    client.table("candidaturas").update({"status": "Contratado", "updated_at": "now()"}).eq("id", candidatura_id).eq("tenant_id", tenant_id).execute()
    client.table("vagas").update({
        "status_vaga": "concluida",
        "candidatura_contratada_id": candidatura_id,
        "data_conclusao": "now()",
        "ativo": False,
        "updated_at": "now()",
    }).eq("id", vaga_id).eq("tenant_id", tenant_id).execute()
    # BUG 2 FIX: Notificacao SMTP isolada ? falhas de e-mail nunca revertem a contratacao.
    import logging as _lg
    _log = _lg.getLogger(__name__)
    try:
        from models.notificacao import notificar_candidato_contratado
        from models.vaga import get_vaga_by_id
        vaga = get_vaga_by_id(vaga_id)
        if vaga:
            notificar_candidato_contratado(
                {"id": vaga_id, "titulo": vaga.get("titulo", "")},
                candidatura.data[0].get("nome", ""),
                candidatura_id
            )
    except Exception as _smtp_err:
        _log.error(f"Falha ao notificar contratacao {candidatura_id}: {_smtp_err}", exc_info=True)
    return True

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
        "resumo": _sanitizar(data.get("resumo", "")),
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

def update_candidatura_erro(candidatura_id, mensagem_erro=""):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    payload = {
        "status": "Erro na Avaliação",
        "analise_detalhada": mensagem_erro or "Falha na avaliação por IA.",
        "updated_at": "now()",
    }
    client.table("candidaturas").update(payload).eq("id", candidatura_id).eq("tenant_id", tenant_id).execute()

def reset_candidatura_ai_eval(candidatura_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    payload = {
        "status": "Pendente",
        "nota": None,
        "analise_detalhada": None,
        "pontos_fortes": None,
        "gaps_atencao": None,
        "recomendacao": None,
        "tags": None,
        "updated_at": "now()",
    }
    client.table("candidaturas").update(payload).eq("id", candidatura_id).eq("tenant_id", tenant_id).execute()

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


def mover_banco_talentos(candidatura_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("candidaturas").update({"status": "Banco_Talentos", "updated_at": "now()"}).eq("id", candidatura_id).eq("tenant_id", tenant_id).execute()

def update_observacoes_rh(candidatura_id, texto):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("candidaturas").update({"observacoes_rh": texto, "updated_at": "now()"}).eq("id", candidatura_id).eq("tenant_id", tenant_id).execute()

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


def get_banco_talentos():
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    # Busca candidaturas cujo status é 'Banco_Talentos'
    result = client.table("candidaturas").select("*, candidatos!candidaturas_candidato_id_fkey(*), vagas!candidaturas_vaga_id_fkey(titulo)").eq("tenant_id", tenant_id).eq("status", "Banco_Talentos").order("updated_at", desc=True).execute()

    data = result.data if result.data else []
    for row in data:
        cand = row.pop("candidatos", {}) or {}
        vg = row.pop("vagas", {}) or {}
        row["nome"] = cand.get("nome", "")
        row["cpf"] = cand.get("cpf", "")
        row["telefone"] = cand.get("telefone", "")
        row["email_candidato"] = cand.get("email", "")
        row["titulo_vaga"] = vg.get("titulo", "—")
        
        # Faz parse das tags que vêm como string "['Python', 'Django']" do Supabase
        tags_str = row.get("tags")
        if tags_str:
            try:
                import ast
                parsed = ast.literal_eval(tags_str)
                if isinstance(parsed, list):
                    row["tags_lista"] = parsed
                else:
                    row["tags_lista"] = [str(parsed)]
            except Exception:
                row["tags_lista"] = [t.strip() for t in tags_str.replace("[","").replace("]","").replace("'","").replace("\"","").split(",") if t.strip()]
        else:
            row["tags_lista"] = []
    return data


def vincular_candidato_a_vaga(candidatura_id, nova_vaga_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()

    # Busca a candidatura de origem no banco de talentos
    old_cand = get_candidatura_by_id(candidatura_id)
    if not old_cand:
        return None

    # Evita duplicidade de candidatura para o mesmo candidato na mesma vaga
    existing = client.table("candidaturas").select("id").eq("tenant_id", tenant_id).eq("vaga_id", nova_vaga_id).eq("candidato_id", old_cand.get("candidato_id")).limit(1).execute()
    if existing.data:
        return existing.data[0]["id"]

    # Cria nova candidatura herdando toda a análise de IA prévia
    payload = {
        "tenant_id": tenant_id,
        "vaga_id": nova_vaga_id,
        "candidato_id": old_cand.get("candidato_id"),
        "resumo": old_cand.get("resumo", ""),
        "link_curriculo": old_cand.get("link_curriculo", ""),
        "status": "Avaliado",
        "nota": old_cand.get("nota"),
        "analise_detalhada": old_cand.get("analise_detalhada"),
        "pontos_fortes": old_cand.get("pontos_fortes"),
        "gaps_atencao": old_cand.get("gaps_atencao"),
        "recomendacao": old_cand.get("recomendacao"),
        "tags": old_cand.get("tags"),
        "etapa_entrevista": "Pré Análise com IA",
    }

    result = client.table("candidaturas").insert(payload).execute()
    if result.data:
        return result.data[0]["id"]
    return None


def get_candidaturas_pendentes_reprocessar(horas=2):
    """
    Bug 3 Fix: Detecta candidaturas travadas em status Pendente com curriculo extraido,
    sintoma de threads de IA mortas silenciosamente apos reinicio do servidor.
    O admin pode usar esta funcao para reprocessar em lote via painel.
    """
    import logging
    logger = logging.getLogger(__name__)
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    try:
        result = client.table("candidaturas") \
            .select("*, candidatos!candidaturas_candidato_id_fkey(nome, email), vagas!candidaturas_vaga_id_fkey(titulo)") \
            .eq("tenant_id", tenant_id) \
            .eq("status", "Pendente") \
            .not_.is_("resumo", "null") \
            .lt("created_at", f"now() - interval '{horas} hours'") \
            .order("created_at", desc=False) \
            .execute()
        data = result.data if result.data else []
        for row in data:
            cand = row.pop("candidatos", {}) or {}
            vg = row.pop("vagas", {}) or {}
            row["nome"] = cand.get("nome", "")
            row["email_candidato"] = cand.get("email", "")
            row["titulo_vaga"] = vg.get("titulo", "?")
        return data
    except Exception as e:
        logger.error(f"Erro ao buscar candidaturas pendentes: {e}", exc_info=True)
        return []
