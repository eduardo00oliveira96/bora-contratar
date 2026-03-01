import sqlite3
import os
import streamlit as st
from services.extarir_texto import extrair_texto_pdf
from services.obter_dados_vaga import obter_dados_vaga
from ai.agente_avaliar_cv import avaliar_cv


UPLOAD_DIR = "upload_curriculos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ==============================
# CONEXÃO COM BANCO
# ==============================
conn = sqlite3.connect("bd_bora_contratar.db", check_same_thread=False)
cursor = conn.cursor()

# ==============================
# CONFIGURAÇÃO DA PÁGINA
# ==============================
st.set_page_config(
    page_title="Portal de Carreiras | Bora Contratar",
    page_icon="💼",
    layout="wide"
)

# ==============================
# ESTILIZAÇÃO CSS
# ==============================
st.markdown("""
    <style>
    .vaga-title {
        color: #1e293b;
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .badge {
        background-color: #f0f2f6;
        color: #475569;
        padding: 4px 12px;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 500;
        margin-right: 8px;
        display: inline-block;
        margin-top: 5px;
    }

    .vaga-salary {
        color: #059669;
        font-weight: 600;
        font-size: 1rem;
    }

    div.stButton > button {
        background-color: transparent;
        color: #007bff;
        border: solid 1px #007bff;
        padding: 5px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)


# ==============================
# BUSCAR VAGAS NO BANCO
# ==============================
def buscar_vagas():
    cursor.execute("SELECT * FROM vagas order by id desc")
    colunas = [desc[0] for desc in cursor.description]
    dados = cursor.fetchall()

    vagas = []
    for row in dados:
        vaga_dict = dict(zip(colunas, row))

        # Converter benefícios string para lista
        vaga_dict["beneficios"] = (
            vaga_dict["beneficios"].split(",")
            if vaga_dict["beneficios"]
            else []
        )

        vagas.append(vaga_dict)

    return vagas


# ==============================
# TELA LISTAGEM
# ==============================
def renderizar_lista():
    st.title("Oportunidades Abertas")
    st.write("Encontre sua próxima oportunidade profissional.")

    vagas = buscar_vagas()

    # FILTROS
    st.sidebar.subheader("Filtros")
    busca = st.sidebar.text_input("Buscar por cargo")
    tipo = st.sidebar.selectbox(
        "Local de Trabalho",
        ["Todos", "Remoto", "Presencial", "Híbrido"]
    )

    vagas_filtradas = [
        v for v in vagas
        if (busca.lower() in v["titulo"].lower())
        and (tipo == "Todos" or v["local_trabalho"] == tipo)
    ]

    if not vagas_filtradas:
        st.info("Nenhuma vaga encontrada.")
        return

    for vaga in vagas_filtradas:
        with st.container(border=True):

            col_text, col_price = st.columns([4, 1])

            with col_text:
                st.markdown(
                    f'<div class="vaga-title">{vaga["titulo"]}</div>',
                    unsafe_allow_html=True
                )

                st.markdown(f"""
                    <span class="badge">💼 {vaga["contrato_trabalho"]}</span>
                    <span class="badge">📍 {vaga["local_trabalho"]}</span>
                """, unsafe_allow_html=True)

            with col_price:
                if vaga["divulgacao_salario"] == "Inserir Salário" and vaga["salario"]:
                    salario_formatado = f"R$ {vaga['salario']:,.2f}"
                else:
                    salario_formatado = "Salário a combinar"

                st.markdown(
                    f'<div style="text-align:right" class="vaga-salary">{salario_formatado}</div>',
                    unsafe_allow_html=True
                )

            if st.button("Ver detalhes →", key=f"btn_{vaga['id']}"):
                st.query_params["job"] = str(vaga["id"])
                st.rerun()


# ==============================
# TELA DETALHES
# ==============================
def renderizar_detalhes(vaga_id):
    cursor.execute("SELECT * FROM vagas WHERE id = ?", (vaga_id,))
    vaga = cursor.fetchone()

    if not vaga:
        st.error("Vaga não encontrada.")
        if st.button("Voltar"):
            st.query_params.clear()
            st.rerun()
        return

    colunas = [desc[0] for desc in cursor.description]
    vaga = dict(zip(colunas, vaga))

    beneficios = vaga["beneficios"].split(",") if vaga["beneficios"] else []

    if st.button("← Voltar para todas as vagas"):
        st.query_params.clear()
        st.rerun()

    st.title(vaga["titulo"])
    st.caption(f"💼 {vaga['contrato_trabalho']} | 📍 {vaga['local_trabalho']} | ID: {vaga['id']}")

    st.divider()

    col_info, col_side = st.columns([2, 1])

    with col_info:
        st.subheader("Descrição da Vaga")
        st.write(vaga["descricao"])

        st.subheader("Responsabilidades")
        st.write(vaga["requisitos"])

        st.subheader("Habilidades")
        st.write(vaga["habilidades"])

        st.subheader("Benefícios")
        for bene in beneficios:
            st.markdown(f"- {bene}")

    with col_side:
        with st.container(border=True):
            st.markdown("### Candidate-se")

            nome = st.text_input("Nome Completo")
            cpf = st.text_input("CPF")
            numero = st.text_input("Número de Telefone")
            email = st.text_input("E-mail")
            curriculo = st.file_uploader("Anexe seu currículo (PDF)", type=["pdf"],max_upload_size=10)

            if st.button("Enviar Candidatura", type="primary", use_container_width=True):
                if nome and cpf and numero and email and curriculo:
                    
                    caminho_pdf = os.path.join(
                        UPLOAD_DIR,
                        curriculo.name
                    )

                    with open(caminho_pdf, "wb") as f:
                        f.write(curriculo.read())

                    # Extrair texto
                    texto_extraido = extrair_texto_pdf(caminho_pdf)

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
                                       feedback TEXT,
                                       nota INTEGER,
                                       analise_detalhada TEXT,
                                       pontos_fortes TEXT,
                                       gaps_atencao TEXT,
                                       recomendacao TEXT,
                                       tags TEXT,
                                       curriculo TEXT,
                                       FOREIGN KEY (vaga_id) REFERENCES vagas (id)
                                   );
                                   """)
                    
                    cursor.execute("""
                                   INSERT INTO candidaturas (vaga_id, nome, cpf, telefone, resumo, email, curriculo)
                                   VALUES (?, ?, ?, ?, ?, ?, ?);
                                   """, (
                                       vaga["id"],
                                       nome,
                                       cpf,
                                       numero,
                                       texto_extraido,
                                       email,
                                       caminho_pdf
                                   ))
                    conn.commit()
                    st.success("Candidatura enviada com sucesso!")
                    st.balloons()
                    #analisar curriculo com ia
                    
                    vaga_info = obter_dados_vaga(vaga["id"])
                    avaliar_cv(texto_extraido, vaga_info)
                    
                    
                else:
                    st.warning("Preencha todos os campos.")



# ==============================
# ROTEADOR
# ==============================
id_na_url = st.query_params.get("job")

if id_na_url:
    renderizar_detalhes(id_na_url)
else:
    renderizar_lista()