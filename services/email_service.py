import smtplib
import threading
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

logger = logging.getLogger(__name__)


def _enviar_email_sync(destinatario, assunto, corpo_html):
    try:
        app = current_app._get_current_object()
        if not app:
            return

        with app.app_context():
            mail_server = app.config.get("MAIL_SERVER")
            mail_port = app.config.get("MAIL_PORT")
            mail_use_tls = app.config.get("MAIL_USE_TLS", True)
            mail_user = app.config.get("MAIL_USERNAME", "")
            mail_pass = app.config.get("MAIL_PASSWORD", "")
            mail_sender = app.config.get("MAIL_DEFAULT_SENDER", "noreply@boracontratar.com.br")

            if not mail_user or not mail_pass:
                logger.warning("Email não configurado: MAIL_USERNAME/MAIL_PASSWORD vazios")
                return

            msg = MIMEMultipart("alternative")
            msg["From"] = mail_sender
            msg["To"] = destinatario
            msg["Subject"] = assunto
            msg.attach(MIMEText(corpo_html, "html"))

            with smtplib.SMTP(mail_server, mail_port) as server:
                if mail_use_tls:
                    server.starttls()
                if mail_user and mail_pass:
                    server.login(mail_user, mail_pass)
                server.sendmail(mail_sender, [destinatario], msg.as_string())

            logger.info(f"Email enviado para {destinatario}: {assunto}")
    except Exception as e:
        logger.error(f"Falha ao enviar email para {destinatario}: {e}")


def enviar_email(destinatario, assunto, corpo_html):
    thread = threading.Thread(
        target=_enviar_email_sync,
        args=(destinatario, assunto, corpo_html),
        daemon=True
    )
    thread.start()


def montar_corpo_email(titulo, mensagem, vaga_titulo, link):
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
<a href="{link}" style="display:inline-block;background:#7c3aed;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;margin-top:12px">Ver solicitação</a>
</div>
<div style="background:#f4f4f4;padding:12px;text-align:center;font-size:11px;color:#999">Bora Contratar</div>
</div></body></html>"""
