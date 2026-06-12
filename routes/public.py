import os
import threading
import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, g
from werkzeug.utils import secure_filename
from models.vaga import get_vaga_by_id, get_all_vagas
from models.candidatura import create_candidatura, update_candidatura_ai_eval, get_candidatura_by_cpf, update_candidatura_info, update_candidatura_erro, reset_candidatura_ai_eval, get_candidatura_by_id
from models.candidato import criar_ou_buscar_candidato
from flask import jsonify
from services.extrair_texto import extrair_texto_pdf
from services.obter_dados_vaga import obter_dados_vaga
from services.upload_curriculo import upload_curriculo, get_curriculo_url
from ai.agente_avaliar_cv import avaliar_cv
from src.decorators import login_required, role_required

public_bp = Blueprint('public', __name__)
UPLOAD_DIR = "upload_curriculos"
logger = logging.getLogger(__name__)

@public_bp.route('/privacidade')
def privacidade():
    return render_template('public/privacidade.html')

@public_bp.route('/')
def index():
    return render_template('public/landing.html')

@public_bp.route('/vagas')
def listar_vagas():
    vagas = get_all_vagas(active_only=True)
    return render_template('public/vagas.html', vagas=vagas)

@public_bp.route('/vaga/<uuid:id>')
def vaga_detalhes(id):
    vaga = get_vaga_by_id(str(id))
    if not vaga:
        flash("Vaga não encontrada.", "error")
        return redirect(url_for('public.index'))

    beneficios_raw = vaga.get('beneficios') or ''
    partes = [x.strip() for x in beneficios_raw.split(',') if x.strip()]
    beneficios = []
    if partes and len(partes[0]) == 36 and '-' in partes[0]:
        from database.conexao_supabase import get_supabase_client, get_tenant_id
        tenant_id = get_tenant_id()
        if tenant_id:
            client = get_supabase_client()
            ben_result = client.table("beneficios").select("id, nome").eq("tenant_id", tenant_id).execute()
            nome_map = {b["id"]: b["nome"] for b in (ben_result.data or [])}
            beneficios = [nome_map.get(p, p) for p in partes]
    else:
        beneficios = partes
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
    aceito_termos = request.form.get('aceito_termos')

    if not aceito_termos:
        flash("Você precisa aceitar a Política de Privacidade para se candidatar.", "warning")
        return redirect(url_for('public.vaga_detalhes', id=id))

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

    local_path = None
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
            vaga_info = obter_dados_vaga(str(id))
            thread = threading.Thread(
                target=_avaliar_cv_background,
                args=(texto_extraido, vaga_info, candidatura_id),
                daemon=True
            )
            thread.start()

    except Exception as e:
        logger.error(f"Erro ao processar candidatura: {e}", exc_info=True)
        flash("Ocorreu um erro ao processar sua candidatura. Tente novamente.", "error")

    finally:
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception as ex:
                logger.error(f"Erro ao remover arquivo temporario do curriculo: {ex}")

    return redirect(url_for('public.vaga_detalhes', id=id))


def _avaliar_cv_background(texto, vaga_info, candidatura_id):
    try:
        avaliar_cv(texto, vaga_info, candidatura_id)
    except Exception as e:
        logger.error(f"Erro na avaliação de IA em background: {e}", exc_info=True)
        try:
            update_candidatura_erro(candidatura_id, f"Erro inesperado no processamento: {e}")
        except Exception:
            pass


@public_bp.route('/candidatura/<uuid:id>/reprocessar-ia', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def candidato_reprocessar_ia(id):
    candidatura = get_candidatura_by_id(str(id))
    if not candidatura:
        flash("Candidatura não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))

    resumo = candidatura.get("resumo", "")
    vaga_id = candidatura.get("vaga_id")

    if not resumo or not resumo.strip():
        flash("Não há texto extraído do currículo para reprocessar. O candidato precisa reenviar o currículo.", "warning")
        return redirect(url_for('admin.candidato_detalhes', id=id))

    if not vaga_id:
        flash("Candidatura sem vaga associada.", "error")
        return redirect(url_for('admin.candidato_detalhes', id=id))

    reset_candidatura_ai_eval(str(id))

    vaga_info = obter_dados_vaga(vaga_id)
    thread = threading.Thread(
        target=_avaliar_cv_background,
        args=(resumo, vaga_info, str(id)),
        daemon=True
    )
    thread.start()

    flash("Reprocessamento da análise por IA iniciado em segundo plano.", "info")
    return redirect(url_for('admin.candidato_detalhes', id=id))
