import io, json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

ARS_NAME="Akshat Royal Stay"
ARS_GSTIN="GSTAKSHATJM81"
ARS_ADDRESS="No. 85, Kamaraj Bazaar Road, Bodinayakanur, Theni District, Tamil Nadu, India - 625513"
ARS_WEBSITE="akshatroyalstay.in"
LOGO=Path(__file__).resolve().parent.parent/"static"/"img"/"peacock-logo-mark.png"

def items(invoice):
    try: return json.loads(invoice.additional_items_json or "[]")
    except (ValueError, TypeError): return []

def build_invoice_pdf(invoice):
    out=io.BytesIO(); doc=SimpleDocTemplate(out,pagesize=A4,rightMargin=16*mm,leftMargin=16*mm,topMargin=13*mm,bottomMargin=14*mm,title=invoice.invoice_no)
    styles=getSampleStyleSheet(); styles.add(ParagraphStyle(name="CenterSmall",parent=styles["BodyText"],alignment=TA_CENTER,fontSize=8,leading=11,textColor=colors.HexColor("#416466"))); styles.add(ParagraphStyle(name="Right",parent=styles["BodyText"],alignment=TA_RIGHT,fontSize=9)); styles.add(ParagraphStyle(name="Tiny",parent=styles["BodyText"],fontSize=7.5,leading=10,textColor=colors.HexColor("#536b6c")))
    story=[]
    if LOGO.exists(): story.append(Image(str(LOGO),width=24*mm,height=24*mm))
    story += [Paragraph(ARS_NAME,ParagraphStyle(name="Brand",parent=styles["Title"],alignment=TA_CENTER,textColor=colors.HexColor("#07545a"),fontSize=21,leading=24)),Paragraph("TAX INVOICE",ParagraphStyle(name="Tax",parent=styles["Heading2"],alignment=TA_CENTER,textColor=colors.HexColor("#b58a24"),fontSize=12)),Paragraph(f"{ARS_ADDRESS}<br/>GSTIN: <b>{ARS_GSTIN}</b> | {ARS_WEBSITE}",styles["CenterSmall"]),Spacer(1,7*mm)]
    meta=[[Paragraph(f"<b>Invoice:</b> {invoice.invoice_no}<br/><b>Date:</b> {invoice.invoice_date:%d-%m-%Y}<br/><b>Booking:</b> {invoice.booking_no or '-'}",styles["BodyText"]),Paragraph(f"<b>Bill To</b><br/>{invoice.customer_name}<br/>{invoice.mobile or '-'} | {invoice.customer_email or '-'}<br/>{invoice.customer_address or '-'}<br/><b>GSTIN:</b> {invoice.customer_gstin or 'Unregistered customer'}",styles["Right"])] ]
    t=Table(meta,colWidths=[82*mm,82*mm]); t.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("BOX",(0,0),(-1,-1),0.6,colors.HexColor("#b9d1ce")),("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#f3f8f7")),("PADDING",(0,0),(-1,-1),8)])); story += [t,Spacer(1,5*mm)]
    stay=[["Check-in","Check-out","Rooms","Room type"],[invoice.checkin_date.strftime("%d-%m-%Y"),invoice.checkout_date.strftime("%d-%m-%Y"),str(invoice.number_of_rooms),invoice.room_type]]
    t=Table(stay,colWidths=[38*mm,38*mm,24*mm,64*mm]); t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#07545a")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#c8d9d6")),("ALIGN",(0,0),(-1,-1),"CENTER"),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("PADDING",(0,0),(-1,-1),7)])); story += [t,Spacer(1,5*mm)]
    rows=[["Description","Amount (INR)"],["Room accommodation",f"{invoice.room_charge:,.2f}"]]
    rows += [[x.get("description","Additional charge"),f"{float(x.get('amount',0)):,.2f}"] for x in items(invoice)]
    if invoice.discount_amount: rows.append(["Discount",f"-{invoice.discount_amount:,.2f}"])
    taxable=invoice.room_charge+invoice.extra_charge-invoice.discount_amount
    rows += [["Taxable value",f"{taxable:,.2f}"],[f"CGST ({invoice.gst_percent/2:g}%)",f"{invoice.gst_amount/2:,.2f}"],[f"SGST ({invoice.gst_percent/2:g}%)",f"{invoice.gst_amount/2:,.2f}"],["GRAND TOTAL",f"{invoice.total_amount:,.2f}"],["Amount paid",f"{invoice.amount_paid:,.2f}"],["Balance due",f"{invoice.balance_amount:,.2f}"]]
    t=Table(rows,colWidths=[120*mm,44*mm]); t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#07545a")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#c8d9d6")),("ALIGN",(1,1),(1,-1),"RIGHT"),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTNAME",(0,-3),(-1,-1),"Helvetica-Bold"),("BACKGROUND",(0,-3),(-1,-3),colors.HexColor("#edf7f4")),("PADDING",(0,0),(-1,-1),6)])); story += [t,Spacer(1,4*mm),Paragraph(f"<b>Payment:</b> {invoice.payment_mode or '-'} | <b>Reference:</b> {invoice.payment_reference or '-'}",styles["BodyText"]),Spacer(1,3*mm),Paragraph(f"<b>Notes:</b> {invoice.notes or '-'}",styles["Tiny"]),Spacer(1,6*mm),Paragraph("Terms: Subject to Akshat Royal Stay booking, cancellation and refund policy. This is a computer-generated invoice.",styles["Tiny"]),Spacer(1,8*mm),Table([["Guest acknowledgement","For Akshat Royal Stay"],["________________________","________________________"]],colWidths=[82*mm,82*mm],style=TableStyle([("ALIGN",(1,0),(1,-1),"RIGHT"),("TOPPADDING",(0,1),(-1,1),18)])),Spacer(1,5*mm),Paragraph("Thank you for staying with us.",styles["CenterSmall"])]
    doc.build(story); out.seek(0); return out.getvalue()
