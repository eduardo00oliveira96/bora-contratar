import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_from_directory, current_app
from models.vaga import get_all_vagas, get_vaga_by_id, create_vaga, update_vaga, close_vaga
from models.candidatura import get_candidaturas_by_vaga, get_candidatura_by_id, update_candidatura_status

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
def dashboard():
    vagas = get_all_vagas()
    # Para o dashboard, poderíamos calcular o total de candidatos com uma query, mas vamos via loop neste MVP:
    total_candidatos = 0
    for v in vagas:
        cands = get_candidaturas_by_vaga(v['id'])
        total_candidatos += len(cands)
        
    return render_template('admin/dashboard.html', vagas=vagas, total_candidatos=total_candidatos)

@admin_bp.route('/vaga/nova', methods=['GET', 'POST'])
def vaga_nova():
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
            "beneficios": ",".join(request.form.getlist('beneficios'))
        }
        create_vaga(data)
        flash("Nova vaga criada com sucesso!", "success")
        return redirect(url_for('admin.dashboard'))
        
    return render_template('admin/vaga_form.html', vaga=None)

@admin_bp.route('/vaga/<int:id>/editar', methods=['GET', 'POST'])
def vaga_editar(id):
    vaga = get_vaga_by_id(id)
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
            "beneficios": ",".join(request.form.getlist('beneficios'))
        }
        update_vaga(id, data)
        flash("Vaga atualizada com sucesso!", "success")
        return redirect(url_for('admin.dashboard'))
        
    # Converter string de benefícios em lista
    return render_template('admin/vaga_form.html', vaga=dict(vaga))

@admin_bp.route('/vaga/<int:id>/encerrar', methods=['POST'])
def vaga_encerrar(id):
    close_vaga(id)
    flash("Vaga encerrada.", "warning")
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/vaga/<int:id>/candidatos')
def vaga_candidatos(id):
    vaga = get_vaga_by_id(id)
    if not vaga:
        flash("Vaga não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))
        
    candidatos = get_candidaturas_by_vaga(id)
    return render_template('admin/candidatos.html', vaga=vaga, candidatos=candidatos)

@admin_bp.route('/candidato/<int:id>', methods=['GET'])
def candidato_detalhes(id):
    candidato = get_candidatura_by_id(id)
    if not candidato:
        flash("Candidato não encontrado.", "error")
        return redirect(url_for('admin.dashboard'))
        
    import ast
    try:
        fortes = ast.literal_eval(candidato['pontos_fortes']) if candidato['pontos_fortes'] else []
    except: fortes = []
    
    try:
        gaps = ast.literal_eval(candidato['gaps_atencao']) if candidato['gaps_atencao'] else []
    except: gaps = []
        
    return render_template('admin/candidato_detalhes.html', candidato=candidato, fortes=fortes, gaps=gaps)

@admin_bp.route('/candidato/<int:id>/status', methods=['POST'])
def candidato_status(id):
    status = request.form.get('status')
    candidato = get_candidatura_by_id(id)
    if status and candidato:
        update_candidatura_status(id, status)
        flash(f"Status atualizado para: {status}", "success")
        return redirect(url_for('admin.candidato_detalhes', id=id))
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/candidato/<int:id>/curriculo')
def download_cv(id):
    candidato = get_candidatura_by_id(id)
    if not candidato or not candidato['curriculo']:
        flash("Currículo não encontrado.", "error")
        return redirect(url_for('admin.candidato_detalhes', id=id))
        
    # The path is usually stored with the directory "upload_curriculos/..."
    filepath = candidato['curriculo']
    filename = os.path.basename(filepath)
    
    # We must construct the absolute path to the directory
    import sys
    # BASE_DIR is two levels up from routes
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(base_dir, "upload_curriculos")
    
    return send_from_directory(upload_dir, filename)