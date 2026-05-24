from models.db import get_db_connection

def get_all_vagas(active_only=False):
    conn = get_db_connection()
    query = "SELECT * FROM vagas"
    if active_only:
        query += " WHERE ativo = 1"
    query += " ORDER BY id DESC"
    vagas = conn.execute(query).fetchall()
    conn.close()
    return vagas

def get_vaga_by_id(vaga_id):
    conn = get_db_connection()
    vaga = conn.execute("SELECT * FROM vagas WHERE id = ?", (vaga_id,)).fetchone()
    conn.close()
    return vaga

def create_vaga(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO vagas (
            titulo, descricao, local_trabalho, contrato_trabalho,
            requisitos, habilidades, salario, divulgacao_salario,
            beneficios, user_created
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("titulo"),
        data.get("descricao"),
        data.get("local_trabalho"),
        data.get("contrato_trabalho"),
        data.get("requisitos"),
        data.get("habilidades"),
        data.get("salario"),
        data.get("divulgacao_salario"),
        data.get("beneficios"),
        data.get("user_created", "Admin")
    ))
    conn.commit()
    vaga_id = cursor.lastrowid
    conn.close()
    return vaga_id

def update_vaga(vaga_id, data):
    conn = get_db_connection()
    conn.execute("""
        UPDATE vagas SET 
            titulo = ?, descricao = ?, local_trabalho = ?, contrato_trabalho = ?,
            requisitos = ?, habilidades = ?, salario = ?, divulgacao_salario = ?,
            beneficios = ?
        WHERE id = ?
    """, (
        data.get("titulo"),
        data.get("descricao"),
        data.get("local_trabalho"),
        data.get("contrato_trabalho"),
        data.get("requisitos"),
        data.get("habilidades"),
        data.get("salario"),
        data.get("divulgacao_salario"),
        data.get("beneficios"),
        vaga_id
    ))
    conn.commit()
    conn.close()

def close_vaga(vaga_id):
    conn = get_db_connection()
    conn.execute("UPDATE vagas SET ativo = 0 WHERE id = ?", (vaga_id,))
    conn.commit()
    conn.close()