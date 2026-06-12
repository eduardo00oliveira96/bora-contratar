import json
import ast
import requests
from flask import Blueprint, render_template, request, flash, redirect, url_for, g, Response
from src.decorators import login_required, role_required
from models.vaga import get_vaga_by_id, iniciar_entrevistas_vaga
from models.candidatura import get_candidatura_by_id, contratar_candidato, mover_banco_talentos
from services.upload_curriculo import get_curriculo_url
from models.entrevista import (
    get_etapas_da_vaga, adicionar_etapa, remover_etapa,
    iniciar_entrevistas_candidato, get_progresso_candidato,
    avancar_etapa, get_etapa_by_id, agendar_entrevista,
    copiar_etapas_da_ficha,
    get_candidatos_pipeline_por_vaga,
    get_candidatos_selecionados,
    get_agendamentos,
    reagendar_entrevista,
)
from models.notificacao import notificar_entrevista_agendada, notificar_entrevista_reagendada

entrevista_bp = Blueprint('entrevista', __name__, url_prefix='/entrevistas')


@entrevista_bp.route('/vaga/<uuid:id>')
@login_required
def pipeline(id):
    vaga = get_vaga_by_id(str(id))
    if not vaga:
        flash("Vaga não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))

    pipeline_data = get_candidatos_pipeline_por_vaga(str(id))
    selecionados = get_candidatos_selecionados(str(id))

    return render_template('admin/entrevistas/kanban.html',
                         vaga=vaga, pipeline_data=pipeline_data,
                         selecionados=selecionados)


@entrevista_bp.route('/agenda')
@login_required
@role_required('admin', 'rh', 'superadmin', 'gestor')
def agenda():
    agendamentos = get_agendamentos()
    from collections import defaultdict
    from datetime import datetime
    hoje_str = datetime.now().strftime('%Y-%m-%d')
    
    grupos = defaultdict(list)
    for a in agendamentos:
        dia = (a.get("agendado_para") or "")[:10]
        grupos[dia].append(a)
        
    return render_template('admin/entrevistas/agenda.html',
                         grupos=dict(grupos),
                         total=len(agendamentos),
                         hoje_str=hoje_str)


@entrevista_bp.route('/vaga/<uuid:id>/configurar', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def configurar(id):
    vaga = get_vaga_by_id(str(id))
    if not vaga:
        flash("Vaga não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))

    acao = request.form.get('acao')

    if acao == 'iniciar_entrevistas':
        if vaga.get("status_vaga") == "publicada":
            iniciar_entrevistas_vaga(str(id))
        flash("Vaga movida para fase de Entrevistas.", "success")

    elif acao == 'copiar_da_ficha':
        from models.ficha_tecnica import get_ficha_by_id
        from models.entrevista import copiar_etapas_da_ficha, criar_etapas_padrao
        ficha_id = vaga.get("ficha_tecnica_id")
        if ficha_id:
            ficha = get_ficha_by_id(ficha_id)
            if ficha and ficha.get("pipeline_personalizado"):
                copiar_etapas_da_ficha(str(id), ficha_id)
                flash("Pipeline copiado da ficha técnica.", "success")
            else:
                criar_etapas_padrao(str(id))
                flash("Etapas padrão (RH + Gestor) criadas com base na ficha.", "success")
        else:
            criar_etapas_padrao(str(id))
            flash("Etapas padrão (RH + Gestor) criadas.", "success")

    elif acao == 'adicionar_etapa':
        titulo = request.form.get('titulo')
        if titulo:
            adicionar_etapa(str(id), titulo,
                          request.form.get('descricao', ''),
                          request.form.get('responsavel_papel'))
            flash("Etapa adicionada.", "success")

    return redirect(url_for('entrevista.pipeline', id=id))


@entrevista_bp.route('/etapa/<uuid:id>/remover', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def remover_etapa_route(id):
    etapa = get_etapa_by_id(str(id))
    if not etapa:
        flash("Etapa não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))
    vaga_id = etapa["vaga_id"]
    remover_etapa(str(id))
    flash("Etapa removida.", "success")
    return redirect(url_for('entrevista.pipeline', id=vaga_id))


@entrevista_bp.route('/candidatura/<uuid:id>')
@login_required
def candidato_progresso(id):
    candidato = get_candidatura_by_id(str(id))
    if not candidato:
        flash("Candidatura não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))

    progresso = get_progresso_candidato(str(id))
    vaga = get_vaga_by_id(candidato.get("vaga_id"))
    etapas = get_etapas_da_vaga(candidato.get("vaga_id"))

    etapa_atual = None
    for p in progresso:
        if p["status"] == "realizado":
            etapa_atual = p
            break
    if not etapa_atual:
        for p in progresso:
            if p["status"] in ("pendente", "agendado"):
                etapa_atual = p
                break
    if not etapa_atual and progresso:
        etapa_atual = progresso[-1]

    def _parse_json_list(val):
        if not val:
            return []
        if isinstance(val, list):
            return val
        for fn in (json.loads, ast.literal_eval):
            try:
                return fn(val)
            except:
                continue
        return []

    fortes = _parse_json_list(candidato.get("pontos_fortes"))
    gaps = _parse_json_list(candidato.get("gaps_atencao"))

    return render_template('admin/entrevistas/candidato.html',
                         candidato=candidato, progresso=progresso, vaga=vaga,
                         etapas=etapas, etapa_atual=etapa_atual,
                         fortes=fortes, gaps=gaps)


@entrevista_bp.route('/candidatura/<uuid:id>/vista')
@login_required
def candidato_vista(id):
    candidato = get_candidatura_by_id(str(id))
    if not candidato:
        return "", 404

    vaga = get_vaga_by_id(candidato.get("vaga_id"))

    def _parse_json_list(val):
        if not val:
            return []
        if isinstance(val, list):
            return val
        for fn in (json.loads, ast.literal_eval):
            try:
                return fn(val)
            except:
                continue
        return []

    fortes = _parse_json_list(candidato.get("pontos_fortes"))
    gaps = _parse_json_list(candidato.get("gaps_atencao"))

    return render_template('admin/entrevistas/candidato_vista.html',
                         candidato=candidato, vaga=vaga,
                         fortes=fortes, gaps=gaps)


@entrevista_bp.route('/candidatura/<uuid:id>/curriculo')
@login_required
def candidato_curriculo(id):
    candidato = get_candidatura_by_id(str(id))
    if not candidato or not candidato.get('link_curriculo'):
        return "", 404

    url = get_curriculo_url(candidato['link_curriculo'])
    if not url:
        return "", 502

    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            return "", 502
        return Response(r.content, mimetype='application/pdf',
                       headers={'Content-Disposition': 'inline'})
    except:
        return "", 502


@entrevista_bp.route('/candidatura/<uuid:id>/iniciar', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def iniciar_por_candidato(id):
    candidato = get_candidatura_by_id(str(id))
    if not candidato:
        flash("Candidatura não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))

    vaga_id = candidato.get("vaga_id")
    agendado_para = request.form.get('agendado_para', '') or None

    if not agendado_para:
        flash("Informe a data/hora para agendar a entrevista.", "warning")
        return redirect(url_for('entrevista.pipeline', id=vaga_id))

    ids_criados = iniciar_entrevistas_candidato(str(id), vaga_id, agendado_para)

    if not ids_criados:
        flash("Erro ao iniciar entrevistas. O candidato pode já estar em andamento.", "error")
        return redirect(url_for('entrevista.pipeline', id=vaga_id))

    flash(f"Candidato {candidato.get('nome', '')} agendado e movido para entrevistas.", "success")

    vaga_obj = get_vaga_by_id(vaga_id)
    notificar_entrevista_agendada(
        {"id": vaga_id, "titulo": (vaga_obj.get("titulo") if vaga_obj else "")},
        candidato.get("nome", ""), ids_criados[0], agendado_para, str(id)
    )

    return redirect(url_for('entrevista.pipeline', id=vaga_id))


@entrevista_bp.route('/entrevista/<uuid:id>/avancar', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def avancar_etapa_route(id):
    status = request.form.get('status')
    feedback = request.form.get('feedback', '')
    if status not in ("realizado", "aprovado", "reprovado"):
        flash("Status inválido.", "error")
        return redirect(url_for('admin.dashboard'))

    entrevista = None
    client = __import__('database.conexao_supabase', fromlist=['get_supabase_client'])
    from database.conexao_supabase import get_supabase_client, get_tenant_id
    tenant_id = get_tenant_id()
    if tenant_id:
        client_sup = get_supabase_client()
        result = client_sup.table("entrevistas_candidato").select("*, etapas_entrevista!inner(vaga_id)").eq("id", str(id)).eq("tenant_id", tenant_id).limit(1).execute()
        if result.data:
            entrevista = result.data[0]

    if not entrevista:
        flash("Registro de entrevista não encontrado.", "error")
        return redirect(url_for('admin.dashboard'))

    vaga_id = entrevista["etapas_entrevista"]["vaga_id"]
    usuario_id = g.usuario.get("id")
    avancar_etapa(str(id), status, feedback, usuario_id)

    if status == "aprovado" or status == "realizado":
        flash("Etapa registrada com sucesso!", "success")
    elif status == "reprovado":
        flash("Candidato reprovado nesta etapa.", "info")

    return redirect(url_for('entrevista.pipeline', id=vaga_id))


@entrevista_bp.route('/entrevista/<uuid:id>/agendar', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def agendar_entrevista_route(id):
    agendado_para = request.form.get('agendado_para')
    if not agendado_para:
        flash("Informe a data/hora do agendamento.", "warning")
        return redirect(request.referrer or url_for('admin.dashboard'))

    entrevista = None
    from database.conexao_supabase import get_supabase_client, get_tenant_id
    tenant_id = get_tenant_id()
    if tenant_id:
        client_sup = get_supabase_client()
        result = client_sup.table("entrevistas_candidato").select("*, etapas_entrevista!inner(vaga_id)").eq("id", str(id)).eq("tenant_id", tenant_id).limit(1).execute()
        if result.data:
            entrevista = result.data[0]

    if not entrevista:
        flash("Registro não encontrado.", "error")
        return redirect(url_for('admin.dashboard'))

    agendar_entrevista(str(id), agendado_para)

    from models.candidatura import get_candidatura_by_id
    cand = get_candidatura_by_id(entrevista.get("candidatura_id"))
    vaga = get_vaga_by_id(entrevista["etapas_entrevista"]["vaga_id"])
    if cand and vaga:
        notificar_entrevista_agendada(
            {"id": vaga["id"], "titulo": vaga.get("titulo", "")},
            cand.get("nome", ""), str(id), agendado_para, entrevista.get("candidatura_id")
        )

    flash("Entrevista agendada!", "success")
    return redirect(url_for('entrevista.pipeline', id=entrevista["etapas_entrevista"]["vaga_id"]))


@entrevista_bp.route('/entrevista/<uuid:id>/reagendar', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def reagendar_entrevista_route(id):
    agendado_para = request.form.get('agendado_para')
    if not agendado_para:
        return {"ok": False, "erro": "Data obrigatória"}, 400

    from database.conexao_supabase import get_supabase_client, get_tenant_id
    tenant_id = get_tenant_id()
    if not tenant_id:
        return {"ok": False, "erro": "Sem tenant"}, 400
    client_sup = get_supabase_client()
    result = client_sup.table("entrevistas_candidato").select("*, etapas_entrevista!entrevistas_candidato_etapa_id_fkey(vaga_id)").eq("id", str(id)).eq("tenant_id", tenant_id).limit(1).execute()
    if not result.data:
        return {"ok": False, "erro": "Entrevista não encontrada"}, 404

    reagendar_entrevista(str(id), agendado_para)

    entrevista = result.data[0]
    from models.candidatura import get_candidatura_by_id
    cand = get_candidatura_by_id(entrevista.get("candidatura_id"))
    vaga = get_vaga_by_id(entrevista["etapas_entrevista"]["vaga_id"])
    if cand and vaga:
        notificar_entrevista_reagendada(
            {"id": vaga["id"], "titulo": vaga.get("titulo", "")},
            cand.get("nome", ""), str(id), agendado_para, entrevista.get("candidatura_id")
        )

    return {"ok": True}


@entrevista_bp.route('/api/mover', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def kanban_mover():
    data = request.get_json()
    candidatura_id = data.get("candidatura_id")
    entrevista_id = data.get("entrevista_id")
    acao = data.get("acao")
    feedback = (data.get("feedback") or "").strip()

    if not candidatura_id or not acao:
        return {"ok": False, "erro": "Dados incompletos"}, 400

    if acao == "finalizar":
        if not entrevista_id:
            return {"ok": False, "erro": "entrevista_id necessário"}, 400
        if not feedback:
            return {"ok": False, "erro": "Feedback é obrigatório"}, 400
        usuario_id = g.usuario.get("id")
        avancar_etapa(str(entrevista_id), "realizado", feedback, usuario_id)

    elif acao == "aprovar":
        if not entrevista_id:
            return {"ok": False, "erro": "entrevista_id necessário"}, 400
        usuario_id = g.usuario.get("id")
        agendado_para = data.get("agendado_para")
        avancar_etapa(str(entrevista_id), "aprovado", feedback, usuario_id, agendado_para=agendado_para)
    elif acao == "reprovar":
        if not entrevista_id:
            return {"ok": False, "erro": "entrevista_id necessário"}, 400
        usuario_id = g.usuario.get("id")
        avancar_etapa(str(entrevista_id), "reprovado", feedback, usuario_id)
    elif acao == "talento":
        mover_banco_talentos(str(candidatura_id))
    elif acao == "contratar":
        if not feedback:
            return {"ok": False, "erro": "Feedback é obrigatório"}, 400
        from database.conexao_supabase import get_supabase_client, get_tenant_id
        tenant_id = get_tenant_id()
        if not tenant_id:
            return {"ok": False, "erro": "Sem tenant"}, 400
        client = get_supabase_client()
        c = client.table("candidaturas").select("vaga_id, status").eq("id", str(candidatura_id)).eq("tenant_id", tenant_id).limit(1).execute()
        if not c.data:
            return {"ok": False, "erro": "Candidatura não encontrada"}, 404
        if c.data[0].get("status") != "Aprovado_Entrevistas":
            return {"ok": False, "erro": "Só é possível contratar candidatos aprovados em todas as etapas"}, 400
        contratar_candidato(str(candidatura_id), c.data[0]["vaga_id"])
    else:
        return {"ok": False, "erro": "Ação inválida"}, 400

    return {"ok": True}


@entrevista_bp.route('/vaga/<uuid:id>/contratar/<uuid:candidatura_id>', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def contratar(id, candidatura_id):
    vaga = get_vaga_by_id(str(id))
    if not vaga:
        flash("Vaga não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))

    ok = contratar_candidato(str(candidatura_id), str(id))
    if ok:
        flash("Candidato contratado! Vaga concluída.", "success")
    else:
        flash("Não foi possível contratar. Verifique se o candidato está aprovado em todas as etapas.", "warning")
    return redirect(url_for('admin.dashboard'))
