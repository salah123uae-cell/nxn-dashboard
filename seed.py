"""
شغّل هذا الملف مرة واحدة فقط بعد إعداد قاعدة البيانات:
    python seed.py
ينشئ الجداول + مستخدم "مالك" افتراضي + نسخة تشيك ليست تجريبية بأقسامها وأسئلتها.
"""
import os
from dotenv import load_dotenv

from database import init_db, get_session
from models import User, Credential, ChecklistVersion, AuditSection, AuditQuestion, Branch
from auth import hash_password

load_dotenv()

OWNER_EMAIL = os.getenv("OWNER_EMAIL", "owner@nxn.local").strip().lower()
OWNER_NAME = os.getenv("OWNER_NAME", "System Owner")
OWNER_PASSWORD = os.getenv("OWNER_PASSWORD", "ChangeMe123!")


def run():
    print("إنشاء الجداول...")
    init_db()

    with get_session() as s:
        existing = s.query(User).filter(User.email == OWNER_EMAIL).first()
        if existing:
            print(f"المستخدم المالك موجود مسبقًا: {OWNER_EMAIL}")
        else:
            owner = User(email=OWNER_EMAIL, name=OWNER_NAME, role="owner")
            s.add(owner)
            s.flush()  # للحصول على owner.id
            s.add(Credential(user_id=owner.id, password_hash=hash_password(OWNER_PASSWORD)))
            print(f"تم إنشاء المستخدم المالك: {OWNER_EMAIL} / {OWNER_PASSWORD}")

        if s.query(Branch).count() == 0:
            s.add_all([
                Branch(code="BR-001", name_ar="فرع الرياض الرئيسي", name_en="Riyadh Main Branch",
                       region="الرياض", city="الرياض", status="active"),
                Branch(code="BR-002", name_ar="فرع جدة", name_en="Jeddah Branch",
                       region="مكة المكرمة", city="جدة", status="active"),
            ])
            print("تم إنشاء فروع تجريبية")

        if s.query(ChecklistVersion).count() == 0:
            s.add(ChecklistVersion(code="QV1", name_ar="نسخة الفحص الأولى", name_en="Checklist v1",
                                    status="active", created_by=OWNER_EMAIL))
            print("تم إنشاء نسخة تشيك ليست QV1")

        if s.query(AuditSection).count() == 0:
            sec1 = AuditSection(code="SEC-SAFETY", name_ar="السلامة", name_en="Safety",
                                 weight=40, sort_order=1, active=True)
            sec2 = AuditSection(code="SEC-SERVICE", name_ar="جودة الخدمة", name_en="Service Quality",
                                 weight=60, sort_order=2, active=True)
            s.add_all([sec1, sec2])
            s.flush()

            s.add_all([
                AuditQuestion(section_id=sec1.id, code="Q-001",
                              question_ar="هل يوجد طفايات حريق سارية الصلاحية؟",
                              question_en="Are fire extinguishers valid?",
                              weight=10, checklist_version="QV1", sort_order=1),
                AuditQuestion(section_id=sec1.id, code="Q-002",
                              question_ar="هل مخارج الطوارئ غير مسدودة؟",
                              question_en="Are emergency exits unobstructed?",
                              weight=10, checklist_version="QV1", sort_order=2),
                AuditQuestion(section_id=sec2.id, code="Q-003",
                              question_ar="هل الموظفون يرتدون الزي الرسمي؟",
                              question_en="Are staff wearing uniforms?",
                              weight=15, checklist_version="QV1", sort_order=1),
                AuditQuestion(section_id=sec2.id, code="Q-004",
                              question_ar="هل تم الرد على العميل خلال دقيقتين؟",
                              question_en="Was the customer greeted within 2 minutes?",
                              weight=15, checklist_version="QV1", sort_order=2),
            ])
            print("تم إنشاء أقسام وأسئلة تجريبية")

    print("\nالتهيئة اكتملت بنجاح.")


if __name__ == "__main__":
    run()

