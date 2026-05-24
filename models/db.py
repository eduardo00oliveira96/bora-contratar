import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = "database/bd_bora_contratar.db"

def get_db_connection():
    """Retorna uma conexão com o banco de dados configurada para acessar colunas por nome."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Inicializa o banco de dados com as tabelas de vagas e candidaturas.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vagas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT,
                descricao TEXT,
                local_trabalho TEXT,
                contrato_trabalho TEXT,
                requisitos TEXT,
                habilidades TEXT,
                salario NUMERIC,
                divulgacao_salario TEXT,
                beneficios TEXT,
                user_created TEXT,
                ativo INTEGER DEFAULT 1
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidaturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vaga_id INTEGER,
                nome TEXT,
                cpf TEXT,
                telefone TEXT,
                resumo TEXT,
                email TEXT,
                status TEXT DEFAULT 'Em análise',
                nota INTEGER,
                analise_detalhada TEXT,
                pontos_fortes TEXT,
                gaps_atencao TEXT,
                recomendacao TEXT,
                tags TEXT,
                etapa_entrevista TEXT,
                curriculo TEXT,
                FOREIGN KEY (vaga_id) REFERENCES vagas (id)
            );
        """)
        conn.commit()
        logger.info("Banco de dados inicializado com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao inicializar DB: {e}")
        conn.rollback()
    finally:
        conn.close()