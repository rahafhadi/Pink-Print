import json
from contextlib import closing

from flask import current_app

from .database import get_db_connection


def parse_json(value, default=None):
    """Safely parse JSON stored in the database."""
    if default is None:
        default = {}

    if not value:
        return default

    try:
        result = json.loads(value)
        return result if isinstance(result, type(default)) else default
    except (TypeError, json.JSONDecodeError):
        return default


def get_latest_gail(conn, user_id):
    """Read the latest saved Gail assessment without recalculating it."""

    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(risk_assessments)"
        ).fetchall()
    }

    if "gail_result" not in columns:
        return None

    row = conn.execute("""
        SELECT created_at, gail_result
        FROM risk_assessments
        WHERE user_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
    """, (user_id,)).fetchone()

    if not row:
        return None

    result = parse_json(row["gail_result"])

    if not result:
        return None

    return {
        "date": row["created_at"],
        "absolute_risk_percent": result.get("absolute_risk_percent"),
        "projection_years": result.get("projection_years"),
        "relative_risk_under_50": result.get("relative_risk_under_50"),
        "relative_risk_50_plus": result.get("relative_risk_50_plus"),
        "reference_population": result.get("reference_population"),
    }


def get_recent_exams(conn, user_id, limit=5):
    """Read the latest self-examination records."""

    rows = conn.execute("""
        SELECT id, exam_date, observations, notes, status
        FROM self_exams
        WHERE user_id = ?
        ORDER BY exam_date DESC, id DESC
        LIMIT ?
    """, (user_id, limit)).fetchall()

    exams = []

    for row in rows:
        exams.append({
            "exam_id": row["id"],
            "date": row["exam_date"],
            "observations": parse_json(row["observations"]),
            "general_notes": row["notes"] or "",
            "status": row["status"],
        })

    return exams


def get_patient_context(user_id, exam_limit=5):
    """
    Read patient-specific information locally.

    The user_id must come from the authenticated Flask session.
    This function does not send data to any external service.
    """

    if not user_id:
        raise ValueError("An authenticated user ID is required.")

    with closing(
        get_db_connection(current_app.config["DATABASE"])
    ) as conn:

        gail = get_latest_gail(conn, user_id)

        exams = get_recent_exams(
            conn,
            user_id,
            limit=exam_limit
        )

    return {
        "gail": gail,
        "recent_exams": exams,
    }


def format_patient_context(context):
    """Convert patient data into a readable Arabic text."""

    sections = []

    gail = context.get("gail")

    if gail:
        lines = [
            "آخر تقييم محفوظ باستخدام Gail Model:",
            f"تاريخ التقييم: {gail.get('date')}",
        ]

        if gail.get("absolute_risk_percent") is not None:
            lines.append(
                f"الخطر المطلق المحسوب: "
                f"{gail['absolute_risk_percent']}%"
            )

        if gail.get("projection_years") is not None:
            lines.append(
                f"مدة التوقع: {gail['projection_years']} سنة"
            )

        if gail.get("relative_risk_under_50") is not None:
            lines.append(
                f"الخطر النسبي لمن هن أقل من 50: "
                f"{gail['relative_risk_under_50']}"
            )

        if gail.get("relative_risk_50_plus") is not None:
            lines.append(
                f"الخطر النسبي لمن هن 50 فأكثر: "
                f"{gail['relative_risk_50_plus']}"
            )

        if gail.get("reference_population"):
            lines.append(
                f"المجموعة المرجعية: {gail['reference_population']}"
            )

        lines.append(
            "هذه نتيجة نموذج لتقدير الخطر وليست تشخيصًا."
        )

        sections.append("\n".join(lines))
    else:
        sections.append("لا توجد نتيجة Gail محفوظة.")

    exams = context.get("recent_exams", [])

    if exams:
        exam_sections = ["سجلات الفحص الذاتي الأخيرة:"]

        for exam in exams:
            exam_lines = [
                f"\nتاريخ الفحص: {exam.get('date')}",
            ]

            observations = exam.get("observations", {})

            for key, value in observations.items():
                if value == "yes":
                    answer = "لاحظت"
                elif value == "no":
                    answer = "لم تلاحظ أثناء الفحص المسجل"
                elif value == "unsure":
                    answer = "غير متأكدة"
                else:
                    answer = str(value)

                exam_lines.append(f"- {key}: {answer}")

            if exam.get("general_notes"):
                exam_lines.append(
                    f"ملاحظات عامة: {exam['general_notes']}"
                )

            exam_sections.append("\n".join(exam_lines))

        sections.append("\n".join(exam_sections))
    else:
        sections.append("لا توجد سجلات فحص ذاتي محفوظة.")

    return "\n\n".join(sections)
