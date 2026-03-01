import streamlit as st
import pathlib

st.set_page_config(
    page_title="Portal Bora Contratar",
    page_icon="💼",
    layout="wide"
)

# Definição das páginas
lista_page = st.Page(
    "pages\cadastro_vagas.py",
    title="Cadastro de Vagas",
    icon="📋",
    default=True
)

detalhe_page = st.Page(
    "pages\concorrer_vaga.py",
    title="Lista de Vagas",
    icon="📂"
)

avaliacao_page = st.Page(
    pathlib.Path("pages/avaliar_curriculos.py"),
    title="Avaliação de Currículos",
    icon="📊")

# Sistema de Navegação
pg = st.navigation([lista_page, detalhe_page, avaliacao_page])
pg.run()