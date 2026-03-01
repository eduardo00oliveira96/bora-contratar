import fitz  # PyMuPDF

def extrair_texto_pdf(caminho_pdf):
    """
    Extrai o texto de um arquivo PDF.

    Parameters
    ----------
    caminho_pdf : str
        O caminho do arquivo PDF a ser lido.

    Returns
    -------
    str
        O texto extraido do arquivo PDF.
    """
    texto = ""
    doc = fitz.open(caminho_pdf)

    for pagina in doc:
        texto += pagina.get_text()

    doc.close()
    return texto