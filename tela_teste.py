import streamlit as st
import re
import base64

def limpar(txt):
    return re.sub(r'\D', '', txt) if txt else ""

st.set_page_config(page_title="Recrutamento Pro", layout="centered")

# --- COMPONENTE V2 COM FORMULÁRIO E ANEXO CUSTOMIZADO ---
HTML = """
<div id="form-container" style="font-family: sans-serif; background: #fff; padding: 25px; border-radius: 15px; border: 1px solid #eee; box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
    <style>
        .field { margin-bottom: 15px; }
        input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; font-size: 15px; outline: none; }
        input:focus { border-color: #007bff; box-shadow: 0 0 0 2px rgba(0,123,255,0.1); }
        label { display: block; font-size: 13px; font-weight: bold; color: #444; margin-bottom: 5px; }
        
        /* Estilização do Upload */
        .file-drop-area {
            position: relative; display: flex; align-items: center; width: 100%; padding: 20px;
            border: 2px dashed #ccc; border-radius: 8px; transition: 0.3s; cursor: pointer; justify-content: center; background: #f9f9f9;
        }
        .file-drop-area:hover { border-color: #007bff; background: #f0f7ff; }
        .file-input { position: absolute; left: 0; top: 0; height: 100%; width: 100%; cursor: pointer; opacity: 0; }
        .file-msg { font-size: 14px; color: #666; }
        
        .btn { width: 100%; background: #007bff; color: white; border: none; padding: 14px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; margin-top: 20px; transition: 0.2s; }
        .btn:hover { background: #0056b3; }
    </style>

    <div class="field">
        <label>Nome Completo</label>
        <input type="text" id="nome" placeholder="Nome do Candidato">
    </div>

    <div style="display: flex; gap: 10px;" class="field">
        <div style="flex:1"><label>CPF</label><input type="text" id="cpf" placeholder="000.000.000-00"></div>
        <div style="flex:1"><label>WhatsApp</label><input type="text" id="tel" placeholder="(00) 00000-0000"></div>
    </div>

    <div class="field">
        <label>E-mail</label>
        <input type="email" id="email" placeholder="exemplo@email.com">
    </div>

    <div class="field">
        <label>Currículo (PDF)</label>
        <div class="file-drop-area" id="drop-area">
            <span class="file-msg" id="file-name">Clique ou arraste o PDF aqui</span>
            <input class="file-input" type="file" id="curriculo" accept=".pdf">
        </div>
    </div>

    <button class="btn" id="btn-confirmar">Enviar Candidatura</button>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/cleave.js/1.6.0/cleave.min.js"></script>
"""

JS = """
export default function(component) {
    const { setTriggerValue, parentElement } = component;

    new Cleave(parentElement.querySelector('#cpf'), {delimiters: ['.', '.', '-'], blocks: [3, 3, 3, 2], numericOnly: true});
    new Cleave(parentElement.querySelector('#tel'), {delimiters: ['(', ') ', '-'], blocks: [0, 2, 5, 4], numericOnly: true});

    const fileInput = parentElement.querySelector('#curriculo');
    const fileMsg = parentElement.querySelector('#file-name');

    // Atualiza o nome do arquivo na UI quando selecionado
    fileInput.onchange = () => {
        if (fileInput.files.length > 0) {
            fileMsg.innerText = "📄 " + fileInput.files[0].name;
        }
    };

    parentElement.querySelector('#btn-confirmar').onclick = () => {
        const nome = parentElement.querySelector('#nome').value;
        const cpf = parentElement.querySelector('#cpf').value;
        const tel = parentElement.querySelector('#tel').value;
        const email = parentElement.querySelector('#email').value;
        const file = fileInput.files[0];

        if (!nome || !cpf || !file) {
            alert("Nome, CPF e Currículo são obrigatórios!");
            return;
        }

        // Converter arquivo para Base64 para enviar ao Python
        const reader = new FileReader();
        reader.onload = (e) => {
            setTriggerValue('submitted', {
                nome, cpf, tel, email,
                file_name: file.name,
                file_data: e.target.result.split(',')[1] // Pega apenas o conteúdo base64
            });
        };
        reader.readAsDataURL(file);
    };
}
"""

form_component = st.components.v2.component(
    "form_completo",
    html=HTML,
    js=JS,
)

# --- APP ---
st.title("💼 Portal de Recrutamento")

result = form_component(on_submitted_change=lambda: None, key="form_full_custom")

if result.submitted:
    dados = result.submitted
    
    # Decodificar o arquivo PDF enviado pelo JS
    pdf_bytes = base64.b64decode(dados['file_data'])
    
    st.success(f"✅ Candidatura recebida: **{dados['nome']}**")
    
    with st.container(border=True):
        st.markdown(f"**CPF:** {dados['cpf']} | **WhatsApp:** {dados['tel']}")
        st.markdown(f"**Arquivo:** `{dados['file_name']}`")
        
        if st.button("Salvar no Banco de Dados", type="primary", use_container_width=True):
            # Exemplo de salvamento (Aqui você usaria seu código de banco)
            path = f"uploads/{limpar(dados['cpf'])}.pdf"
            with open(path, "wb") as f:
                f.write(pdf_bytes)
            
            st.balloons()
            st.success(f"Currículo salvo em: {path}")
else:
    st.info("Preencha todos os campos e anexe seu currículo acima.")