import html, logging, smtplib
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path
from app.config.settings import settings

log=logging.getLogger(__name__)
LOGO=Path(__file__).resolve().parent.parent/'static'/'img'/'peacock-logo-mark.png'
@dataclass(frozen=True)
class BookingEmail:
    recipient:str; guest_name:str; booking_no:str; room_type:str; check_in_at:datetime; check_out_at:datetime
    number_of_rooms:int; number_of_days:int; subtotal_amount:object; gst_amount:object; total_amount:object; paid_amount:object
    payment_mode:str; payment_id:str|None=None; balance_amount:object=0

def money(v): return f'₹{float(v):,.2f}'
def dt(v): return v.strftime('%d %b %Y, %I:%M %p')
def send_booking_confirmation(d:BookingEmail)->bool:
    if not d.recipient or not settings.SMTP_PASSWORD:
        log.warning('Email skipped for %s: recipient or SMTP password missing',d.booking_no); return False
    e=html.escape
    rows=[('Room',f'{e(d.room_type)} × {d.number_of_rooms}'),('Check-in',dt(d.check_in_at)),('Check-out',dt(d.check_out_at)),('Stay',f'{d.number_of_days} day(s)'),('Subtotal',money(d.subtotal_amount)),('GST',money(d.gst_amount)),('Total',money(d.total_amount)),(f'Paid via {e(d.payment_mode)}',money(d.paid_amount)),('Balance',money(d.balance_amount)),('Payment reference',e(d.payment_id or 'Recorded by the property'))]
    table=''.join(f'<tr><td style="padding:8px"><b>{a}</b></td><td align="right" style="padding:8px">{b}</td></tr>' for a,b in rows)
    body=f'''<html><body style="margin:0;background:#f2f8f6;font-family:Arial;color:#143d3d"><div style="max-width:620px;margin:auto;background:white"><div style="padding:28px;text-align:center;background:#07545a;color:white"><img src="cid:ars-logo" width="90"><h1>Akshat Royal Stay</h1><p style="color:#e6c56e">Booking confirmed</p></div><div style="padding:28px"><p>Dear {e(d.guest_name)},</p><p>Your booking and payment details are confirmed.</p><h2>{e(d.booking_no)}</h2><table width="100%">{table}</table><h3>Terms & refund policy</h3><ul style="line-height:1.6"><li>Valid government photo ID is required. Occupancy must match the booking; extra guests incur applicable charges.</li><li>Date changes depend on availability and rate difference.</li><li>48+ hours before check-in: full room-charge refund; gateway charges, if any, are non-refundable.</li><li>24–48 hours: 50% refund. Within 24 hours, no-show or early departure: no refund.</li><li>Approved refunds return to the original method in 7–10 business days. Property cancellation: full refund.</li></ul><p>Help: +91 90929 77055 · ars.familystay@gmail.com</p></div></div></body></html>'''
    msg=EmailMessage(); msg['Subject']=f'Booking confirmed — {d.booking_no} | Akshat Royal Stay'; msg['From']=formataddr((settings.SMTP_FROM_NAME,settings.SMTP_FROM_EMAIL)); msg['To']=d.recipient; msg['Reply-To']=settings.SMTP_REPLY_TO; msg.set_content(f'Booking {d.booking_no} confirmed. Total {money(d.total_amount)}; paid {money(d.paid_amount)}. https://online.akshatroyalstay.in/refund-policy'); msg.add_alternative(body,subtype='html')
    if LOGO.exists(): msg.get_payload()[-1].add_related(LOGO.read_bytes(),maintype='image',subtype='png',cid='<ars-logo>')
    try:
        client=smtplib.SMTP_SSL(settings.SMTP_HOST,settings.SMTP_PORT,timeout=settings.SMTP_TIMEOUT_SECONDS) if settings.SMTP_USE_SSL else smtplib.SMTP(settings.SMTP_HOST,settings.SMTP_PORT,timeout=settings.SMTP_TIMEOUT_SECONDS)
        with client:
            if settings.SMTP_USE_STARTTLS: client.starttls()
            client.login(settings.SMTP_USERNAME,settings.SMTP_PASSWORD); client.send_message(msg)
        return True
    except Exception: log.exception('Email failed for %s',d.booking_no); return False
