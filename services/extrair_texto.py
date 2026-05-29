import fitz
import logging

logger = logging.getLogger(__name__)

def limpar_texto(texto):
    if not texto:
        return ""
    return texto.replace("\u0000", "").strip()

def extrair_texto_pdf(caminho_pdf):
    texto = ""
    doc = None
    try:
        doc = fitz.open(caminho_pdf)
        for pagina in doc:
            texto += pagina.get_text()
    except Exception as e:
        logger.error(f"Erro ao abrir ou extrair texto do PDF em {caminho_pdf}: {e}", exc_info=True)
    finally:
        if doc:
            try:
                doc.close()
            except Exception:
                pass
    return limpar_texto(texto)