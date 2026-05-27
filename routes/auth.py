import os
import requests
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, g
from src.decorators import login_required, role_required, verificar_jwt
from models.usuario import (
    buscar_usuario_por_auth, criar_usuario, listar_tenants,
    criar_tenant, listar_usuarios_do_tenant, buscar_usuario_por_id,
    atualizar_usuario
)
from database.conexao_supabase import get_supabase_client, get_tenant_id

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

SUPABASE_URL = os.getenv("SUPABASE_URL", "http://localhost:8000")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Preencha email e senha.", "warning")
            return render_template('auth/login.html')

        try:
            resp = requests.post(
                f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
                json={"email": email, "password": password},
                headers={
                    "apikey": SUPABASE_KEY,
                    "Content-Type": "application/json"
                }
            )

            if resp.status_code != 200:
                flash("Email ou senha inválidos.", "error")
                return render_template('auth/login.html')

            auth_data = resp.json()
            access_token = auth_data["access_token"]
            auth_user_id = auth_data["user"]["id"]
            auth_email = auth_data["user"]["email"]

            jwt_payload = verificar_jwt(access_token)
            if not jwt_payload:
                flash("Erro ao verificar token.", "error")
                return render_template('auth/login.html')

            usuario = buscar_usuario_por_auth(auth_user_id)
            if not usuario:
                flash("Usuário não encontrado. Contate o administrador.", "error")
                return render_template('auth/login.html')

            if not usuario.get("ativo"):
                flash("Usuário desativado. Contate o administrador.", "error")
                return render_template('auth/login.html')

            session["user"] = usuario
            session["access_token"] = access_token
            session.permanent = False

            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('admin.dashboard'))

        except requests.RequestException as e:
            flash(f"Erro de conexão com o servidor de autenticação.", "error")
            print(f"Auth error: {e}")
            return render_template('auth/login.html')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Sessão encerrada.", "info")
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
@role_required('superadmin')
def register():
    if request.method == 'POST':
        tenant_nome = request.form.get('tenant_nome', '').strip()
        tenant_slug = request.form.get('tenant_slug', '').strip()
        admin_nome = request.form.get('admin_nome', '').strip()
        admin_email = request.form.get('admin_email', '').strip()
        admin_password = request.form.get('admin_password', '')

        if not all([tenant_nome, tenant_slug, admin_nome, admin_email, admin_password]):
            flash("Preencha todos os campos.", "warning")
            return render_template('auth/register.html')

        try:
            client = get_supabase_client()

            tenant_result = criar_tenant({"nome": tenant_nome, "slug": tenant_slug})
            if not tenant_result:
                flash("Erro ao criar tenant.", "error")
                return render_template('auth/register.html')

            tenant_id = tenant_result["id"]

            auth_resp = requests.post(
                f"{SUPABASE_URL}/auth/v1/signup",
                json={"email": admin_email, "password": admin_password},
                headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
            )

            if auth_resp.status_code not in (200, 201, 204):
                client.table("tenants").delete().eq("id", tenant_id).execute()
                flash(f"Erro ao criar usuário de autenticação: {auth_resp.text}", "error")
                return render_template('auth/register.html')

            auth_user_id = auth_resp.json()["user"]["id"]

            criar_usuario({
                "tenant_id": tenant_id,
                "auth_user_id": auth_user_id,
                "nome": admin_nome,
                "email": admin_email,
                "papel": "admin",
            })

            flash(f"Tenant '{tenant_nome}' e admin '{admin_email}' criados com sucesso!", "success")
            return redirect(url_for('admin.dashboard'))

        except Exception as e:
            flash(f"Erro: {e}", "error")
            return render_template('auth/register.html')

    return render_template('auth/register.html')


@auth_bp.route('/usuarios', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'superadmin')
def gerenciar_usuarios():
    usuario = g.usuario
    tenant_id = usuario.get("tenant_id")

    if usuario.get("papel") == "superadmin" and request.args.get("tenant_id"):
        tenant_id = request.args["tenant_id"]

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        papel = request.form.get('papel', 'rh')

        if not all([nome, email, password]):
            flash("Preencha todos os campos.", "warning")
            return redirect(url_for('auth.gerenciar_usuarios', tenant_id=tenant_id))

        try:
            auth_resp = requests.post(
                f"{SUPABASE_URL}/auth/v1/signup",
                json={"email": email, "password": password},
                headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
            )

            if auth_resp.status_code not in (200, 201, 204):
                flash(f"Erro ao criar usuário: {auth_resp.text}", "error")
                return redirect(url_for('auth.gerenciar_usuarios', tenant_id=tenant_id))

            auth_user_id = auth_resp.json()["user"]["id"]

            criar_usuario({
                "tenant_id": tenant_id,
                "auth_user_id": auth_user_id,
                "nome": nome,
                "email": email,
                "papel": papel,
            })

            flash(f"Usuário '{nome}' criado como {papel}!", "success")
        except Exception as e:
            flash(f"Erro: {e}", "error")

        return redirect(url_for('auth.gerenciar_usuarios', tenant_id=tenant_id))

    usuarios = listar_usuarios_do_tenant(tenant_id)
    tenants = listar_tenants() if usuario.get("papel") == "superadmin" else []
    return render_template('auth/usuarios.html', usuarios=usuarios, tenants=tenants, tenant_id=tenant_id)
