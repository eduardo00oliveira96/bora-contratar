import sqlite3
import os
import ast
from streamlit_pdf_viewer import pdf_viewer
import streamlit as st

DB_PATH = "database/bd_bora_contratar.db"

# ==============================
# CONFIGURAÇÃO E ESTILO (UI)
# ==============================
st.set_page_config(page_title="Bora Contratar | Pro", layout="wide", page_icon="📊")

def local_css():
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        .stExpander { border: 1px solid #e0e0e0; border-radius: 10px; background-color: white; }
        .candidate-card { 
            padding: 12px; border-radius: 8px; border-left: 5px solid #007bff; 
            background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px;
        }
        .status-badge { padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; }
        .status-aprovado { background-color: #d4edda; color: #155724; }
        .status-reprovado { background-color: #f8d7da; color: #721c24; }
        .status-pendente { background-color: #fff3cd; color: #856404; }
        
        /* Ajuste para títulos menores no modal */
        .modal-header { font-size: 1.8rem; font-weight: bold; color: #1e1e1e; margin-bottom: 0; }
        </style>
    """, unsafe_allow_html=True)

local_css()

# ==============================
# FUNÇÕES DE APOIO
# ==============================
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def safe_list_eval(data):
    try:
        return ast.literal_eval(data) if data else []
    except:
        return []

# ==============================
# MODAL DE DETALHES (UX REFINADA)
# ==============================
@st.dialog("📄 Detalhes do Candidato", width="large")
def modal_detalhes(candidato_id):
    conn = get_db_connection()
    candidato = conn.execute("""
        SELECT c.*, v.titulo as titulo_vaga 
        FROM candidaturas c JOIN vagas v ON c.vaga_id = v.id 
        WHERE c.id = ?
    """, (candidato_id,)).fetchone()
    
    if not candidato:
        st.error("Candidato não encontrado.")
        return

    # --- HEADER DO MODAL ---
    st.markdown(f"<p class='modal-header'>👤 {candidato['nome']}</p>", unsafe_allow_html=True)
    st.caption(f"Candidato para a vaga de **{candidato['titulo_vaga']}**")
    
    col_info, col_actions = st.columns([2.2, 1], gap="large")

    with col_info:
        # Contato Rápido
        st.markdown(f"📧 `{candidato['email']}` | 📱 `{candidato['telefone']}`")
        
        # Resumo Executivo

        # Análise da IA
        st.markdown("### 🤖 Inteligência Artificial")
        st.write(candidato['analise_detalhada'] or "Nenhuma análise detalhada.")
        
        # Pontos Fortes e Fracos Lado a Lado
        e1, e2 = st.columns(2)
        with e1:
            st.markdown("#### ✅ Pontos Fortes")
            for item in safe_list_eval(candidato['pontos_fortes']):
                st.success(item)
        with e2:
            st.markdown("#### ⚠️ Gaps de Atenção")
            for item in safe_list_eval(candidato['gaps_atencao']):
                st.info(item)
            
            

    # Visualizador de PDF Embutido (Evita abrir outro modal)
    with st.expander("📄 Visualizar Currículo Original"):
        if candidato['curriculo'] and os.path.exists(candidato['curriculo']):
            pdf_viewer(candidato['curriculo'], width=700)
        else:
            st.warning("Arquivo PDF não localizado.")

    with col_actions:
        # Painel de Decisão
        st.markdown("### ⚖️ Avaliação")
        
        # Métrica de Score IA
        score = candidato['nota'] or 0
        cor_score = "normal" if score < 70 else "inverse"
        st.metric("Score de Match", f"{score}/100", delta=f"{score-50}% vs média" if score else None)
        
        st.divider()
        
        st.markdown("### 💡 Recomendação")
        st.warning(f"**IA:** {candidato['recomendacao'] or 'Sem recomendação'}")
        
        st.divider()
        
        # Status e Ações
        st.markdown(f"Status Atual: `{candidato['status']}`")
        
        btn_aprov = st.button("✅ Aprovar Candidato", use_container_width=True, type="primary")
        btn_repro = st.button("❌ Reprovar", use_container_width=True)
        
        if btn_aprov:
            # update_status(candidato_id, "Aprovado") -> implementar logica de db
            st.success("Candidato Aprovado!")
            st.rerun()
        if btn_repro:
            # update_status(candidato_id, "Reprovado") -> implementar logica de db
            st.rerun()

        st.divider()
        
        # Ajuste de Nota Manual
        nova_nota = st.slider("Ajuste Manual", 0, 100, int(score))
        if st.button("Salvar Nota Manual", use_container_width=True):
            # update_nota(candidato_id, nova_nota) -> implementar logica de db
            st.toast("Nota atualizada!")

# ==============================
# INTERFACE PRINCIPAL
# ==============================
st.title("📊 Painel de Recrutamento")

conn = get_db_connection()
vagas = conn.execute("SELECT * FROM vagas ORDER BY id DESC").fetchall()

if not vagas:
    st.info("Nenhuma vaga encontrada.")
else:
    for vaga in vagas:
        candidatos = conn.execute("SELECT * FROM candidaturas WHERE vaga_id = ?", (vaga['id'],)).fetchall()
        
        with st.expander(f"💼 {vaga['titulo']} — {len(candidatos)} candidatos"):
            v_col1, v_col2 = st.columns([3, 1])
            with v_col1:
                st.markdown(f"**Descrição:** {vaga['descricao']}")
                st.markdown(f"📍 `{vaga['local_trabalho']}` | 💰 `{vaga['salario'] or 'A combinar'}`")
            
            st.divider()
            
            if not candidatos:
                st.caption("Nenhum inscrito.")
            else:
                # Exibição em colunas para economizar espaço vertical
                for cand in candidatos:
                    status_class = "status-pendente"
                    if cand['status'] == "Aprovado": status_class = "status-aprovado"
                    elif cand['status'] == "Reprovado": status_class = "status-reprovado"

                    c_col1, c_col2 = st.columns([4, 1])
                    with c_col1:
                        st.markdown(f"""
                            <div class="candidate-card">
                                <span style="float: right;" class="status-badge {status_class}">{cand['status']}</span>
                                <strong>{cand['nome']}</strong> | Score IA: {cand['nota'] or '—'}
                            </div>
                        """, unsafe_allow_html=True)
                    with c_col2:
                        if st.button("Avaliar", key=f"btn_{cand['id']}", use_container_width=True):
                            modal_detalhes(cand['id'])

conn.close()