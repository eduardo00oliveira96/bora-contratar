"""
Cria o Superadmin do sistema Bora Contratar.
Use: python scripts/criar_superadmin.py
"""

import os
import sys
import getpass
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database.conexao_supabase import get_supabase_client, TENANT_SLUG_PADRAO

SUPABASE_URL = os.getenv("SUPABASE_URL", "http://localhost:8000")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

EMAIL = os.getenv("SUPERADMIN_EMAIL") or input("Email do superadmin: ").strip()
PASSWORD = os.getenv("SUPERADMIN_PASSWORD") or getpass.getpass("Senha do superadmin: ")


def main():
    client = get_supabase_client()

    tenants = client.table("tenants").select("id").eq("slug", TENANT_SLUG_PADRAO).execute()
    if tenants.data:
        tenant_id = tenants.data[0]["id"]
        print(f"Tenant encontrado: {tenant_id}")
    else:
        result = client.table("tenants").insert({
            "nome": "Bora Contratar",
            "slug": TENANT_SLUG_PADRAO,
        }).execute()
        tenant_id = result.data[0]["id"]
        print(f"Tenant criado: {tenant_id}")

    existing = client.table("usuarios").select("id").eq("email", EMAIL).limit(1).execute()
    if existing.data:
        print(f"Superadmin já existe: {existing.data[0]['id']}")
        return

    print(f"Criando usuário auth para {EMAIL}...")
    resp = requests.post(
        f"{SUPABASE_URL}/auth/v1/signup",
        json={"email": EMAIL, "password": PASSWORD},
        headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
    )

    if resp.status_code not in (200, 201, 204):
        print(f"Erro ao criar auth user: {resp.status_code} {resp.text}")
        return

    auth_user_id = resp.json()["user"]["id"]
    print(f"Auth user criado: {auth_user_id}")

    client.table("usuarios").insert({
        "tenant_id": tenant_id,
        "auth_user_id": auth_user_id,
        "nome": "Superadmin Bora Contratar",
        "email": EMAIL,
        "papel": "superadmin",
    }).execute()

    print(f"\nSuperadmin criado com sucesso!")
    print(f"  Email: {EMAIL}")
    print(f"  Papel: superadmin")


if __name__ == "__main__":
    main()
