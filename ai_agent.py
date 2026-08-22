"""
وحدة الذكاء الاصطناعي والوكيل الذكي — تستخدم Claude من Anthropic لتحليل بيانات
جودة الفروع، توليد ملخصات وتوصيات ذكية، والرد على استفسارات المستخدمين.
"""
import os
import streamlit as st

try:
    import anthropic
except ImportError:
    anthropic = None

MODEL_NAME = "claude-sonnet-4-5"


def _get_api_key() -> str:
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if key:
        return key
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    return ""


def is_ai_configured() -> bool:
    """يتحقق من توفر مفتاح API ومكتبة anthropic معًا."""
    return bool(_get_api_key()) and anthropic is not None


def ask_claude(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
    """يرسل طلبًا لنموذج Claude ويرجع الرد النصي. يرمي استثناء عند الفشل."""
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("لم يتم ضبط مفتاح ANTHROPIC_API_KEY بعد.")
    if anthropic is None:
        raise RuntimeError("مكتبة anthropic غير مثبتة. أضفها لملف requirements.txt.")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=MODEL_NAME,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(block.text for block in message.content if hasattr(block, "text"))


def summarize_audit(audit_info: dict, answers_rows: list) -> str:
    """يولّد ملخصًا ذكيًا وتوصيات عملية لتدقيق معيّن بناءً على إجاباته."""
    system_prompt = (
        "أنت مساعد ذكي متخصص في جودة الفروع وإدارة التدقيق الداخلي. "
        "تكتب دائمًا بالعربية الفصحى، بأسلوب مهني موجز ومباشر، وتركّز على "
        "استنتاجات عملية قابلة للتنفيذ."
    )
    lines = []
    for r in answers_rows:
        line = f"- {r['question']}: {r['answer']} (الوزن: {r['weight']})"
        if r.get("note"):
            line += f" — ملاحظة: {r['note']}"
        lines.append(line)

    user_prompt = f"""لدي تدقيق جودة بالمعلومات التالية:
المرجع: {audit_info.get('reference')}
الفرع: {audit_info.get('branch_name')}
النتيجة الإجمالية: {audit_info.get('score')}%

الإجابات التفصيلية:
{chr(10).join(lines)}

اكتب تحليلًا يشمل:
1) ملخص من 2-3 جمل عن حالة الفرع
2) أهم نقاط عدم التوافق وأسبابها المحتملة
3) 2-3 توصيات عملية ومحددة لتحسين النتيجة القادمة
"""
    return ask_claude(system_prompt, user_prompt, max_tokens=700)


def chat_with_assistant(user_message: str, context_summary: str, history: list) -> str:
    """محادثة عامة مع المساعد الذكي حول بيانات النظام الحالية."""
    system_prompt = (
        "أنت المساعد الذكي (الوكيل الذكي) لنظام NXN لإدارة جودة الفروع. "
        "تساعد المستخدمين على فهم بيانات التدقيق والفروع والإجراءات التصحيحية، "
        "وتقدّم نصائح عملية لتحسين الجودة. أجب دائمًا بالعربية بأسلوب واضح ومباشر. "
        "إذا سُئلت عن معلومة محددة غير متوفرة في السياق المعطى، وضّح ذلك صراحة "
        "بدلًا من التخمين أو اختلاق أرقام."
    )
    convo = "\n".join(
        f"{'المستخدم' if m['role'] == 'user' else 'المساعد'}: {m['content']}"
        for m in history[-6:]
    )
    user_prompt = f"""معلومات سياقية عن حالة النظام حاليًا:
{context_summary}

سجل المحادثة السابق:
{convo}

سؤال المستخدم الجديد: {user_message}
"""
    return ask_claude(system_prompt, user_prompt, max_tokens=800)
