import logging, smtplib
from email.message import EmailMessage
from email.utils import formataddr
from app.config.settings import settings
from app.custom_gst.pdf_service import build_invoice_pdf
log=logging.getLogger(__name__)

def send_invoice_email(invoice)->bool:
    if not invoice.customer_email or not settings.SMTP_PASSWORD: return False
    msg=EmailMessage(); msg["Subject"]=f"Tax invoice {invoice.invoice_no} | Akshat Royal Stay"; msg["From"]=formataddr((settings.SMTP_FROM_NAME,settings.SMTP_FROM_EMAIL)); msg["To"]=invoice.customer_email; msg["Reply-To"]=settings.SMTP_REPLY_TO
    msg.set_content(f"Dear {invoice.customer_name},\n\nPlease find attached tax invoice {invoice.invoice_no} for your stay at Akshat Royal Stay. Total: INR {invoice.total_amount:,.2f}; Paid: INR {invoice.amount_paid:,.2f}; Balance: INR {invoice.balance_amount:,.2f}.\n\nThank you.")
    msg.add_attachment(build_invoice_pdf(invoice),maintype="application",subtype="pdf",filename=f"{invoice.invoice_no}.pdf")
    try:
        client=smtplib.SMTP_SSL(settings.SMTP_HOST,settings.SMTP_PORT,timeout=settings.SMTP_TIMEOUT_SECONDS) if settings.SMTP_USE_SSL else smtplib.SMTP(settings.SMTP_HOST,settings.SMTP_PORT,timeout=settings.SMTP_TIMEOUT_SECONDS)
        with client:
            if settings.SMTP_USE_STARTTLS: client.starttls()
            client.login(settings.SMTP_USERNAME,settings.SMTP_PASSWORD); client.send_message(msg)
        return True
    except Exception: log.exception("Invoice email failed: %s",invoice.invoice_no); return False
