import streamlit as st
import sqlite3
import os

# ==============================
# CONFIGURAÇÃO E ESTILO (UI)
# ==============================
st.set_page_config(page_title="Bora Contratar | Pro", layout="wide", page_icon="📊")

def local_css():
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        .stExpander { border: 1px solid #e0e0e0; border-radius: 10px; background-color: white; margin-bottom: 1rem; }
        .candidate-card { 
            padding: 15px; border-radius: 8px; border-left: 5px solid #007bff; 
            background: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px;
        }
        .status-badge {
            padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;
        }
        .status-aprovado { background-color: #d4edda; color: #155724; }
        .status-reprovado { background-color: #f8d7da; color: #721c24; }
        .status-pendente { background-color: #fff3cd; color: #856404; }
        </style>
    """, unsafe_allow_html=True)

local_css()

# ==============================
# FUNÇÕES DE DADOS (DEVELOPMENT)
# ==============================
def get_db_connection():
    conn = sqlite3.connect("bd_bora_contratar.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas pelo nome
    return conn

def update_status(candidato_id, novo_status):
    conn = get_db_connection()
    conn.execute("UPDATE candidaturas SET status = ? WHERE id = ?", (novo_status, candidato_id))
    conn.commit()
    conn.close()

def update_nota(candidato_id, nota):
    conn = get_db_connection()
    conn.execute("UPDATE candidaturas SET nota = ? WHERE id = ?", (nota, candidato_id))
    conn.commit()
    conn.close()

# ==============================
# MODAL DE DETALHES (UX)
# ==============================
@st.dialog("📄 Detalhes do Candidato", width="large")
def modal_detalhes(candidato_id):
    conn = get_db_connection()
    candidato = conn.execute("""
        SELECT c.*, v.titulo as titulo_vaga 
        FROM candidaturas c JOIN vagas v ON c.vaga_id = v.id 
        WHERE c.id = ?
    """, (candidato_id,)).fetchone()
    
    if candidato:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.title(f"👤 {candidato['nome']}")
            st.caption(f"Vaga: {candidato['titulo_vaga']}")
            st.write(f"📧 **E-mail:** {candidato['email']}")
            st.write(f"📱 **WhatsApp:** {candidato['telefone']}")
            with st.expander("📑 Resumo do Candidato",):
                st.write(f"📋 **Resumo:** {candidato['resumo']}",)
        
        with col2:
            st.metric("Avaliação", f"{candidato['nota']}/10" if candidato['nota'] else "S/N")
            st.write(f"Status: `{candidato['status']}`")

        st.divider()
        
        # Ações
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("✅ Aprovar", use_container_width=True):
                update_status(candidato_id, "Aprovado")
                st.rerun()
        with c2:
            if st.button("❌ Reprovar", use_container_width=True, type="secondary"):
                update_status(candidato_id, "Reprovado")
                st.rerun()
        with c3:
            if candidato['curriculo'] and os.path.exists(candidato['curriculo']):
                with open(candidato['curriculo'], "rb") as f:
                    st.download_button("📂 Baixar CV", f, file_name=f"CV_{candidato['nome']}.pdf", use_container_width=True)

        st.divider()
        nova_nota = st.slider("Ajustar Nota", 0, 10, int(candidato['nota'] or 5))
        if st.button("Salvar Nota"):
            update_nota(candidato_id, nova_nota)
            st.success("Nota atualizada!")
            st.rerun()

# ==============================
# INTERFACE PRINCIPAL
# ==============================
st.title("📊 Painel de Recrutamento")
st.markdown("Gerencie suas vagas e avalie candidatos com agilidade.")

conn = get_db_connection()
vagas = conn.execute("SELECT * FROM vagas ORDER BY id DESC").fetchall()

if not vagas:
    st.info("Nenhuma vaga encontrada no sistema.")
else:
    for vaga in vagas:
        # Busca candidatos da vaga
        candidatos = conn.execute("SELECT * FROM candidaturas WHERE vaga_id = ?", (vaga['id'],)).fetchall()
        
        with st.expander(f"💼 {vaga['titulo']} — {len(candidatos)} candidatos"):
            # Info da Vaga em colunas
            v_col1, v_col2 = st.columns([3, 1])
            with v_col1:
                st.markdown(f"**Descrição:** {vaga['descricao']}")
                st.markdown(f"📍 `{vaga['local_trabalho']}` | 📄 `{vaga['contrato_trabalho']}` | 💰 `{vaga['salario'] if vaga['salario'] is not None else 'Salário a combinar'}`")
            
            with v_col2:
                st.markdown("**Habilidades Requeridas:**")
                for h in vaga['habilidades'].split('\n'):
                    if h: st.markdown(f"- {h}")

            st.divider()
            
            # Grid de Candidatos
            if not candidatos:
                st.caption("Nenhum candidato inscrito.")
            else:
                for cand in candidatos:
                    # Lógica de cores para status
                    status_class = "status-pendente"
                    if cand['status'] == "Aprovado": status_class = "status-aprovado"
                    elif cand['status'] == "Reprovado": status_class = "status-reprovado"

                    # Card customizado com HTML/CSS
                    st.markdown(f"""
                        <div class="candidate-card">
                            <span style="float: right;" class="status-badge {status_class}">{cand['status']}</span>
                            <strong>{cand['nome']}</strong><br>
                            <small>Nota: {cand['nota'] if cand['nota'] else '—'}</small>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Botão de ação (Streamlit Nativo)
                    if st.button(f"Avaliar {cand['nome']}", key=f"btn_{cand['id']}"):
                        modal_detalhes(cand['id'])

conn.close()