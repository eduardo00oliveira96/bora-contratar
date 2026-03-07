import os

import streamlit as st
import sqlite3
import time

DB_PATH = "database/bd_bora_contratar.db"

conn = sqlite3.connect(DB_PATH, check_same_thread=False)

cursor = conn.cursor()


st.set_page_config(page_title="Cadastro de Vagas", page_icon=":briefcase:")

def init_state():
    defaults = {
        "input_vaga": "",
        "input_descricao": "",
        "local_trabalho": None,
        "contrato_trabalho": None,
        "input_requisitos": "",
        "input_habilidades": "",
        "opcao_salario": "Salário a combinar",
        "salario": 0.0,
        "beneficios": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()
with st.container(border=True):
    st.title("Cadastro de Vagas")

    input_vaga = st.text_input(
        "Digite o nome da vaga:",
        key="input_vaga"
    )

    input_descricao = st.text_area(
        "Digite a descrição da vaga:",
        key="input_descricao"
    )

    local_trabalho = st.pills(
        "Selecione o local de trabalho:",
        ["Remoto", "Presencial", "Híbrido"],
        key="local_trabalho"
    )

    contrato_trabalho = st.pills(
        "Selecione o tipo de contrato:",
        ["CLT", "PJ", "Temporário", "Estágio"],
        key="contrato_trabalho"
    )

    input_requisitos = st.text_area(
        "Digite as responsabilidades da vaga:",
        key="input_requisitos"
    )

    habilidades = st.text_area(
        "Digite as habilidades necessárias:",
        key="input_habilidades"
    )

    opcao_salario = st.radio(
        "Deseja informar o salário?",
        ["Salário a combinar", "Inserir Salário"],
        key="opcao_salario"
    )

    salario = None

    if opcao_salario == "Inserir Salário":
        salario = st.number_input(
            "Digite o salário:",
            min_value=0.0,
            step=100.0,
            format="%.2f",
            key="salario"
        )

    beneficios = st.pills(
        "Selecione os benefícios:",
        ["Vale Refeição", "Vale Transporte", "Plano de Saúde",
         "Plano Odontológico", "Auxílio Home Office", "Gympass"],
        selection_mode='multi',
        key="beneficios"
    )

    submitted = st.button("Cadastrar Vaga", key="submit_button")
    

if submitted:
    if (
        input_vaga and input_descricao and local_trabalho and contrato_trabalho
        and input_requisitos and habilidades and beneficios
    ):

        if opcao_salario == "Salário a combinar":
            salario = None

        cursor.execute("""
            INSERT INTO vagas (
                titulo, descricao, local_trabalho, contrato_trabalho,
                requisitos, habilidades, salario, divulgacao_salario,
                beneficios, user_created
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            input_vaga,
            input_descricao,
            local_trabalho,
            contrato_trabalho,
            input_requisitos,
            habilidades,
            salario,
            opcao_salario,
            ",".join(beneficios),
            st.session_state.get("user_name", "Usuário Desconhecido")
        ))

        conn.commit()

        st.success("Vaga cadastrada com sucesso!")
        st.toast("Sua vaga foi salva e está pronta para ser divulgada.", icon="✅",duration='short')

        # RESET DOS CAMPOS APÓS CADASTRO
        for key in [
            "input_vaga", "input_descricao", "local_trabalho",
            "contrato_trabalho", "input_requisitos",
            "input_habilidades", "beneficios", "salario"
        ]:
            if key in st.session_state:
                del st.session_state[key]

        with st.spinner("Salvando...", show_time=True):
            time.sleep(3)
            st.rerun()
        
        
    else:
        st.warning("Por favor, preencha todos os campos.")
        
        