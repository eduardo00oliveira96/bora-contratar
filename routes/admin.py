import os
import json
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_from_directory, current_app, g
from src.decorators import login_required, role_required
from models.vaga import (
    get_all_vagas, get_vaga_by_id, create_vaga, update_vaga,
    close_vaga, publicar_vaga, get_vagas_solicitadas,
    get_solicitacoes_em_triagem, get_solicitacoes_aguardando_aprovacao,
    get_solicitacoes_aprovadas,     get_solicitacoes_por_papel,
    get_all_vagas_status, get_solicitacoes_ajustes_pendentes
)
from models.candidatura import get_candidaturas_by_vaga, get_candidatura_by_id, update_candidatura_status, get_all_candidaturas_with_vaga, contratar_candidato, selecionar_candidato, update_observacoes_rh, get_banco_talentos, vincular_candidato_a_vaga
from models.entrevista import get_etapas_da_vaga, iniciar_entrevistas_candidato
from models.usuario import listar_usuarios_do_tenant
from models.ficha_tecnica import listar_fichas, get_ficha_by_id, criar_ficha, atualizar_ficha, arquivar_ficha, get_ficha_beneficios, set_ficha_beneficios
from models.beneficio import listar_beneficios, get_beneficio_by_id, criar_beneficio, atualizar_beneficio, excluir_beneficio
from models.dashboard import get_kpis, get_vagas_por_status, get_candidatos_por_status, get_notas_distribuicao, get_vagas_por_mes, get_recentes
from services.upload_curriculo import get_curriculo_url

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@login_required
def dashboard():
    usuario = g.usuario
    papel = usuario.get("papel")
    usuario_id = usuario.get("id")

    vagas = get_all_vagas(papel=papel, usuario_id=usuario_id)

    vagas_solicitadas = []
    solicitacoes_triagem = []
    solicitacoes_aprovacao = []
    solicitacoes_aprovar = []

    if papel in ("admin", "rh", "superadmin"):
        vagas_solicitadas = get_vagas_solicitadas()
        solicitacoes_triagem = get_solicitacoes_em_triagem()
        solicitacoes_aprovacao = get_solicitacoes_aguardando_aprovacao()


    solicitacoes_ajustes = get_solicitacoes_ajustes_pendentes(usuario_id)

    if papel == "aprovador":
        solicitacoes_aprovar = get_solicitacoes_por_papel("aprovador", usuario_id)

    # Chart data
    kpis = get_kpis()
    vagas_por_status = get_vagas_por_status()
    candidatos_por_status = get_candidatos_por_status()
    notas_dist = get_notas_distribuicao()
    vagas_por_mes = get_vagas_por_mes()
    recentes_vagas, recentes_cands = get_recentes()

    return render_template('admin/dashboard.html',
                         vagas=vagas,
                         vagas_solicitadas=vagas_solicitadas,
                         solicitacoes_triagem=solicitacoes_triagem,
                         solicitacoes_aprovacao=solicitacoes_aprovacao,
                         solicitacoes_ajustes=solicitacoes_ajustes,
                         solicitacoes_aprovar=solicitacoes_aprovar,
                         kpis=kpis,
                         vagas_por_status=vagas_por_status,
                         candidatos_por_status=candidatos_por_status,
                         notas_dist=notas_dist,
                         vagas_por_mes=vagas_por_mes,
                         recentes_vagas=recentes_vagas,
                         recentes_cands=recentes_cands)


@admin_bp.route('/vagas')
@login_required
def vagas_listar():
    usuario = g.usuario
    vagas = get_all_vagas(papel=usuario.get("papel"), usuario_id=usuario.get("id"))
    return render_template('admin/vagas.html', vagas=vagas)


@admin_bp.route('/entrevistas')
@login_required
@role_required('admin', 'rh', 'superadmin')
def entrevistas_listar():
    from models.entrevista import get_candidatos_em_entrevista, get_candidatos_selecionados, get_etapas_da_vaga, get_vagas_com_selecionados
    vagas = get_all_vagas_status(['em_entrevistas'])
    vagas_existing_ids = {v["id"] for v in vagas}

    vagas_ids_selecionados = get_vagas_com_selecionados()
    for vaga_id in vagas_ids_selecionados:
        if vaga_id not in vagas_existing_ids:
            vaga = get_vaga_by_id(vaga_id)
            if vaga:
                vagas.append(vaga)
                vagas_existing_ids.add(vaga_id)

    from database.conexao_supabase import get_supabase_client, get_tenant_id
    tenant_id = get_tenant_id()
    if tenant_id:
        client = get_supabase_client()
        result = client.table("candidaturas").select("vaga_id").eq("tenant_id", tenant_id).in_("status", ["Em_Entrevistas", "Aprovado_Entrevistas"]).execute()
        for row in (result.data or []):
            vaga_id = row.get("vaga_id")
            if vaga_id and vaga_id not in vagas_existing_ids:
                vaga = get_vaga_by_id(vaga_id)
                if vaga:
                    vagas.append(vaga)
                    vagas_existing_ids.add(vaga_id)

    vagas_com_info = []
    for v in vagas:
        vaga_id = v["id"]
        v["candidatos_entrevista"] = len(get_candidatos_em_entrevista(vaga_id))
        v["candidatos_selecionados"] = len(get_candidatos_selecionados(vaga_id))
        v["etapas"] = len(get_etapas_da_vaga(vaga_id))
        v["tem_selecionados"] = v["candidatos_selecionados"] > 0
        vagas_com_info.append(v)
    return render_template('admin/entrevistas/lista.html', vagas=vagas_com_info)


@admin_bp.route('/candidaturas')
@login_required
def candidaturas_listar():
    candidaturas = get_all_candidaturas_with_vaga()
    return render_template('admin/candidaturas.html', candidaturas=candidaturas)


@admin_bp.route('/vaga/nova', methods=['GET', 'POST'])
@login_required
def vaga_nova():
    usuario = g.usuario
    if request.method == 'POST':
        data = {
            "titulo": request.form.get('titulo'),
            "descricao": request.form.get('descricao'),
            "local_trabalho": request.form.get('local_trabalho'),
            "contrato_trabalho": request.form.get('contrato_trabalho'),
            "requisitos": request.form.get('requisitos'),
            "habilidades": request.form.get('habilidades'),
            "salario": request.form.get('salario', type=float) if request.form.get('salario') else None,
            "divulgacao_salario": request.form.get('divulgacao_salario'),
            "beneficios": ",".join(request.form.getlist('beneficios')),
            "criado_por": usuario.get("id"),
            "gestor_owner_id": usuario.get("id") if usuario.get("papel") == "gestor" else None,
            "user_created": usuario.get("nome"),
            "papel_criador": usuario.get("papel"),
        }
        vaga_id = create_vaga(data)

        if usuario.get("papel") == "gestor":
            flash("Solicitação de vaga enviada para aprovação do RH!", "success")
        else:
            flash("Nova vaga criada com sucesso!", "success")

        return redirect(url_for('admin.dashboard'))

    return render_template('admin/vaga_form.html', vaga=None)


@admin_bp.route('/vaga/<uuid:id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def vaga_editar(id):
    vaga = get_vaga_by_id(str(id))
    if not vaga:
        flash("Vaga não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        data = {
            "titulo": request.form.get('titulo'),
            "descricao": request.form.get('descricao'),
            "local_trabalho": request.form.get('local_trabalho'),
            "contrato_trabalho": request.form.get('contrato_trabalho'),
            "requisitos": request.form.get('requisitos'),
            "habilidades": request.form.get('habilidades'),
            "salario": request.form.get('salario', type=float) if request.form.get('salario') else None,
            "divulgacao_salario": request.form.get('divulgacao_salario'),
            "beneficios": ",".join(request.form.getlist('beneficios')),
        }
        update_vaga(str(id), data)
        flash("Vaga atualizada com sucesso!", "success")
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/vaga_form.html', vaga=dict(vaga))


@admin_bp.route('/vaga/<uuid:id>/publicar', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def vaga_publicar(id):
    publicar_vaga(str(id))
    flash("Vaga publicada com sucesso!", "success")
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/vaga/<uuid:id>/encerrar', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def vaga_encerrar(id):
    close_vaga(str(id))
    flash("Vaga encerrada.", "warning")
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/vaga/<uuid:id>/candidatos')
@login_required
def vaga_candidatos(id):
    usuario = g.usuario
    vaga = get_vaga_by_id(str(id))
    if not vaga:
        flash("Vaga não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))

    if usuario.get("papel") == "gestor" and vaga.get("gestor_owner_id") != usuario.get("id"):
        flash("Você não tem permissão para ver candidatos desta vaga.", "error")
        return redirect(url_for('admin.dashboard'))

    candidatos = get_candidaturas_by_vaga(str(id))
    return render_template('admin/candidatos.html', vaga=vaga, candidatos=candidatos)


@admin_bp.route('/vaga/<uuid:id>/comparar')
@login_required
def vaga_comparar(id):
    vaga = get_vaga_by_id(str(id))
    if not vaga:
        flash("Vaga não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))

    candidatos = get_candidaturas_by_vaga(str(id))

    for c in candidatos:
        try:
            c['pontos_fortes_lista'] = json.loads(c['pontos_fortes']) if c.get('pontos_fortes') else []
        except:
            c['pontos_fortes_lista'] = []
        try:
            c['gaps_lista'] = json.loads(c['gaps_atencao']) if c.get('gaps_atencao') else []
        except:
            c['gaps_lista'] = []

    return render_template('admin/comparativo.html', vaga=vaga, candidatos=candidatos)


@admin_bp.route('/candidato/<uuid:id>', methods=['GET'])
@login_required
def candidato_detalhes(id):
    candidato = get_candidatura_by_id(str(id))
    if not candidato:
        flash("Candidato não encontrado.", "error")
        return redirect(url_for('admin.dashboard'))

    try:
        fortes = json.loads(candidato['pontos_fortes']) if candidato.get('pontos_fortes') else []
    except:
        fortes = []
    try:
        gaps = json.loads(candidato['gaps_atencao']) if candidato.get('gaps_atencao') else []
    except:
        gaps = []

    return render_template('admin/candidato_detalhes.html', candidato=candidato, fortes=fortes, gaps=gaps)


@admin_bp.route('/candidato/<uuid:id>/selecionar', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def candidato_selecionar(id):
    candidato = get_candidatura_by_id(str(id))
    if not candidato:
        flash("Candidatura não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))

    selecionar_candidato(str(id))
    flash(f"Candidato {candidato.get('nome', '')} selecionado! Configure o pipeline de entrevistas.", "success")
    return redirect(url_for('entrevista.pipeline', id=candidato.get('vaga_id')))


@admin_bp.route('/candidato/<uuid:id>/status', methods=['POST'])
@login_required
def candidato_status(id):
    status = request.form.get('status')
    candidato = get_candidatura_by_id(str(id))
    if status and candidato:
        update_candidatura_status(str(id), status)
        flash(f"Status atualizado para: {status}", "success")
        return redirect(url_for('admin.candidato_detalhes', id=id))
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/candidato/<uuid:id>/curriculo')
@login_required
def download_cv(id):
    candidato = get_candidatura_by_id(str(id))
    if not candidato or not candidato.get('link_curriculo'):
        flash("Currículo não encontrado.", "error")
        return redirect(url_for('admin.candidato_detalhes', id=id))

    url = get_curriculo_url(candidato['link_curriculo'])
    if url:
        return redirect(url)
    flash("Erro ao gerar link do currículo.", "error")
    return redirect(url_for('admin.candidato_detalhes', id=id))


@admin_bp.route('/candidato/<uuid:id>/observacoes', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def candidato_observacoes(id):
    data = request.get_json()
    texto = (data.get("observacoes_rh", "") or "").strip()
    update_observacoes_rh(str(id), texto)
    return {"ok": True}


# ===== CENTRAL DE SOLICITAÇÕES =====

@admin_bp.route('/solicitacoes')
@login_required
@role_required('admin', 'rh', 'superadmin')
def solicitacoes_listar():
    pendentes = get_all_vagas_status(["solicitada", "em_triagem", "ajustes_pendentes"])
    em_aprovacao = get_all_vagas_status(["aguardando_aprovacao"])
    aprovadas = get_all_vagas_status(["aprovada", "aprovada_ressalvas", "em_recrutamento", "publicada", "em_entrevistas", "concluida"])
    recusadas = get_all_vagas_status(["encerrada"])
    return render_template('admin/solicitacoes.html',
                         pendentes=pendentes,
                         em_aprovacao=em_aprovacao,
                         aprovadas=aprovadas,
                         recusadas=recusadas)


# ===== FICHAS TÉCNICAS =====

@admin_bp.route('/fichas')
@login_required
@role_required('admin', 'rh', 'superadmin')
def fichas_listar():
    fichas = listar_fichas(apenas_ativas=False)
    return render_template('admin/fichas.html', fichas=fichas)


@admin_bp.route('/fichas/nova', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def fichas_nova():
    beneficios_lista = listar_beneficios()
    if request.method == 'POST':
        data = {
            "titulo": request.form.get('titulo'),
            "descricao": request.form.get('descricao'),
            "local_trabalho": request.form.get('local_trabalho'),
            "contrato_trabalho": request.form.get('contrato_trabalho'),
            "requisitos": request.form.get('requisitos'),
            "habilidades": request.form.get('habilidades'),
            "salario": request.form.get('salario', type=float) if request.form.get('salario') else None,
            "beneficios": ",".join(request.form.getlist('beneficios')),
        }
        if not data["titulo"]:
            flash("Informe o título da ficha técnica.", "warning")
            return render_template('admin/ficha_form.html', ficha=None, beneficios=beneficios_lista)
        ficha = criar_ficha(data)
        if ficha:
            set_ficha_beneficios(ficha["id"], request.form.getlist('beneficios'))
        flash("Ficha técnica criada com sucesso!", "success")
        return redirect(url_for('admin.fichas_listar'))
    return render_template('admin/ficha_form.html', ficha=None, beneficios=beneficios_lista)


@admin_bp.route('/fichas/<uuid:id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def fichas_editar(id):
    ficha = get_ficha_by_id(str(id))
    if not ficha:
        flash("Ficha não encontrada.", "error")
        return redirect(url_for('admin.fichas_listar'))
    beneficios_lista = listar_beneficios()
    ficha_beneficios_ids = get_ficha_beneficios(str(id))
    if request.method == 'POST':
        data = {
            "titulo": request.form.get('titulo'),
            "descricao": request.form.get('descricao'),
            "local_trabalho": request.form.get('local_trabalho'),
            "contrato_trabalho": request.form.get('contrato_trabalho'),
            "requisitos": request.form.get('requisitos'),
            "habilidades": request.form.get('habilidades'),
            "salario": request.form.get('salario', type=float) if request.form.get('salario') else None,
            "beneficios": ",".join(request.form.getlist('beneficios')),
        }
        atualizar_ficha(str(id), data)
        set_ficha_beneficios(str(id), request.form.getlist('beneficios'))
        flash("Ficha técnica atualizada!", "success")
        return redirect(url_for('admin.fichas_listar'))
    return render_template('admin/ficha_form.html', ficha=dict(ficha), beneficios=beneficios_lista, ficha_beneficios_ids=ficha_beneficios_ids)


@admin_bp.route('/fichas/<uuid:id>/arquivar', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def fichas_arquivar(id):
    arquivar_ficha(str(id))
    flash("Ficha técnica arquivada.", "info")
    return redirect(url_for('admin.fichas_listar'))


# ===== BENEFÍCIOS =====

@admin_bp.route('/beneficios')
@login_required
@role_required('admin', 'rh', 'superadmin')
def beneficios_listar():
    beneficios = listar_beneficios()
    return render_template('admin/beneficios.html', beneficios=beneficios)


@admin_bp.route('/beneficios/novo', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def beneficios_novo():
    if request.method == 'POST':
        nome = request.form.get('nome')
        if not nome:
            flash("Informe o nome do benefício.", "warning")
            return render_template('admin/beneficio_form.html', beneficio=None)
        criar_beneficio(nome)
        flash("Benefício criado com sucesso!", "success")
        return redirect(url_for('admin.beneficios_listar'))
    return render_template('admin/beneficio_form.html', beneficio=None)


@admin_bp.route('/beneficios/<uuid:id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def beneficios_editar(id):
    beneficio = get_beneficio_by_id(str(id))
    if not beneficio:
        flash("Benefício não encontrado.", "error")
        return redirect(url_for('admin.beneficios_listar'))
    if request.method == 'POST':
        nome = request.form.get('nome')
        if not nome:
            flash("Informe o nome do benefício.", "warning")
            return render_template('admin/beneficio_form.html', beneficio=beneficio)
        atualizar_beneficio(str(id), nome)
        flash("Benefício atualizado!", "success")
        return redirect(url_for('admin.beneficios_listar'))
    return render_template('admin/beneficio_form.html', beneficio=beneficio)


@admin_bp.route('/beneficios/<uuid:id>/excluir', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def beneficios_excluir(id):
    excluir_beneficio(str(id))
    flash("Benefício excluído.", "info")
    return redirect(url_for('admin.beneficios_listar'))


@admin_bp.route('/upgrade')
@login_required
def upgrade():
    return render_template('admin/upgrade.html')


@admin_bp.route('/banco-de-talentos')
@login_required
@role_required('admin', 'rh', 'superadmin')
def banco_talentos():
    talentos = get_banco_talentos()
    vagas_ativas = get_all_vagas(active_only=False)
    # Filtra apenas vagas ativas (onde ativo é True)
    vagas_ativas = [v for v in vagas_ativas if v.get("ativo") is True]
    
    # Extrai todas as tags únicas dos talentos para alimentar o filtro do frontend
    tags_unicas = set()
    for t in talentos:
        for tag in t.get("tags_lista", []):
            if tag:
                tags_unicas.add(tag.strip())
                
    return render_template('admin/banco_talentos.html', 
                           talentos=talentos, 
                           vagas=vagas_ativas, 
                           tags_unicas=sorted(list(tags_unicas)))


@admin_bp.route('/banco-de-talentos/vincular', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def banco_talentos_vincular():
    candidatura_id = request.form.get('candidatura_id')
    vaga_id = request.form.get('vaga_id')
    
    if not candidatura_id or not vaga_id:
        flash("Dados de vinculação incompletos.", "error")
        return redirect(url_for('admin.banco_talentos'))
        
    nova_candidatura_id = vincular_candidato_a_vaga(candidatura_id, vaga_id)
    if nova_candidatura_id:
        from models.vaga import get_vaga_by_id
        vaga = get_vaga_by_id(vaga_id)
        titulo_vaga = vaga.get("titulo", "") if vaga else "vaga selecionada"
        flash(f"Candidato vinculado com sucesso à vaga '{titulo_vaga}'!", "success")
        return redirect(url_for('admin.vaga_candidatos', id=vaga_id))
    else:
        flash("O candidato já está inscrito ou ocorreu um erro ao vincular a esta vaga.", "error")
        return redirect(url_for('admin.banco_talentos'))
