import logging
from database.conexao_supabase import get_supabase_client, get_tenant_id

logger = logging.getLogger(__name__)

def criar_etapas_padrao(vaga_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    etapas = [
        {"tenant_id": tenant_id, "vaga_id": vaga_id, "titulo": "Entrevista RH", "ordem": 1, "responsavel_papel": "rh"},
        {"tenant_id": tenant_id, "vaga_id": vaga_id, "titulo": "Entrevista Gestor", "ordem": 2, "responsavel_papel": "gestor"},
    ]
    for etapa in etapas:
        client.table("etapas_entrevista").insert(etapa).execute()


def copiar_etapas_da_ficha(vaga_id, ficha_id):
    """
    BUG 1 FIX: Anteriormente a funcao ignorava o pipeline_personalizado e sempre
    criava etapas padrao, tornando o recurso de ficha com pipeline completamente inoperante.

    pipeline_personalizado e um BOOLEAN na tabela fichas_tecnicas.
    - False (ou null): cria as etapas padrao simples (RH + Gestor).
    - True: marca a vaga como pre_definido e cria as etapas padrao como base.
      NOTA TECNICA: Para suportar etapas personalizadas reais por ficha, sera necessario
      criar uma tabela `etapas_ficha` (migration futura) e copiar suas linhas aqui.
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    ficha = client.table("fichas_tecnicas").select("*").eq("id", ficha_id).eq("tenant_id", tenant_id).limit(1).execute()
    if not ficha.data:
        return criar_etapas_padrao(vaga_id)

    pipeline_personalizado = ficha.data[0].get("pipeline_personalizado")

    if pipeline_personalizado:
        # Ficha marcada com pipeline personalizado: atualiza flag na vaga
        # e cria as etapas padrao como baseline (ponto de partida para customizacao).
        client.table("vagas").update({"pipeline_tipo": "pre_definido"}).eq("id", vaga_id).eq("tenant_id", tenant_id).execute()
    else:
        # Ficha sem pipeline personalizado: usa etapas padrao e pipeline manual.
        client.table("vagas").update({"pipeline_tipo": "manual"}).eq("id", vaga_id).eq("tenant_id", tenant_id).execute()

    criar_etapas_padrao(vaga_id)


def get_etapas_da_vaga(vaga_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    result = client.table("etapas_entrevista").select("*").eq("vaga_id", vaga_id).eq("tenant_id", tenant_id).order("ordem", desc=False).execute()
    return result.data if result.data else []


def adicionar_etapa(vaga_id, titulo, descricao="", responsavel_papel=None):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()
    ultima = client.table("etapas_entrevista").select("ordem").eq("vaga_id", vaga_id).eq("tenant_id", tenant_id).order("ordem", desc=True).limit(1).execute()
    prox_ordem = (ultima.data[0]["ordem"] + 1) if ultima.data else 1
    payload = {
        "tenant_id": tenant_id,
        "vaga_id": vaga_id,
        "titulo": titulo,
        "descricao": descricao,
        "ordem": prox_ordem,
        "responsavel_papel": responsavel_papel,
    }
    result = client.table("etapas_entrevista").insert(payload).execute()
    return result.data[0] if result.data else None


def remover_etapa(etapa_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("etapas_entrevista").delete().eq("id", etapa_id).eq("tenant_id", tenant_id).execute()


def get_etapa_by_id(etapa_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()
    result = client.table("etapas_entrevista").select("*").eq("id", etapa_id).eq("tenant_id", tenant_id).limit(1).execute()
    return result.data[0] if result.data else None


def iniciar_entrevistas_candidato(candidatura_id, vaga_id, agendado_para=None):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    cid = str(candidatura_id)
    vid = str(vaga_id)

    existentes = client.table("entrevistas_candidato").select("id, etapa_id, status").eq("candidatura_id", cid).eq("tenant_id", tenant_id).execute()
    if existentes.data:
        ids = [r["id"] for r in existentes.data]
        if agendado_para:
            primeiro = None
            for r in existentes.data:
                if r.get("status") in ("pendente", "agendado"):
                    primeiro = r
                    break
            if primeiro:
                client.table("entrevistas_candidato").update({
                    "status": "agendado",
                    "agendado_para": agendado_para,
                }).eq("id", primeiro["id"]).eq("tenant_id", tenant_id).execute()
        client.table("candidaturas").update({"status": "Em_Entrevistas", "updated_at": "now()"}).eq("id", cid).eq("tenant_id", tenant_id).execute()
        return ids

    etapas = client.table("etapas_entrevista").select("*").eq("vaga_id", vid).eq("tenant_id", tenant_id).order("ordem", desc=False).execute()
    if not etapas.data:
        criar_etapas_padrao(vid)
        etapas = client.table("etapas_entrevista").select("*").eq("vaga_id", vid).eq("tenant_id", tenant_id).order("ordem", desc=False).execute()

    client.table("entrevistas_candidato").delete().eq("candidatura_id", cid).eq("tenant_id", tenant_id).execute()

    ids = []
    for i, etapa in enumerate(etapas.data):
        payload = {
            "candidatura_id": cid,
            "etapa_id": etapa["id"],
            "tenant_id": tenant_id,
            "status": "agendado" if (agendado_para and i == 0) else "pendente",
        }
        if agendado_para and i == 0:
            payload["agendado_para"] = agendado_para
        result = client.table("entrevistas_candidato").insert(payload).execute()
        inserted_id = result.data[0]["id"] if result.data else None
        if inserted_id:
            ids.append(inserted_id)
        else:
            query = client.table("entrevistas_candidato").select("id").eq("candidatura_id", cid).eq("etapa_id", etapa["id"]).eq("tenant_id", tenant_id).limit(1).execute()
            if query.data:
                ids.append(query.data[0]["id"])

    if ids:
        client.table("candidaturas").update({"status": "Em_Entrevistas", "updated_at": "now()"}).eq("id", cid).eq("tenant_id", tenant_id).execute()

    return ids


def get_progresso_candidato(candidatura_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    result = client.table("entrevistas_candidato").select("*, etapas_entrevista!entrevistas_candidato_etapa_id_fkey(titulo, ordem, responsavel_papel)").eq("candidatura_id", candidatura_id).eq("tenant_id", tenant_id).order("ordem", desc=False, foreign_table="etapas_entrevista").execute()
    return result.data if result.data else []


def avancar_etapa(entrevista_id, status, feedback="", entrevistador_id=None):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    payload = {
        "status": status,
        "realizado_em": "now()",
    }
    if feedback:
        payload["feedback"] = feedback
    if entrevistador_id:
        payload["entrevistador_id"] = entrevistador_id
    client.table("entrevistas_candidato").update(payload).eq("id", entrevista_id).eq("tenant_id", tenant_id).execute()

    entrevista = client.table("entrevistas_candidato").select("*, etapas_entrevista!inner(vaga_id, ordem)").eq("id", entrevista_id).eq("tenant_id", tenant_id).limit(1).execute()
    if not entrevista.data:
        return

    vaga_id = entrevista.data[0]["etapas_entrevista"]["vaga_id"]
    candidatura_id = entrevista.data[0]["candidatura_id"]

    if status == "reprovado":
        client.table("candidaturas").update({"status": "Reprovado", "updated_at": "now()"}).eq("id", candidatura_id).eq("tenant_id", tenant_id).execute()
        from models.notificacao import notificar_candidato_reprovado
        vaga_info = client.table("vagas").select("id, titulo").eq("id", vaga_id).eq("tenant_id", tenant_id).limit(1).execute()
        cand_info = client.table("candidaturas").select("nome").eq("id", candidatura_id).limit(1).execute()
        if vaga_info.data and cand_info.data:
            notificar_candidato_reprovado(
                {"id": vaga_id, "titulo": vaga_info.data[0].get("titulo", "")},
                cand_info.data[0].get("nome", ""),
                candidatura_id
            )
        return

    if status == "aprovado":
        etapas = client.table("etapas_entrevista").select("id").eq("vaga_id", vaga_id).eq("tenant_id", tenant_id).order("ordem", desc=False).execute()
        total = len(etapas.data or [])
        ordens = [e["etapas_entrevista"]["ordem"] for e in client.table("entrevistas_candidato").select("*, etapas_entrevista!inner(ordem)").eq("candidatura_id", candidatura_id).eq("tenant_id", tenant_id).eq("status", "aprovado").execute().data or []]
        if len(ordens) >= total:
            client.table("candidaturas").update({"status": "Aprovado_Entrevistas", "updated_at": "now()"}).eq("id", candidatura_id).eq("tenant_id", tenant_id).execute()
            from models.notificacao import notificar_candidato_aprovado
            vaga_info = client.table("vagas").select("id, titulo").eq("id", vaga_id).eq("tenant_id", tenant_id).limit(1).execute()
            cand_info = client.table("candidaturas").select("nome").eq("id", candidatura_id).limit(1).execute()
            if vaga_info.data and cand_info.data:
                notificar_candidato_aprovado(
                    {"id": vaga_id, "titulo": vaga_info.data[0].get("titulo", "")},
                    cand_info.data[0].get("nome", ""),
                    candidatura_id
                )


def get_vagas_com_selecionados():
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    result = client.table("candidaturas").select("vaga_id").eq("tenant_id", tenant_id).eq("status", "Selecionado").execute()
    return list(set(row["vaga_id"] for row in (result.data or []) if row.get("vaga_id")))

def get_candidatos_selecionados(vaga_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    result = client.table("candidaturas").select("*, candidatos!candidaturas_candidato_id_fkey(nome, email)").eq("vaga_id", vaga_id).eq("tenant_id", tenant_id).eq("status", "Selecionado").order("nota", desc=True).execute()

    data = result.data if result.data else []
    for row in data:
        cand = row.pop("candidatos", {}) or {}
        row["nome"] = cand.get("nome", "")
        row["email"] = cand.get("email", "")
    return data

def get_candidatos_em_entrevista(vaga_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    result = client.table("candidaturas").select("*, candidatos!candidaturas_candidato_id_fkey(nome, email)").eq("vaga_id", vaga_id).eq("tenant_id", tenant_id).in_("status", ["Em_Entrevistas", "Aprovado_Entrevistas"]).order("nota", desc=True).execute()

    data = result.data if result.data else []
    for row in data:
        cand = row.pop("candidatos", {}) or {}
        row["nome"] = cand.get("nome", "")
        row["email"] = cand.get("email", "")
        row["progresso"] = get_progresso_candidato(row["id"])
    return data


def get_candidatos_pipeline_por_vaga(vaga_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return {"etapas": [], "colunas": {}}
    client = get_supabase_client()

    etapas = client.table("etapas_entrevista").select("*").eq("vaga_id", vaga_id).eq("tenant_id", tenant_id).order("ordem", desc=False).execute()
    etapas = etapas.data or []

    candidaturas = client.table("candidaturas").select("*, candidatos!candidaturas_candidato_id_fkey(nome, email)").eq("vaga_id", vaga_id).eq("tenant_id", tenant_id).in_("status", ["Selecionado", "Em_Entrevistas", "Aprovado_Entrevistas", "Reprovado", "Contratado", "Banco_Talentos"]).order("nota", desc=True).execute()
    candidaturas = candidaturas.data or []

    colunas = {}
    for etapa in etapas:
        colunas[f"etapa_{etapa['id']}"] = {"id": f"etapa_{etapa['id']}", "tipo": "etapa", "etapa": etapa, "candidatos": []}
    colunas["aprovado"] = {"id": "aprovado", "tipo": "final", "titulo": "Aprovado", "icone": "fa-check-circle", "cor": "emerald", "candidatos": []}
    colunas["reprovado"] = {"id": "reprovado", "tipo": "final", "titulo": "Reprovado", "icone": "fa-xmark-circle", "cor": "red", "candidatos": []}
    colunas["banco_talentos"] = {"id": "banco_talentos", "tipo": "final", "titulo": "Banco de Talentos", "icone": "fa-star", "cor": "amber", "candidatos": []}
    colunas["contratado"] = {"id": "contratado", "tipo": "final", "titulo": "Contratado", "icone": "fa-handshake", "cor": "blue", "candidatos": []}

    for c in candidaturas:
        cand = c.pop("candidatos", {}) or {}
        c["nome"] = cand.get("nome", "")
        c["email"] = cand.get("email", "")

        progresso = client.table("entrevistas_candidato").select("*, etapas_entrevista!entrevistas_candidato_etapa_id_fkey(titulo, ordem)").eq("candidatura_id", c["id"]).eq("tenant_id", tenant_id).order("etapa_id", desc=False).execute()
        c["progresso"] = progresso.data or []

        c["pendente_entrevista_id"] = None
        for p in c["progresso"]:
            if p["status"] in ("pendente", "agendado"):
                c["pendente_entrevista_id"] = p["id"]
                break

        coluna_id = None
        if c["status"] == "Selecionado":
            continue
        elif c["status"] == "Contratado":
            coluna_id = "contratado"
        elif c["status"] == "Reprovado":
            coluna_id = "reprovado"
        elif c["status"] == "Banco_Talentos":
            coluna_id = "banco_talentos"
        elif c["status"] == "Aprovado_Entrevistas":
            coluna_id = "aprovado"
        else:
            etapa_atual_id = None
            tem_reprovado = False
            for p in c["progresso"]:
                if p["status"] in ("pendente", "agendado", "realizado") and etapa_atual_id is None:
                    etapa_atual_id = p["etapa_id"]
                if p["status"] == "reprovado":
                    tem_reprovado = True
            if tem_reprovado:
                coluna_id = "reprovado"
            elif etapa_atual_id:
                coluna_id = f"etapa_{etapa_atual_id}"
            elif c["progresso"]:
                coluna_id = "aprovado"

        if coluna_id and coluna_id in colunas:
            colunas[coluna_id]["candidatos"].append(c)

    return {"etapas": etapas, "colunas": colunas}

def agendar_entrevista(entrevista_id, agendado_para):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("entrevistas_candidato").update({"status": "agendado", "agendado_para": agendado_para}).eq("id", entrevista_id).eq("tenant_id", tenant_id).execute()


def get_agendamentos():
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    result = client.table("entrevistas_candidato") \
        .select("*, etapas_entrevista!entrevistas_candidato_etapa_id_fkey(*)") \
        .eq("tenant_id", tenant_id) \
        .eq("status", "agendado") \
        .not_.is_("agendado_para", "null") \
        .order("agendado_para", desc=False) \
        .execute()
    data = result.data or []
    from models.candidatura import get_candidatura_by_id
    out = []
    for row in data:
        etapa = row.pop("etapas_entrevista", {}) or {}
        cand = get_candidatura_by_id(row.get("candidatura_id"))
        out.append({
            "id": row["id"],
            "candidatura_id": row["candidatura_id"],
            "status": row["status"],
            "feedback": row.get("feedback"),
            "agendado_para": row.get("agendado_para"),
            "realizado_em": row.get("realizado_em"),
            "entrevistador_id": row.get("entrevistador_id"),
            "etapa_titulo": etapa.get("titulo", ""),
            "etapa_ordem": etapa.get("ordem", 0),
            "responsavel_papel": etapa.get("responsavel_papel", ""),
            "candidato_nome": cand.get("nome", "") if cand else "",
            "candidato_email": cand.get("email", "") if cand else "",
            "vaga_id": cand.get("vaga_id", "") if cand else "",
            "vaga_titulo": cand.get("titulo_vaga", "") if cand else "",
        })
    return out


def reagendar_entrevista(entrevista_id, agendado_para):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("entrevistas_candidato").update({
        "status": "agendado",
        "agendado_para": agendado_para,
    }).eq("id", entrevista_id).eq("tenant_id", tenant_id).execute()
