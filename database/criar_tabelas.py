import sqlite3
import os
import logging

# Configuração básica de logging para visualizar erros no console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Caminho do banco de dados
DB_PATH = "database/bd_bora_contratar.db"

# Garante que o diretório existe antes de conectar
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Conexão Global (Cuidado com check_same_thread=False em produção)
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
# Não instanciamos o cursor globalmente aqui para evitar conflitos de fechamento

def init_db():
    """
    Inicializa o banco de dados com as tabelas de vagas e candidaturas.
    Trata erros de conexão, sintaxe SQL e permissões.
    """
    cursor = None
    try:
        # Cria um cursor local para esta operação
        cursor = conn.cursor()
        
        # Tabela de Vagas (Corrigida a vírgula final)
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
        
        # Tabela de Candidaturas
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
        
        # Confirma as transações
        conn.commit()
        logger.info("Banco de dados inicializado com sucesso.")
        return "Banco de dados inicializado com sucesso!"

    except sqlite3.OperationalError as e:
        logger.error(f"Erro operacional no banco de dados (ex: tabela bloqueada, caminho inválido): {e}")
        return f"Erro operacional: {e}"
    
    except sqlite3.DatabaseError as e:
        logger.error(f"Erro geral no banco de dados: {e}")
        # Em caso de erro, tenta reverter mudanças pendentes
        try:
            conn.rollback()
        except:
            pass
        return f"Erro no banco de dados: {e}"
    
    except Exception as e:
        logger.critical(f"Erro inesperado ao inicializar DB: {e}")
        return f"Erro inesperado: {e}"
    
    finally:
        # Garante que o cursor local seja fechado, mas mantém a conexão (conn) aberta
        if cursor:
            cursor.close()

# Exemplo de uso
if __name__ == "__main__":
    mensagem = init_db()
    print(mensagem)