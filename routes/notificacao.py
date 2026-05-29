from flask import Blueprint, render_template, request, jsonify, redirect, url_for, g
from src.decorators import login_required
from models.notificacao import (
    listar_notificacoes, notificacoes_nao_lidas,
    marcar_como_lida, marcar_todas_como_lidas
)

notificacao_bp = Blueprint('notificacao', __name__, url_prefix='/notificacoes')


@notificacao_bp.route('')
@login_required
def listar():
    usuario = g.usuario
    notificacoes = listar_notificacoes(usuario.get("id"))
    return render_template('notificacoes.html', notificacoes=notificacoes)


@notificacao_bp.route('/<uuid:id>/ler', methods=['POST'])
@login_required
def ler(id):
    marcar_como_lida(str(id))
    return jsonify({"ok": True})


@notificacao_bp.route('/ler-todas', methods=['POST'])
@login_required
def ler_todas():
    usuario = g.usuario
    marcar_todas_como_lidas(usuario.get("id"))
    return jsonify({"ok": True})


@notificacao_bp.route('/nao-lidas')
@login_required
def nao_lidas():
    usuario = g.usuario
    count = notificacoes_nao_lidas(usuario.get("id"))
    return jsonify({"count": count})
