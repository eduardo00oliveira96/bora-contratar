import httpx
import os
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("SUPABASE_URL")
SERVICE_KEY = os.getenv("SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

headers = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
}

migrations_dir = "supabase/migrations"
migrations = sorted(os.listdir(migrations_dir))

print(f"Conectando a {URL}")
print(f"Encontradas {len(migrations)} migrations\n")

for m in migrations:
    path = os.path.join(migrations_dir, m)
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()

    print(f"[{m}] Executando...")

    resp = httpx.post(
        f"{URL}/sql",
        json={"query": sql},
        headers=headers,
        timeout=30,
    )

    if resp.status_code in (200, 201):
        print(f"  OK ({resp.status_code})")
    elif resp.status_code == 404:
        resp2 = httpx.post(
            f"{URL}/rest/v1/rpc/pgexecute",
            json={"query": sql},
            headers=headers,
            timeout=30,
        )
        if resp2.status_code in (200, 201):
            print(f"  OK via rpc ({resp2.status_code})")
        else:
            print(f"  FALHA: {resp2.status_code} {resp2.text[:200]}")
    else:
        print(f"  FALHA: {resp.status_code} {resp.text[:200]}")

print("\nConcluido!")
