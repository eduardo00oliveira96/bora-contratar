import os
import ast
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_from_directory, current_app, g
from src.decorators import login_required, role_required
from models.vaga import (
    get_all_vagas, get_vaga_by_id, create_vaga, update_vaga,
    close_vaga, publicar_vaga, get_vagas_solicitadas,
    get_solicitacoes_em_triagem, get_solicitacoes_aguardando_aprovacao,
    get_solicitacoes_aprovadas, get_solicitacoes_por_papel
)
from models.candidatura import get_candidaturas_by_vaga, get_candidatura_by_id, update_candidatura_status, get_all_candidaturas_with_vaga
from models.usuario import listar_usuarios_do_tenant
from models.ficha_tecnica import listar_fichas, get_ficha_by_id, criar_ficha, atualizar_ficha, arquivar_ficha
from services.upload_curriculo import get_curriculo_url

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@login_required
def dashboard():
    usuario = g.usuario
    papel = usuario.get("papel")
    usuario_id = usuario.get("id")

    vagas = get_all_vagas(papel=papel, usuario_id=usuario_id)

    total_candidatos = 0
    for v in vagas:
        cands = get_candidaturas_by_vaga(v['id'])
        total_candidatos += len(cands)

    vagas_solicitadas = []
    solicitacoes_triagem = []
    solicitacoes_aprovacao = []
    solicitacoes_aprovadas = []
    solicitacoes_aprovar = []

    if papel in ("admin", "rh", "superadmin"):
        vagas_solicitadas = get_vagas_solicitadas()
        solicitacoes_triagem = get_solicitacoes_em_triagem()
        solicitacoes_aprovacao = get_solicitacoes_aguardando_aprovacao()
        solicitacoes_aprovadas = get_solicitacoes_aprovadas()

    if papel == "aprovador":
        solicitacoes_aprovar = get_solicitacoes_por_papel("aprovador", usuario_id)

    return render_template('admin/dashboard.html',
                         vagas=vagas,
                         vagas_solicitadas=vagas_solicitadas,
                         solicitacoes_triagem=solicitacoes_triagem,
                         solicitacoes_aprovacao=solicitacoes_aprovacao,
                         solicitacoes_aprovadas=solicitacoes_aprovadas,
                         solicitacoes_aprovar=solicitacoes_aprovar,
                         total_candidatos=total_candidatos)


@admin_bp.route('/vagas')
@login_required
def vagas_listar():
    usuario = g.usuario
    vagas = get_all_vagas(papel=usuario.get("papel"), usuario_id=usuario.get("id"))
    return render_template('admin/vagas.html', vagas=vagas)


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


@admin_bp.route('/candidato/<uuid:id>', methods=['GET'])
@login_required
def candidato_detalhes(id):
    candidato = get_candidatura_by_id(str(id))
    if not candidato:
        flash("Candidato não encontrado.", "error")
        return redirect(url_for('admin.dashboard'))

    try:
        fortes = ast.literal_eval(candidato['pontos_fortes']) if candidato.get('pontos_fortes') else []
    except:
        fortes = []
    try:
        gaps = ast.literal_eval(candidato['gaps_atencao']) if candidato.get('gaps_atencao') else []
    except:
        gaps = []

    return render_template('admin/candidato_detalhes.html', candidato=candidato, fortes=fortes, gaps=gaps)


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
    if request.method == 'POST':
        data = {
            "titulo": request.form.get('titulo'),
            "descricao": request.form.get('descricao'),
            "local_trabalho": request.form.get('local_trabalho'),
            "contrato_trabalho": request.form.get('contrato_trabalho'),
            "requisitos": request.form.get('requisitos'),
            "habilidades": request.form.get('habilidades'),
            "salario": request.form.get('salario', type=float) if request.form.get('salario') else None,
            "beneficios": request.form.get('beneficios'),
        }
        if not data["titulo"]:
            flash("Informe o título da ficha técnica.", "warning")
            return render_template('admin/ficha_form.html', ficha=None)
        criar_ficha(data)
        flash("Ficha técnica criada com sucesso!", "success")
        return redirect(url_for('admin.fichas_listar'))
    return render_template('admin/ficha_form.html', ficha=None)


@admin_bp.route('/fichas/<uuid:id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def fichas_editar(id):
    ficha = get_ficha_by_id(str(id))
    if not ficha:
        flash("Ficha não encontrada.", "error")
        return redirect(url_for('admin.fichas_listar'))
    if request.method == 'POST':
        data = {
            "titulo": request.form.get('titulo'),
            "descricao": request.form.get('descricao'),
            "local_trabalho": request.form.get('local_trabalho'),
            "contrato_trabalho": request.form.get('contrato_trabalho'),
            "requisitos": request.form.get('requisitos'),
            "habilidades": request.form.get('habilidades'),
            "salario": request.form.get('salario', type=float) if request.form.get('salario') else None,
            "beneficios": request.form.get('beneficios'),
        }
        atualizar_ficha(str(id), data)
        flash("Ficha técnica atualizada!", "success")
        return redirect(url_for('admin.fichas_listar'))
    return render_template('admin/ficha_form.html', ficha=dict(ficha))


@admin_bp.route('/fichas/<uuid:id>/arquivar', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def fichas_arquivar(id):
    arquivar_ficha(str(id))
    flash("Ficha técnica arquivada.", "info")
    return redirect(url_for('admin.fichas_listar'))
