import os
import smtplib
import html as html_mod
import queue
import threading
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

logger = logging.getLogger(__name__)

_fila_email = queue.Queue()
_worker_iniciado = False
_lock_worker = threading.Lock()


def _processar_fila():
    """Worker que consome a fila de emails em background."""
    while True:
        destinatario, assunto, corpo_html = _fila_email.get()
        try:
            app = current_app._get_current_object()
            if not app:
                continue

            with app.app_context():
                _enviar_email_sync(app, destinatario, assunto, corpo_html)
        except Exception as e:
            logger.error(f"Falha ao processar email da fila para {destinatario}: {e}")
        finally:
            _fila_email.task_done()


def _garantir_worker():
    """Garante que o worker da fila está rodando (singleton)."""
    global _worker_iniciado
    if _worker_iniciado:
        return
    with _lock_worker:
        if _worker_iniciado:
            return
        t = threading.Thread(target=_processar_fila, daemon=True)
        t.start()
        _worker_iniciado = True


def _enviar_email_sync(app, destinatario, assunto, corpo_html):
    
    with app.app_context():
        mail_server = app.config.get("MAIL_SERVER")
        mail_port = app.config.get("MAIL_PORT", 587)
        mail_use_tls = app.config.get("MAIL_USE_TLS", True)
        mail_user = app.config.get("MAIL_USERNAME", "")
        mail_pass = app.config.get("MAIL_PASSWORD", "")
        mail_sender = app.config.get(
            "MAIL_DEFAULT_SENDER",
            os.environ.get("MAIL_DEFAULT_SENDER", "noreply@boracontratar.com.br"),
        )

        if not mail_user or not mail_pass:
            logger.warning("Email não configurado: MAIL_USERNAME/MAIL_PASSWORD vazios")
            return

        msg = MIMEMultipart("alternative")
        msg["From"] = mail_sender
        msg["To"] = destinatario
        msg["Subject"] = assunto

        corpo_texto = _html_para_texto(corpo_html)
        msg.attach(MIMEText(corpo_texto, "plain", "utf-8"))
        msg.attach(MIMEText(corpo_html, "html", "utf-8"))

        with smtplib.SMTP(mail_server, mail_port, timeout=30) as server:
            if mail_use_tls:
                server.starttls()
            if mail_user and mail_pass:
                server.login(mail_user, mail_pass)
            server.sendmail(mail_sender, [destinatario], msg.as_string())

        logger.info(f"Email enviado para {destinatario}: {assunto}")


def _html_para_texto(html_str):
    """Extrai texto simples do HTML para versão plain-text do email."""
    import re

    texto = re.sub(r"<style[^>]*>.*?</style>", "", html_str, flags=re.DOTALL | re.IGNORECASE)
    texto = re.sub(r"<script[^>]*>.*?</script>", "", texto, flags=re.DOTALL | re.IGNORECASE)
    texto = re.sub(r"<br\s*/?>", "\n", texto, flags=re.IGNORECASE)
    texto = re.sub(r"</(p|div|h[1-6]|li)>", "\n", texto, flags=re.IGNORECASE)
    texto = re.sub(r"<[^>]+>", "", texto)
    texto = html_mod.unescape(texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def enviar_email(destinatario, assunto, corpo_html):
    """Enfileira envio de email (não bloqueia o chamador)."""
    _garantir_worker()
    _fila_email.put((destinatario, assunto, corpo_html))


def montar_corpo_email(titulo, mensagem, vaga_titulo, link):
    """Monta template HTML do email com escape de XSS."""
    titulo = html_mod.escape(str(titulo))
    mensagem = html_mod.escape(str(mensagem))
    vaga_titulo = html_mod.escape(str(vaga_titulo))
    link_escaped = html_mod.escape(str(link), quote=True)

    return f"""<!DOCTYPE html>
<html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px">
<div style="max-width:600px;margin:auto;background:#fff;border-radius:8px;overflow:hidden">
<div style="background:#7c3aed;padding:20px;text-align:center">
<h1 style="color:#fff;margin:0;font-size:20px">Bora Contratar</h1>
</div>
<div style="padding:24px">
<h2 style="color:#333;font-size:18px;margin:0 0 8px">{titulo}</h2>
<p style="color:#555;line-height:1.5">{mensagem}</p>
<p style="color:#888;font-size:13px">Vaga: {vaga_titulo}</p>
<a href="{link_escaped}" style="display:inline-block;background:#7c3aed;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;margin-top:12px">Ver solicitação</a>
</div>
<div style="background:#f4f4f4;padding:12px;text-align:center;font-size:11px;color:#999">Bora Contratar</div>
</div></body></html>"""
