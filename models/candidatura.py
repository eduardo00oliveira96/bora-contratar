from models.db import get_db_connection

def create_candidatura(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO candidaturas (
            vaga_id, nome, cpf, telefone, resumo, email, curriculo
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("vaga_id"),
        data.get("nome"),
        data.get("cpf"),
        data.get("telefone"),
        data.get("resumo"),
        data.get("email"),
        data.get("curriculo")
    ))
    conn.commit()
    candidatura_id = cursor.lastrowid
    conn.close()
    return candidatura_id

def update_candidatura_ai_eval(candidatura_id, nota, analise, fortes, gaps, recomendacao, tags=""):
    conn = get_db_connection()
    conn.execute("""
        UPDATE candidaturas SET
            nota = ?, analise_detalhada = ?, pontos_fortes = ?,
            gaps_atencao = ?, recomendacao = ?, tags = ?
        WHERE id = ?
    """, (
        nota, analise, fortes, gaps, recomendacao, tags, candidatura_id
    ))
    conn.commit()
    conn.close()

def get_candidaturas_by_vaga(vaga_id):
    conn = get_db_connection()
    cands = conn.execute("SELECT * FROM candidaturas WHERE vaga_id = ? ORDER BY nota DESC", (vaga_id,)).fetchall()
    conn.close()
    return cands

def get_candidatura_by_id(candidatura_id):
    conn = get_db_connection()
    cand = conn.execute("""
        SELECT c.*, v.titulo as titulo_vaga 
        FROM candidaturas c JOIN vagas v ON c.vaga_id = v.id 
        WHERE c.id = ?
    """, (candidatura_id,)).fetchone()
    conn.close()
    return cand

def update_candidatura_status(candidatura_id, status):
    conn = get_db_connection()
    conn.execute("UPDATE candidaturas SET status = ? WHERE id = ?", (status, candidatura_id))
    conn.commit()
    conn.close()

def get_candidatura_by_cpf(cpf, vaga_id=None):
    """Retorna uma candidatura existente pelo CPF.
       Se vaga_id for fornecido, tenta achar especificamente daquela vaga para update direto.
       Caso não ache, tenta pegar o perfil global mais recente do CPF para apenas preenchimento.
    """
    conn = get_db_connection()
    candidatura = None
    
    if vaga_id:
        candidatura = conn.execute("SELECT * FROM candidaturas WHERE cpf = ? AND vaga_id = ?", (cpf, vaga_id)).fetchone()
    
    # Se não achou na vaga (ou não passou a vaga), pega do histórico global (mais recente)
    if not candidatura:
        candidatura = conn.execute("SELECT * FROM candidaturas WHERE cpf = ? ORDER BY id DESC LIMIT 1", (cpf,)).fetchone()
        
    conn.close()
    return candidatura

def update_candidatura_info(candidatura_id, data):
    """Atualiza dados do candidato sem criar uma linha nova quando já tem praquela vaga."""
    conn = get_db_connection()
    conn.execute("""
        UPDATE candidaturas SET
            nome = ?, telefone = ?, email = ?, curriculo = ?, resumo = ?
        WHERE id = ?
    """, (
        data.get("nome"),
        data.get("telefone"),
        data.get("email"),
        data.get("curriculo"),
        data.get("resumo"),
        candidatura_id
    ))
    conn.commit()
    conn.close()