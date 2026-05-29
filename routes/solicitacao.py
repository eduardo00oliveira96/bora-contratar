from flask import Blueprint, render_template, request, flash, redirect, url_for, g
from src.decorators import login_required, role_required
from models.vaga import (
    criar_solicitacao, get_vaga_by_id, triar_solicitacao,
    encaminhar_para_aprovacao, atualizar_status_vaga,
    preencher_ficha_tecnica, get_solicitacoes_por_papel, get_all_vagas
)
from models.solicitacao import (
    adicionar_aprovador, get_aprovadores_da_solicitacao,
    registrar_parecer_aprovador, verificar_status_aprovacao,
    get_aprovacao_pendente, listar_aprovadores_disponiveis
)
from models.usuario import listar_usuarios_do_tenant
from models.ficha_tecnica import listar_fichas, get_ficha_by_id, atualizar_ficha
from models.entrevista import copiar_etapas_da_ficha
from models.notificacao import notificar_gestor, notificar_rh, notificar_aprovadores

solicitacao_bp = Blueprint('solicitacao', __name__, url_prefix='/solicitacao')


@solicitacao_bp.route('/nova', methods=['GET', 'POST'])
@login_required
@role_required('gestor', 'admin', 'superadmin')
def nova():
    usuario = g.usuario

    if request.method == 'POST':
        tipo_solicitacao = request.form.get('tipo_solicitacao')
        ficha_id = request.form.get('ficha_id')
        justificativa = request.form.get('justificativa')
        previsao_inicio = request.form.get('previsao_inicio')

        if not tipo_solicitacao:
            fichas = listar_fichas()
            flash("Selecione o tipo de solicitação.", "warning")
            return render_template('solicitacao/form.html', vaga=None, fichas=fichas)

        titulo = request.form.get('titulo')
        if ficha_id:
            ficha = get_ficha_by_id(ficha_id)
            if ficha:
                titulo = ficha['titulo']

        if not titulo:
            fichas = listar_fichas()
            flash("Não foi possível gerar o título. Selecione uma ficha técnica.", "warning")
            return render_template('solicitacao/form.html', vaga=None, fichas=fichas)

        data = {
            "titulo": titulo,
            "tipo_solicitacao": tipo_solicitacao,
            "justificativa": justificativa,
            "previsao_inicio": previsao_inicio,
            "criado_por": usuario.get("id"),
            "gestor_owner_id": usuario.get("id") if usuario.get("papel") == "gestor" else None,
            "user_created": usuario.get("nome"),
        }

        vaga_id = criar_solicitacao(data)
        if not vaga_id:
            fichas = listar_fichas()
            flash("Erro ao criar solicitação.", "error")
            return render_template('solicitacao/form.html', vaga=None, fichas=fichas)

        if ficha_id:
            ficha = get_ficha_by_id(ficha_id)
            if ficha:
                preencher_ficha_tecnica(vaga_id, {
                    "descricao": ficha.get("descricao"),
                    "local_trabalho": ficha.get("local_trabalho"),
                    "tipo_contrato": ficha.get("tipo_contrato"),
                    "requisitos": ficha.get("requisitos"),
                    "habilidades": ficha.get("habilidades"),
                    "salario": ficha.get("salario"),
                    "beneficios": ficha.get("beneficios"),
                    "ficha_tecnica_id": ficha_id,
                })
                copiar_etapas_da_ficha(vaga_id, ficha_id)

        notificar_rh(
            {"id": vaga_id, "criado_por": usuario.get("id")},
            "nova_solicitacao",
            "Nova solicitação de contratação",
            f"{usuario.get('nome')} criou uma nova solicitação: {titulo}"
        )

        flash("Solicitação de contratação enviada com sucesso!", "success")
        return redirect(url_for('solicitacao.detalhes', id=vaga_id))

    fichas = listar_fichas()
    return render_template('solicitacao/form.html', vaga=None, fichas=fichas)


@solicitacao_bp.route('/<uuid:id>')
@login_required
def detalhes(id):
    usuario = g.usuario
    vaga = get_vaga_by_id(str(id))
    if not vaga:
        flash("Solicitação não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))

    aprovadores = get_aprovadores_da_solicitacao(str(id))
    status_aprovacao = verificar_status_aprovacao(str(id))
    aprovacao_pendente = None

    if usuario.get("papel") == "aprovador":
        aprovacao_pendente = get_aprovacao_pendente(str(id), usuario.get("id"))

    return render_template('solicitacao/detalhes.html',
                         vaga=vaga,
                         aprovadores=aprovadores,
                         status_aprovacao=status_aprovacao,
                         aprovacao_pendente=aprovacao_pendente)


@solicitacao_bp.route('/<uuid:id>/triar', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def triar(id):
    usuario = g.usuario
    vaga = get_vaga_by_id(str(id))
    if not vaga:
        flash("Solicitação não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))

    if vaga.get("status_vaga") not in ("solicitada", "em_triagem"):
        flash("Solicitação não está em triagem.", "warning")
        return redirect(url_for('solicitacao.detalhes', id=id))

    if request.method == 'POST':
        parecer = request.form.get('parecer_rh')
        observacoes = request.form.get('observacoes_rh', '')

        if parecer == "validada":
            ficha = {
                "descricao": request.form.get('descricao'),
                "local_trabalho": request.form.get('local_trabalho'),
                "tipo_contrato": request.form.get('tipo_contrato') or request.form.get('contrato_trabalho'),
                "requisitos": request.form.get('requisitos'),
                "habilidades": request.form.get('habilidades'),
                "salario": request.form.get('salario', type=float) if request.form.get('salario') else None,
                "beneficios": request.form.get('beneficios'),
            }
            aprovador_ids = request.form.getlist('aprovador_ids')

            try:
                triar_solicitacao(str(id), "validada", observacoes)
                if any(ficha.values()):
                    preencher_ficha_tecnica(str(id), ficha)
                    if vaga.get("ficha_tecnica_id"):
                        atualizar_ficha(vaga["ficha_tecnica_id"], ficha)
                if aprovador_ids:
                    for ordem, apr_id in enumerate(aprovador_ids, 1):
                        adicionar_aprovador(str(id), apr_id, ordem)
                    encaminhar_para_aprovacao(str(id))
                    mensagem = "Solicitação validada e encaminhada para aprovação."
                else:
                    atualizar_status_vaga(str(id), "aprovada")
                    mensagem = "Solicitação validada e aprovada!"

                notificar_gestor(
                    vaga, "validada",
                    "Solicitação validada pelo RH",
                    f"{usuario.get('nome')} validou sua solicitação e {'encaminhou para aprovação' if aprovador_ids else 'aprovou'}."
                )
                flash(mensagem, "success")
            except Exception:
                atualizar_status_vaga(str(id), "solicitada", {"parecer_rh": None, "observacoes_rh": None})
                flash("Erro ao processar validação. Operação revertida.", "error")
        elif parecer == "ajustes":
            triar_solicitacao(str(id), "ajustes", observacoes)
            flash("Solicitação devolvida para ajustes.", "warning")
            notificar_gestor(
                vaga, "ajustes",
                "Solicitação precisa de ajustes",
                f"{usuario.get('nome')} solicitou ajustes: {observacoes}" if observacoes else f"{usuario.get('nome')} solicitou ajustes na sua solicitação."
            )
        elif parecer == "reprovada_rh":
            triar_solicitacao(str(id), "reprovada_rh", observacoes)
            flash("Solicitação reprovada.", "error")
            notificar_gestor(
                vaga, "reprovada_rh",
                "Solicitação reprovada pelo RH",
                f"{usuario.get('nome')} reprovou sua solicitação{' com justificativa: ' + observacoes if observacoes else '.'}"
            )

        return redirect(url_for('solicitacao.detalhes', id=id))

    ficha = None
    if vaga.get("ficha_tecnica_id"):
        ficha = get_ficha_by_id(vaga["ficha_tecnica_id"])

    aprovadores_disponiveis = listar_aprovadores_disponiveis(usuario.get("tenant_id"))
    return render_template('solicitacao/triagem.html',
                         vaga=vaga,
                         ficha=ficha,
                         aprovadores=aprovadores_disponiveis)


@solicitacao_bp.route('/<uuid:id>/aprovar', methods=['POST'])
@login_required
@role_required('aprovador')
def aprovar(id):
    usuario = g.usuario
    vaga = get_vaga_by_id(str(id))
    if not vaga:
        flash("Solicitação não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))

    if vaga.get("status_vaga") != "aguardando_aprovacao":
        flash("Solicitação não está aguardando aprovação.", "warning")
        return redirect(url_for('solicitacao.detalhes', id=id))

    aprovacao = get_aprovacao_pendente(str(id), usuario.get("id"))
    if not aprovacao:
        flash("Você não tem aprovação pendente para esta solicitação.", "warning")
        return redirect(url_for('solicitacao.detalhes', id=id))

    parecer = request.form.get('parecer')
    observacoes = request.form.get('observacoes', '')

    if parecer not in ("aprovado", "aprovado_ressalvas", "reprovado"):
        flash("Parecer inválido.", "error")
        return redirect(url_for('solicitacao.detalhes', id=id))

    registrar_parecer_aprovador(aprovacao["id"], parecer, observacoes)
    status_geral = verificar_status_aprovacao(str(id))

    if status_geral == "aprovado":
        atualizar_status_vaga(str(id), "aprovada")
        notificar_gestor(
            vaga, "aprovado",
            "Solicitação aprovada",
            f"Sua solicitação foi aprovada por {usuario.get('nome')}."
        )
    elif status_geral == "aprovado_ressalvas":
        atualizar_status_vaga(str(id), "aprovada_ressalvas")
        notificar_gestor(
            vaga, "aprovado_ressalvas",
            "Solicitação aprovada com ressalvas",
            f"Sua solicitação foi aprovada com ressalvas por {usuario.get('nome')}."
        )
    elif status_geral == "reprovado":
        atualizar_status_vaga(str(id), "encerrada", {"ativo": False})
        notificar_gestor(
            vaga, "reprovado",
            "Solicitação reprovada",
            f"Sua solicitação foi reprovada por {usuario.get('nome')}."
        )

    notificar_rh(
        vaga, "parecer_aprovador",
        f"Aprovador {'aprovou' if status_geral != 'reprovado' else 'rejeitou'} solicitação",
        f"{usuario.get('nome')} registrou parecer '{status_geral}' na solicitação '{vaga.get('titulo')}'."
    )
    notificar_aprovadores(
        vaga, "parecer_aprovador",
        f"Atualização na aprovação",
        f"{usuario.get('nome')} registrou parecer '{status_geral}'."
    )

    flash("Parecer registrado com sucesso!", "success")
    return redirect(url_for('solicitacao.detalhes', id=id))


@solicitacao_bp.route('/<uuid:id>/recusar', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def recusar(id):
    usuario = g.usuario
    vaga = get_vaga_by_id(str(id))
    if not vaga:
        flash("Solicitação não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))

    if vaga.get("status_vaga") in ("encerrada", "publicada"):
        flash("Solicitação já encerrada ou publicada.", "warning")
        return redirect(url_for('solicitacao.detalhes', id=id))

    motivo = request.form.get('motivo_recusa', '').strip()
    if not motivo:
        flash("Informe o motivo da recusa.", "warning")
        return redirect(url_for('solicitacao.detalhes', id=id))

    atualizar_status_vaga(str(id), "encerrada", {"ativo": False, "observacoes_rh": motivo})
    flash("Solicitação recusada.", "info")
    notificar_gestor(
        vaga, "recusada",
        "Solicitação recusada",
        f"{usuario.get('nome')} recusou sua solicitação. Motivo: {motivo}"
    )
    return redirect(url_for('admin.solicitacoes_listar'))


@solicitacao_bp.route('/<uuid:id>/ajustar', methods=['GET', 'POST'])
@login_required
def ajustar(id):
    usuario = g.usuario
    vaga = get_vaga_by_id(str(id))
    if not vaga:
        flash("Solicitação não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))

    if vaga.get("criado_por") != usuario.get("id"):
        flash("Você não tem permissão para ajustar esta solicitação.", "error")
        return redirect(url_for('admin.dashboard'))

    if vaga.get("status_vaga") != "ajustes_pendentes":
        flash("Esta solicitação não está pendente de ajustes.", "warning")
        return redirect(url_for('solicitacao.detalhes', id=id))

    if request.method == 'POST':
        justificativa = request.form.get('justificativa')
        previsao_inicio = request.form.get('previsao_inicio')

        atualizar_status_vaga(str(id), "solicitada", {
            "justificativa": justificativa,
            "previsao_inicio": previsao_inicio,
            "parecer_rh": None,
        })
        notificar_rh(
            {"id": str(id), "criado_por": usuario.get("id")},
            "reenviada",
            "Solicitação reenviada após ajustes",
            f"{usuario.get('nome')} reenviou a solicitação '{vaga.get('titulo')}' após ajustes."
        )
        flash("Solicitação ajustada e reenviada para o RH!", "success")
        return redirect(url_for('solicitacao.detalhes', id=id))

    return render_template('solicitacao/ajustar.html', vaga=vaga)


@solicitacao_bp.route('/<uuid:id>/recrutar', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def iniciar_recrutamento(id):
    vaga = get_vaga_by_id(str(id))
    if not vaga:
        flash("Solicitação não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))

    if vaga.get("status_vaga") not in ("aprovada", "aprovada_ressalvas"):
        flash("Solicitação precisa estar aprovada para iniciar recrutamento.", "warning")
        return redirect(url_for('solicitacao.detalhes', id=id))

    atualizar_status_vaga(str(id), "em_recrutamento")
    flash("Recrutamento iniciado!", "success")
    return redirect(url_for('solicitacao.detalhes', id=id))


@solicitacao_bp.route('/<uuid:id>/publicar', methods=['POST'])
@login_required
@role_required('admin', 'rh', 'superadmin')
def publicar(id):
    vaga = get_vaga_by_id(str(id))
    if not vaga:
        flash("Vaga não encontrada.", "error")
        return redirect(url_for('admin.dashboard'))

    if vaga.get("status_vaga") not in ("em_recrutamento", "publicada"):
        flash("Só é possível publicar vagas em recrutamento.", "warning")
        return redirect(url_for('solicitacao.detalhes', id=id))

    atualizar_status_vaga(str(id), "publicada", {"ativo": True})
    flash("Vaga publicada com sucesso!", "success")
    return redirect(url_for('solicitacao.detalhes', id=id))
