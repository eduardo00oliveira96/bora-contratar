import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from models.vaga import get_vaga_by_id, get_all_vagas
from models.candidatura import create_candidatura, update_candidatura_ai_eval, get_candidatura_by_cpf, update_candidatura_info
from models.candidato import criar_ou_buscar_candidato
from flask import jsonify
from services.extrair_texto import extrair_texto_pdf
from services.obter_dados_vaga import obter_dados_vaga
from services.upload_curriculo import upload_curriculo, get_curriculo_url
from ai.agente_avaliar_cv import avaliar_cv

public_bp = Blueprint('public', __name__)
UPLOAD_DIR = "upload_curriculos"

@public_bp.route('/')
def index():
    vagas = get_all_vagas(active_only=True)
    return render_template('public/index.html', vagas=vagas)

@public_bp.route('/vaga/<uuid:id>')
def vaga_detalhes(id):
    vaga = get_vaga_by_id(str(id))
    if not vaga:
        flash("Vaga não encontrada.", "error")
        return redirect(url_for('public.index'))

    beneficios = vaga['beneficios'].split(',') if vaga.get('beneficios') else []
    return render_template('public/vaga.html', vaga=vaga, beneficios=beneficios)

@public_bp.route('/vaga/<uuid:id>/apply', methods=['POST'])
def vaga_apply(id):
    vaga = get_vaga_by_id(str(id))
    if not vaga:
        flash("Vaga não encontrada.", "error")
        return redirect(url_for('public.index'))

    nome = request.form.get('nome')
    cpf = request.form.get('cpf')
    telefone = request.form.get('telefone')
    email = request.form.get('email')
    curriculo = request.files.get('curriculo')

    candidato_existente = get_candidatura_by_cpf(cpf, str(id))
    existing_id = None
    if candidato_existente and candidato_existente.get('vaga_id') == str(id):
        existing_id = candidato_existente.get('id')

    if not (nome and cpf and telefone and email):
        flash("Preencha todos os campos obrigatórios.", "warning")
        return redirect(url_for('public.vaga_detalhes', id=id))

    if not existing_id and (not curriculo or curriculo.filename == ''):
        flash("Nenhum currículo selecionado.", "warning")
        return redirect(url_for('public.vaga_detalhes', id=id))

    try:
        texto_extraido = ""
        curriculo_path = ""

        if curriculo and curriculo.filename != '':
            curriculo_path = upload_curriculo(curriculo)
            if curriculo_path:
                os.makedirs(UPLOAD_DIR, exist_ok=True)
                timestamp_name = f"{int(__import__('time').time())}_{secure_filename(curriculo.filename)}"
                local_path = os.path.join(UPLOAD_DIR, timestamp_name)
                curriculo.seek(0)
                curriculo.save(local_path)
                texto_extraido = extrair_texto_pdf(local_path)

        candidato_id = criar_ou_buscar_candidato({
            "nome": nome, "cpf": cpf,
            "telefone": telefone, "email": email
        })

        candidatura_data = {
            "vaga_id": str(id),
            "candidato_id": candidato_id,
            "resumo": texto_extraido,
            "link_curriculo": curriculo_path or "",
        }

        if existing_id:
            if not curriculo_path:
                old_data = get_candidatura_by_cpf(cpf, str(id))
                if old_data:
                    candidatura_data['resumo'] = old_data.get('resumo', '')
                    texto_extraido = old_data.get('resumo', '')

            update_candidatura_info(existing_id, {
                **candidatura_data,
                "candidato_id": candidato_id,
                "nome": nome,
                "telefone": telefone,
                "email": email,
            })
            candidatura_id = existing_id
            flash("Candidatura atualizada com sucesso!", "success")
        else:
            candidatura_id = create_candidatura(candidatura_data)
            flash("Candidatura enviada com sucesso! Boa sorte!", "success")

        if texto_extraido:
            try:
                vaga_info = obter_dados_vaga(str(id))
                avaliar_cv(texto_extraido, vaga_info, candidatura_id)
            except Exception as e_ia:
                print(f"Erro na IA: {e_ia}")

    except Exception as e:
        print(f"Erro inesperado: {e}")
        flash("Ocorreu um erro ao processar sua candidatura. Tente novamente.", "error")

    return redirect(url_for('public.vaga_detalhes', id=id))
