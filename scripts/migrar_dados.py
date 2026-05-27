"""
Script de migração: SQLite → Supabase

1. Cria tenant padrão
2. Migra vagas (com mapeamento de ID antigo → novo UUID)
3. Migra candidaturas → candidatos + candidaturas
4. Faz upload dos currículos PDF para o Storage
"""
import os
import sys
import sqlite3
import time
import uuid as uuid_lib

sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database.conexao_supabase import get_supabase_client, TENANT_SLUG_PADRAO

DB_PATH = os.path.join(BASE_DIR, "database", "bd_bora_contratar.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "upload_curriculos")
BUCKET_NAME = "curriculos"


def clean_text(value):
    """Remove null characters and other problematic chars from text."""
    if value is None:
        return None
    return value.replace('\u0000', '').replace('\x00', '')

def conectar_sqlite():
    if not os.path.exists(DB_PATH):
        print(f"Arquivo SQLite não encontrado: {DB_PATH}")
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tenant():
    client = get_supabase_client()
    existing = client.table("tenants").select("id").eq("slug", TENANT_SLUG_PADRAO).limit(1).execute()
    if existing.data:
        tenant_id = existing.data[0]["id"]
        print(f"Tenant ja existe: {tenant_id}")
        return tenant_id

    result = client.table("tenants").insert({
        "nome": "Bora Contratar",
        "slug": TENANT_SLUG_PADRAO,
    }).execute()
    tenant_id = result.data[0]["id"]
    print(f"Tenant criado: {tenant_id}")
    return tenant_id

def migrar_vagas(conn, tenant_id):
    client = get_supabase_client()

    existing = client.table("vagas").select("id").eq("tenant_id", tenant_id).limit(1).execute()
    if existing.data:
        print("Vaga(s) ja migradas, limpando para refazer...")
        client.table("candidaturas").delete().eq("tenant_id", tenant_id).execute()
        client.table("candidatos").delete().eq("tenant_id", tenant_id).execute()
        client.table("vagas").delete().eq("tenant_id", tenant_id).execute()

    vagas = conn.execute("SELECT * FROM vagas").fetchall()
    mapeamento = {}
    print(f"Migrando {len(vagas)} vaga(s)...")
    for v in vagas:
        old_id = v["id"]
        new_id = str(uuid_lib.uuid4())

        divulgar = v["divulgacao_salario"] in ("Inserir Salário", True, 1) if v["divulgacao_salario"] else False

        payload = {
            "id": new_id,
            "tenant_id": tenant_id,
            "titulo": v["titulo"],
            "descricao": clean_text(v["descricao"]),
            "local_trabalho": v["local_trabalho"],
            "tipo_contrato": v["contrato_trabalho"],
            "requisitos": clean_text(v["requisitos"]),
            "habilidades": clean_text(v["habilidades"]),
            "salario": v["salario"],
            "divulgar_salario": divulgar,
            "beneficios": v["beneficios"],
            "user_created": v["user_created"] or "Admin",
            "ativo": bool(v["ativo"]),
        }
        client.table("vagas").insert(payload).execute()
        mapeamento[old_id] = new_id
        print(f"  Vaga {old_id} -> {new_id}: {v['titulo']}")
    return mapeamento

def migrar_candidaturas(conn, tenant_id, vaga_map):
    client = get_supabase_client()
    candidaturas = conn.execute("SELECT * FROM candidaturas").fetchall()
    print(f"Migrando {len(candidaturas)} candidatura(s)...")

    for c in candidaturas:
        new_vaga_id = vaga_map.get(c["vaga_id"])
        if not new_vaga_id:
            print(f"  Pulando candidatura {c['id']}: vaga {c['vaga_id']} não encontrada no mapeamento")
            continue

        cpf = c["cpf"] or ""
        candidato_id = None

        if cpf:
            existing = client.table("candidatos").select("id").eq("tenant_id", tenant_id).eq("cpf", cpf).limit(1).execute()
            if existing.data:
                candidato_id = existing.data[0]["id"]
            else:
                cand_result = client.table("candidatos").insert({
                    "tenant_id": tenant_id,
                    "nome": c["nome"],
                    "cpf": cpf,
                    "telefone": c["telefone"],
                    "email": c["email"],
                }).execute()
                candidato_id = cand_result.data[0]["id"]

        curriculo_path = c["curriculo"] or ""
        link_curriculo = ""

        if curriculo_path and os.path.exists(curriculo_path):
            try:
                safe_name = f"{int(time.time())}_{uuid_lib.uuid4().hex[:8]}_{os.path.basename(curriculo_path)}"
                with open(curriculo_path, "rb") as f:
                    file_content = f.read()
                client.storage.from_(BUCKET_NAME).upload(
                    path=safe_name,
                    file=file_content,
                    file_options={"content-type": "application/pdf"}
                )
                link_curriculo = safe_name
                print(f"    Currículo upado: {safe_name}")
            except Exception as e:
                print(f"    Erro ao upar currículo {curriculo_path}: {e}")

        payload = {
            "tenant_id": tenant_id,
            "vaga_id": new_vaga_id,
            "candidato_id": candidato_id,
            "status": c["status"] or "Em análise",
            "nota": c["nota"],
            "resumo": clean_text(c["resumo"]),
            "analise_detalhada": clean_text(c["analise_detalhada"]),
            "pontos_fortes": c["pontos_fortes"],
            "gaps_atencao": c["gaps_atencao"],
            "recomendacao": c["recomendacao"],
            "tags": c["tags"],
            "link_curriculo": link_curriculo,
            "etapa_entrevista": c["etapa_entrevista"],
        }
        client.table("candidaturas").insert(payload).execute()
        print(f"  Candidatura {c['id']} migrada (vaga {c['vaga_id']} -> {new_vaga_id})")

def main():
    print("=== Iniciando migracao SQLite -> Supabase ===\n")

    conn = conectar_sqlite()
    if not conn:
        print("Nada a migrar.")
        return

    try:
        client = get_supabase_client()
        try:
            buckets = client.storage.list_buckets()
            if not any(b.get('name') == BUCKET_NAME for b in buckets):
                import requests
                from database.conexao_supabase import SUPABASE_URL, SUPABASE_KEY
                headers = {'apikey': SUPABASE_KEY, 'Authorization': 'Bearer ' + SUPABASE_KEY, 'Content-Type': 'application/json'}
                requests.post(SUPABASE_URL + '/storage/v1/bucket', json={'name': BUCKET_NAME, 'public': False}, headers=headers)
                print(f"Bucket '{BUCKET_NAME}' criado.")
        except Exception as e:
            print(f"Nota: bucket ja pode existir: {e}")

        tenant_id = criar_tenant()

        vaga_map = migrar_vagas(conn, tenant_id)

        migrar_candidaturas(conn, tenant_id, vaga_map)

        print("\n=== Migração concluída com sucesso! ===")
    except Exception as e:
        print(f"\nErro durante a migração: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
