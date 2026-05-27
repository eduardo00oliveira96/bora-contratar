from database.conexao_supabase import get_supabase_client, get_tenant_id

def adicionar_aprovador(vaga_id, usuario_id, ordem=1):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()
    payload = {
        "vaga_id": vaga_id,
        "usuario_id": usuario_id,
        "ordem_aprovacao": ordem,
    }
    result = client.table("aprovacoes_solicitacao").insert(payload).execute()
    return result.data[0] if result.data else None

def remover_aprovador(aprovacao_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("aprovacoes_solicitacao").delete().eq("id", aprovacao_id).execute()

def get_aprovadores_da_solicitacao(vaga_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return []
    client = get_supabase_client()
    result = client.table("aprovacoes_solicitacao").select("*, usuarios!aprovacoes_solicitacao_usuario_id_fkey(nome, email, papel)").eq("vaga_id", vaga_id).order("ordem_aprovacao", desc=False).execute()
    return result.data if result.data else []

def registrar_parecer_aprovador(aprovacao_id, parecer, observacoes=""):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return
    client = get_supabase_client()
    client.table("aprovacoes_solicitacao").update({
        "parecer": parecer,
        "observacoes": observacoes,
        "respondido_em": "now()",
    }).eq("id", aprovacao_id).execute()

def verificar_status_aprovacao(vaga_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return "pendente"
    client = get_supabase_client()
    result = client.table("aprovacoes_solicitacao").select("parecer").eq("vaga_id", vaga_id).execute()
    aprovacoes = result.data if result.data else []
    if not aprovacoes:
        return "sem_aprovadores"

    todos_responderam = all(a["parecer"] != "pendente" for a in aprovacoes)
    if not todos_responderam:
        return "pendente"

    tem_reprovado = any(a["parecer"] == "reprovado" for a in aprovacoes)
    if tem_reprovado:
        return "reprovado"

    tem_ressalvas = any(a["parecer"] == "aprovado_ressalvas" for a in aprovacoes)
    if tem_ressalvas:
        return "aprovado_ressalvas"

    return "aprovado"

def get_aprovacao_pendente(vaga_id, usuario_id):
    tenant_id = get_tenant_id()
    if not tenant_id:
        return None
    client = get_supabase_client()
    result = client.table("aprovacoes_solicitacao").select("*").eq("vaga_id", vaga_id).eq("usuario_id", usuario_id).eq("parecer", "pendente").limit(1).execute()
    return result.data[0] if result.data else None

def listar_aprovadores_disponiveis(tenant_id):
    client = get_supabase_client()
    result = client.table("usuarios").select("id, nome, email").eq("tenant_id", tenant_id).eq("papel", "aprovador").eq("ativo", True).order("nome", desc=False).execute()
    return result.data if result.data else []
