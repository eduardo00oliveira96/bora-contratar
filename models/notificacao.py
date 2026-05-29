import threading
import logging
from database.conexao_supabase import get_supabase_client, get_tenant_id
from flask import url_for
from services.email_service import enviar_email, montar_corpo_email

logger = logging.getLogger(__name__)


def criar_notificacao(usuario_id, vaga_id, tipo, titulo, mensagem=None):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()
    payload = {
        "tenant_id": tenant_id,
        "usuario_id": usuario_id,
        "vaga_id": vaga_id,
        "tipo": tipo,
        "titulo": titulo,
        "mensagem": mensagem,
    }
    result = client.table("notificacoes").insert(payload).execute()
    return result.data[0] if result.data else None


def listar_notificacoes(usuario_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    result = client.table("notificacoes") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .eq("usuario_id", usuario_id) \
        .order("created_at", desc=True) \
        .limit(50) \
        .execute()
    return result.data or []


def notificacoes_nao_lidas(usuario_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return 0
    client = get_supabase_client()
    result = client.table("notificacoes") \
        .select("id", count="exact") \
        .eq("tenant_id", tenant_id) \
        .eq("usuario_id", usuario_id) \
        .eq("lida", False) \
        .execute()
    return result.count or 0


def marcar_como_lida(notificacao_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("notificacoes") \
        .update({"lida": True}) \
        .eq("id", notificacao_id) \
        .eq("tenant_id", tenant_id) \
        .execute()


def marcar_todas_como_lidas(usuario_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("notificacoes") \
        .update({"lida": True}) \
        .eq("tenant_id", tenant_id) \
        .eq("usuario_id", usuario_id) \
        .eq("lida", False) \
        .execute()


def _notificar_com_email(usuario, vaga_id, tipo, titulo, mensagem):
    criar_notificacao(usuario["id"], vaga_id, tipo, titulo, mensagem)
    if usuario.get("email"):
        link = url_for("solicitacao.detalhes", id=vaga_id, _external=True)
        corpo = montar_corpo_email(titulo, mensagem or "", "", link)
        enviar_email(usuario["email"], f"[Bora Contratar] {titulo}", corpo)


def notificar_gestor(vaga, tipo, titulo, mensagem=None):
    from models.usuario import buscar_usuario_por_id

    gestor_id = vaga.get("criado_por")
    if not gestor_id:
        return

    gestor = buscar_usuario_por_id(gestor_id)
    if not gestor:
        return

    _notificar_com_email(gestor, vaga.get("id"), tipo, titulo, mensagem)


def notificar_rh(vaga, tipo, titulo, mensagem=None):
    from models.usuario import listar_usuarios_do_tenant

    tenant_id = get_tenant_id()
    if not tenant_id:
        return

    usuarios = listar_usuarios_do_tenant(tenant_id)
    for u in usuarios:
        if u.get("papel") in ("admin", "rh", "superadmin") and u.get("id") != vaga.get("criado_por"):
            _notificar_com_email(u, vaga.get("id"), tipo, titulo, mensagem)


def notificar_aprovadores(vaga, tipo, titulo, mensagem=None):
    from models.solicitacao import get_aprovadores_da_solicitacao

    aprovacoes = get_aprovadores_da_solicitacao(vaga.get("id"))
    for aprovacao in aprovacoes:
        usuario_data = aprovacao.get("usuarios") or {}
        user_id = aprovacao.get("usuario_id")
        if not user_id:
            continue
        criar_notificacao(user_id, vaga.get("id"), tipo, titulo, mensagem)
        if usuario_data.get("email"):
            link = url_for("solicitacao.detalhes", id=vaga.get("id"), _external=True)
            corpo = montar_corpo_email(titulo, mensagem or "", vaga.get("titulo", ""), link)
            enviar_email(usuario_data["email"], f"[Bora Contratar] {titulo}", corpo)


def notificar_entrevista_agendada(vaga, candidato_nome, entrevista_id, agendado_para, candidatura_id):
    from models.usuario import listar_usuarios_do_tenant

    tenant_id = get_tenant_id()
    if not tenant_id:
        return

    data_str = agendado_para[:16] if agendado_para and len(agendado_para) > 16 else (agendado_para or "")
    titulo = "Entrevista agendada"
    mensagem = f"{candidato_nome} — {data_str.replace('T', ' às ')}"

    usuarios = listar_usuarios_do_tenant(tenant_id)
    for u in usuarios:
        if u.get("papel") in ("admin", "rh", "superadmin", "gestor"):
            link = url_for("entrevista.candidato_progresso", id=candidatura_id, _external=True)
            criar_notificacao(u["id"], vaga.get("id"), "entrevista_agendada", titulo, mensagem)
            if u.get("email"):
                corpo = montar_corpo_email(titulo, mensagem, vaga.get("titulo", ""), link)
                enviar_email(u["email"], f"[Bora Contratar] {titulo}", corpo)


def notificar_entrevista_reagendada(vaga, candidato_nome, entrevista_id, nova_data, candidatura_id):
    from models.usuario import listar_usuarios_do_tenant

    tenant_id = get_tenant_id()
    if not tenant_id:
        return

    data_str = nova_data[:16] if nova_data and len(nova_data) > 16 else (nova_data or "")
    titulo = "Entrevista reagendada"
    mensagem = f"{candidato_nome} — nova data: {data_str.replace('T', ' às ')}"

    usuarios = listar_usuarios_do_tenant(tenant_id)
    for u in usuarios:
        if u.get("papel") in ("admin", "rh", "superadmin", "gestor"):
            link = url_for("entrevista.candidato_progresso", id=candidatura_id, _external=True)
            criar_notificacao(u["id"], vaga.get("id"), "entrevista_reagendada", titulo, mensagem)
            if u.get("email"):
                corpo = montar_corpo_email(titulo, mensagem, vaga.get("titulo", ""), link)
                enviar_email(u["email"], f"[Bora Contratar] {titulo}", corpo)


def notificar_candidato_aprovado(vaga, candidato_nome, candidatura_id):
    from models.usuario import listar_usuarios_do_tenant

    tenant_id = get_tenant_id()
    if not tenant_id:
        return

    titulo = "Candidato aprovado nas entrevistas"
    mensagem = f"{candidato_nome} foi aprovado em todas as etapas de entrevista"

    usuarios = listar_usuarios_do_tenant(tenant_id)
    for u in usuarios:
        if u.get("papel") in ("admin", "rh", "superadmin", "gestor"):
            link = url_for("entrevista.candidato_progresso", id=candidatura_id, _external=True)
            criar_notificacao(u["id"], vaga.get("id"), "candidato_aprovado", titulo, mensagem)
            if u.get("email"):
                corpo = montar_corpo_email(titulo, mensagem, vaga.get("titulo", ""), link)
                enviar_email(u["email"], f"[Bora Contratar] {titulo}", corpo)


def notificar_candidato_reprovado(vaga, candidato_nome, candidatura_id):
    from models.usuario import listar_usuarios_do_tenant

    tenant_id = get_tenant_id()
    if not tenant_id:
        return

    titulo = "Candidato reprovado"
    mensagem = f"{candidato_nome} foi reprovado em uma etapa de entrevista"

    usuarios = listar_usuarios_do_tenant(tenant_id)
    for u in usuarios:
        if u.get("papel") in ("admin", "rh", "superadmin", "gestor"):
            link = url_for("entrevista.candidato_progresso", id=candidatura_id, _external=True)
            criar_notificacao(u["id"], vaga.get("id"), "candidato_reprovado", titulo, mensagem)
            if u.get("email"):
                corpo = montar_corpo_email(titulo, mensagem, vaga.get("titulo", ""), link)
                enviar_email(u["email"], f"[Bora Contratar] {titulo}", corpo)


def notificar_candidato_contratado(vaga, candidato_nome, candidatura_id):
    from models.usuario import listar_usuarios_do_tenant

    tenant_id = get_tenant_id()
    if not tenant_id:
        return

    titulo = "Candidato contratado"
    mensagem = f"{candidato_nome} foi contratado para a vaga"

    usuarios = listar_usuarios_do_tenant(tenant_id)
    for u in usuarios:
        if u.get("papel") in ("admin", "rh", "superadmin", "gestor"):
            link = url_for("entrevista.candidato_progresso", id=candidatura_id, _external=True)
            criar_notificacao(u["id"], vaga.get("id"), "candidato_contratado", titulo, mensagem)
            if u.get("email"):
                corpo = montar_corpo_email(titulo, mensagem, vaga.get("titulo", ""), link)
                enviar_email(u["email"], f"[Bora Contratar] {titulo}", corpo)
