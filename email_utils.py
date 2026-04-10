import smtplib
from email.message import EmailMessage
from typing import Iterable, Tuple


def send_bulk_email_smtp(
    *,
    smtp_host: str,
    smtp_port: int,
    smtp_username: str | None,
    smtp_password: str | None,
    smtp_use_tls: bool,
    mail_from: str,
    recipients: Iterable[str],
    subject: str,
    body: str,
) -> Tuple[int, int]:
    """
    Sends one email per recipient (simplest + best deliverability for small batches).
    Returns: (sent_count, failed_count).
    """

    recipient_list = [r.strip() for r in recipients if r and r.strip()]
    if not recipient_list:
        return (0, 0)

    if not smtp_host:
        raise ValueError("SMTP_HOST is not configured")
    if not mail_from:
        raise ValueError("MAIL_FROM is not configured")

    server = smtplib.SMTP(smtp_host, smtp_port, timeout=20)
    try:
        server.ehlo()
        if smtp_use_tls:
            server.starttls()
            server.ehlo()

        if smtp_username and smtp_password:
            server.login(smtp_username, smtp_password)

        sent = 0
        failed = 0
        for to_addr in recipient_list:
            msg = EmailMessage()
            msg["From"] = mail_from
            msg["To"] = to_addr
            msg["Subject"] = subject
            msg.set_content(body)

            try:
                server.send_message(msg)
                sent += 1
            except Exception:
                failed += 1

        return (sent, failed)
    finally:
        try:
            server.quit()
        except Exception:
            server.close()
