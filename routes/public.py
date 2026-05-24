import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from models.vaga import get_vaga_by_id, get_all_vagas
from models.candidatura import create_candidatura, update_candidatura_ai_eval, get_candidatura_by_cpf, update_candidatura_info
from flask import jsonify

# Integrations
from services.extarir_texto import extrair_texto_pdf
from services.obter_dados_vaga import obter_dados_vaga
from ai.agente_avaliar_cv import avaliar_cv

public_bp = Blueprint('public', __name__)
UPLOAD_DIR = "upload_curriculos"

@public_bp.route('/')
def index():
    vagas = get_all_vagas(active_only=True)
    return render_template('public/index.html', vagas=vagas)

@public_bp.route('/vaga/<int:id>')
def vaga_detalhes(id):
    vaga = get_vaga_by_id(id)
    if not vaga:
        flash("Vaga não encontrada.", "error")
        return redirect(url_for('public.index'))
    
    beneficios = vaga['beneficios'].split(',') if vaga['beneficios'] else []
    return render_template('public/vaga.html', vaga=vaga, beneficios=beneficios)

@public_bp.route('/vaga/<int:id>/apply', methods=['POST'])
def vaga_apply(id):
    vaga = get_vaga_by_id(id)
    if not vaga:
        flash("Vaga não encontrada.", "error")
        return redirect(url_for('public.index'))
        
    nome = request.form.get('nome')
    cpf = request.form.get('cpf')
    telefone = request.form.get('telefone')
    email = request.form.get('email')
    curriculo = request.files.get('curriculo')
    
    # Internal check: Does this CPF already exist for THIS job?
    candidato_existente = get_candidatura_by_cpf(cpf, id)
    existing_id = None
    if candidato_existente and candidato_existente['vaga_id'] == id:
        existing_id = candidato_existente['id']
    
    if not (nome and cpf and telefone and email):
        flash("Preencha todos os campos obrigatórios.", "warning")
        return redirect(url_for('public.vaga_detalhes', id=id))
        
    # Exigir currículo apenas se for uma nova candidatura
    if not existing_id and (not curriculo or curriculo.filename == ''):
        flash("Nenhum currículo selecionado.", "warning")
        return redirect(url_for('public.vaga_detalhes', id=id))
        
    try:
        texto_extraido = ""
        filepath = ""
        
        # Só processamos novo PDF se o usuário fez o upload de um, seja na criação ou no update
        if curriculo and curriculo.filename != '':
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            filename = secure_filename(curriculo.filename)
            import time
            safe_filename = f"{int(time.time())}_{filename}"
            filepath = os.path.join(UPLOAD_DIR, safe_filename)
            curriculo.save(filepath)
            texto_extraido = extrair_texto_pdf(filepath)
            
        candidatura_data = {
            "vaga_id": id,
            "nome": nome,
            "cpf": cpf,
            "telefone": telefone,
            "email": email,
            "curriculo": filepath,
            "resumo": texto_extraido 
        }
        
        if existing_id:
            # Se não fez upload de novo currículo, precisamos pegar os dados antigos para não zerar no banco
            if not filepath:
                # Opcional: buscar os dados antigos no BD para manter no update
                old_data = get_candidatura_by_cpf(cpf, id)
                if old_data:
                    candidatura_data['curriculo'] = old_data['curriculo']
                    candidacy_data['resumo'] = old_data['resumo']
                    texto_extraido = old_data['resumo']
                    
            update_candidatura_info(existing_id, candidatura_data)
            candidatura_id = existing_id
            flash("Candidatura atualizada com sucesso!", "success")
        else:
            candidatura_id = create_candidatura(candidatura_data)
            flash("Candidatura enviada com sucesso! Boa sorte!", "success")
        
        # Só reprocessamos a IA se houver texto_extraido (novo cv enviado) ou no caso de criação
        if texto_extraido:
            try:
                vaga_info = obter_dados_vaga(id)
                avaliar_cv(texto_extraido, vaga_info, candidatura_id)
            except Exception as e_ia:
                print(f"Erro na IA: {e_ia}")
            
    except Exception as e:
        print(f"Erro inesperado: {e}")
        flash("Ocorreu um erro ao processar sua candidatura. Tente novamente.", "error")
        
    return redirect(url_for('public.vaga_detalhes', id=id))