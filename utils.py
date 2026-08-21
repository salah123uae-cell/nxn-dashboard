"""
دوال مساعدة: حساب نتائج التدقيق، توليد رقم مرجعي، والتصدير إلى Excel/PDF.
"""
import io
import random
import string
from datetime import datetime

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def generate_reference() -> str:
    """يولّد رقمًا مرجعيًا فريدًا للتدقيق، مثل AUD-20260818-XJ29"""
    date_part = datetime.utcnow().strftime("%Y%m%d")
    rand_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"AUD-{date_part}-{rand_part}"


def calculate_audit_score(answers: list[dict], questions_by_id: dict) -> float:
    """
    يحسب نسبة الالتزام المئوية لتدقيق معين.
    القاعدة: نأخذ الأسئلة القابلة للتطبيق فقط (answer != not_applicable)
    ونحسب: مجموع (الوزن للأسئلة المتوافقة) / مجموع (وزن كل الأسئلة القابلة للتطبيق) * 100
    """
    applicable_weight = 0.0
    earned_weight = 0.0
    for ans in answers:
        q = questions_by_id.get(ans["question_id"])
        if not q:
            continue
        if ans.get("answer") == "not_applicable":
            continue
        applicable_weight += q.weight
        if ans.get("answer") == "compliant":
            earned_weight += q.weight

    if applicable_weight == 0:
        return 0.0
    return round((earned_weight / applicable_weight) * 100, 2)


def score_badge(score: float | None) -> str:
    if score is None:
        return "⚪ غير محسوبة"
    if score >= 90:
        return f"🟢 {score}%"
    if score >= 75:
        return f"🟡 {score}%"
    return f"🔴 {score}%"


def export_audits_to_excel(df: pd.DataFrame) -> bytes:
    """يصدر جدول تدقيقات إلى ملف Excel منسّق ويرجعه كـ bytes."""
    wb = Workbook()
    ws = wb.active
    ws.title = "التدقيقات"

    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)

    ws.append(list(df.columns))
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for _, row in df.iterrows():
        ws.append(list(row))

    for col in ws.columns:
        max_len = max(len(str(c.value)) if c.value else 0 for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def export_audit_report_pdf(audit_info: dict, answers_rows: list[dict]) -> bytes:
    """يصدر تقرير PDF لتدقيق واحد."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"تقرير تدقيق: {audit_info.get('reference','')}", styles["Title"]))
    elements.append(Spacer(1, 12))

    meta = (
        f"الفرع: {audit_info.get('branch_name','')}<br/>"
        f"المدقق: {audit_info.get('auditor_email','')}<br/>"
        f"الحالة: {audit_info.get('status','')}<br/>"
        f"النتيجة: {audit_info.get('score','—')}%<br/>"
    )
    elements.append(Paragraph(meta, styles["Normal"]))
    elements.append(Spacer(1, 16))

    table_data = [["السؤال", "الإجابة", "الوزن", "ملاحظة"]]
    for r in answers_rows:
        table_data.append([r["question"], r["answer"], str(r["weight"]), r.get("note", "")])

    table = Table(table_data, colWidths=[220, 80, 50, 150])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table)

    doc.build(elements)
    return buf.getvalue()
