"""PDF export utilities using reportlab + THSarabunNew font."""
import os
import sys
import unicodedata
from screens.base import count_fc
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# path เมื่อรันจาก source
_FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts", "THSarabunNew.ttf")
_FONT_REGISTERED = False

_FALLBACK_FONTS = [
    os.path.expanduser("~/Library/Fonts/THSarabunNew.ttf"),  # installed by main.py
    "/System/Library/Fonts/Supplemental/Ayuthaya.ttf",        # macOS system
    "/System/Library/Fonts/Ayuthaya.ttf",                     # macOS older
    "C:/Windows/Fonts/leelawad.ttf",                          # Windows
]


def _best_font_path() -> str:
    # 1. PyInstaller bundle: ดึงจาก sys._MEIPASS (Contents/Frameworks/)
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        for base in [meipass, os.path.join(meipass, "..", "Resources")]:
            p = os.path.join(base, "assets", "fonts", "THSarabunNew.ttf")
            p = os.path.normpath(p)
            if os.path.exists(p):
                return p
    # 2. Source path (dev mode)
    if os.path.exists(_FONT_PATH):
        return _FONT_PATH
    # 3. Fallbacks: installed / system fonts
    for p in _FALLBACK_FONTS:
        if os.path.exists(p):
            return p
    return _FONT_PATH


def _register():
    global _FONT_REGISTERED
    if not _FONT_REGISTERED:
        path = _best_font_path()
        pdfmetrics.registerFont(TTFont("Thai",   path))
        pdfmetrics.registerFont(TTFont("ThaiBd", path))
        _FONT_REGISTERED = True


def _p(text, size=12, bold=False, fg=colors.black, align="LEFT"):
    """Create a Paragraph with Thai font."""
    _register()
    style = ParagraphStyle(
        "t",
        fontName="ThaiBd" if bold else "Thai",
        fontSize=size,
        textColor=fg,
        alignment={"LEFT": 0, "CENTER": 1, "RIGHT": 2}.get(align, 0),
        leading=size * 1.5,
        wordWrap="CJK",
    )
    safe = unicodedata.normalize("NFC", text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(safe, style)


_BASE_STYLE = [
    ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#aaaaaa")),
    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING",    (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#d0d0d0")),
]


# ── History Result ─────────────────────────────────────────────────────────────

def export_history_result(ev: dict, groups: list, filepath: str, copies: int = 1, rank: int = 0) -> None:
    _register()

    type_map   = {"diagnostic": "Diagnostic", "modality": "Modality", "clinic": "Clinical Review", "ehr": "Electronic Health Record display"}
    period_map = {"monthly": "รายเดือน", "quarterly": "ราย 3 เดือน", "annual": "ประจำปี"}
    stype  = type_map.get(ev.get("screen_type", ""), "")
    period = period_map.get(ev.get("period", ""), "")

    eval_dt_str = ev.get('eval_datetime', '')
    import datetime
    try:
        dt_obj = datetime.datetime.strptime(eval_dt_str, "%Y-%m-%d %H:%M:%S")
        display_date = f"{dt_obj.day:02d}/{dt_obj.month:02d}/{dt_obj.year + 543} {dt_obj.strftime('%H:%M:%S')}"
    except Exception:
        display_date = eval_dt_str

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=20*mm,
    )

    rank_txt  = f"ครั้งที่ {rank}  " if rank else ""
    model_txt = f"หมายเลขครุภัณฑ์ {ev.get('screen_model','')}  " if ev.get("screen_model") else ""

    story = [
        _p("รายงานผลการประเมินคุณภาพหน้าจอแสดงผลทางการแพทย์", size=20, bold=True, align="CENTER"),
        Spacer(1, 4*mm),
        _p(f"โรงพยาบาล: {ev.get('hospital_name','')}", size=13),
        _p(f"จอภาพ: {stype} | รอบ: {period} | {rank_txt} | {model_txt} | ผู้ประเมิน {ev.get('evaluator_name','')} |  {display_date}", size=13),
        Spacer(1, 4*mm),
    ]

    # usable width ≈ A4(595) – 30mm = 510pt
    col_w = [105*mm, 32*mm, 40*mm]

    answers = ev.get("answers", {})
    data = [[
        _p("หัวข้อการประเมิน", 13, bold=True),
        _p("ผลการประเมิน",    13, bold=True, align="CENTER"),
        _p("หมายเหตุ",        13, bold=True),
    ]]
    style_extra = []

    CLR_PASS = colors.HexColor("#007700")
    CLR_FAIL = colors.HexColor("#cc0000")
    CLR_NONE = colors.HexColor("#888888")

    for group in groups:
        ri = len(data)
        data.append([_p(group["group_title"], 13, bold=True), _p(""), _p("")])
        style_extra += [
            ("BACKGROUND", (0, ri), (-1, ri), colors.HexColor("#c8c8c8")),
            ("SPAN",       (0, ri), (-1, ri)),
        ]

        for item in group["items"]:
            ans = answers.get(item["item_id"])
            if ans:
                res   = "ผ่าน " if ans["passed"] else "ไม่ผ่าน"
                rfg   = CLR_PASS if ans["passed"] else CLR_FAIL
                user_note = ans.get("notes", "")
                notes = ""
                if ans.get("failed_channels"):
                    fc_list = ans["failed_channels"]
                    ch_str = ", ".join(str(c) for c in fc_list)
                    if item.get("question_type") == "yes_no_channels_text":
                        notes = (f"จำนวนภาพที่ Pixel ไม่สม่ำเสมอ: {count_fc(fc_list)} ภาพ  "
                                 f"ภาพที่ไม่เห็น: {ch_str}")
                    else:
                        ch_lbl = item.get("channel_label", "ช่อง")
                        note_prefix = item.get("channel_note", f"{ch_lbl}ที่ไม่เห็น")
                        count_lbl = item.get("count_label")
                        if count_lbl:
                            notes = (f"{count_lbl}: {count_fc(fc_list)}  "
                                     f"{note_prefix}: {ch_str}")
                        else:
                            notes = f"{note_prefix}: {ch_str}"
                if user_note:
                    notes = (notes + "  " if notes else "") + f"*{user_note}"
            else:
                res, rfg, notes = "ไม่ได้ตอบ", CLR_NONE, ""

            ri = len(data)
            data.append([
                _p(f"  {item['title']}", 12),
                _p(res, 12, fg=rfg, align="CENTER"),
                _p(notes, 12),
            ])

    tbl = Table(data, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle(_BASE_STYLE + style_extra))
    story.append(tbl)

    # ── signature block (bottom right) ──────────────────────────────────
    story.append(Spacer(1, 10*mm))
    sig_data = [[
        _p(""),
        Table(
            [
                [_p(f"ลงชื่อ ....................................................", 12, align="CENTER")],
                [_p(f"( {ev.get('evaluator_name', '')} )", 12, align="CENTER")],
                [_p("ผู้ประเมิน", 12, align="CENTER")],
                
            ],
            colWidths=[70*mm],
            style=TableStyle([
                ("ALIGN",    (0, 0), (-1, -1), "CENTER"),
                ("VALIGN",   (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",    (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]),
        ),
    ]]
    sig_tbl = Table(sig_data, colWidths=[107*mm, 70*mm])
    sig_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
    ]))
    story.append(sig_tbl)

    if copies > 1:
        full = []
        for i in range(copies):
            full.extend(story)
            if i < copies - 1:
                full.append(PageBreak())
        doc.build(full)
    else:
        doc.build(story)


# ── Comparison ─────────────────────────────────────────────────────────────────

def export_comparison(current: dict, baseline: dict, row_data: list, filepath: str, copies: int = 1) -> None:
    """
    row_data: list of dicts with keys:
        is_group, title, b_text, c_text, result_text, description, tag
    """
    _register()

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )

    _type_map   = {"diagnostic": "Diagnostic", "modality": "Modality", "clinic": "Clinical Review", "ehr": "Electronic Health Record display"}
    _period_map = {"monthly": "รายเดือน", "quarterly": "ราย 3 เดือน", "annual": "ประจำปี"}
    cmp_stype  = _type_map.get(current.get("screen_type", ""), current.get("screen_type", ""))
    cmp_period = _period_map.get(current.get("period", ""), current.get("period", ""))

    import datetime
    
    curr_dt_str = current.get('eval_datetime','')
    try:
        dt_obj = datetime.datetime.strptime(curr_dt_str, "%Y-%m-%d %H:%M:%S")
        curr_disp_dt = f"{dt_obj.day:02d}/{dt_obj.month:02d}/{dt_obj.year + 543} {dt_obj.strftime('%H:%M:%S')}"
    except Exception:
        curr_disp_dt = curr_dt_str
        
    base_dt_str = baseline.get('eval_datetime','')
    try:
        dt_obj = datetime.datetime.strptime(base_dt_str, "%Y-%m-%d %H:%M:%S")
        base_disp_dt = f"{dt_obj.day:02d}/{dt_obj.month:02d}/{dt_obj.year + 543} {dt_obj.strftime('%H:%M:%S')}"
    except Exception:
        base_disp_dt = base_dt_str

    now_txt  = f"ครั้งที่: {current.get('rank','')} |  {current.get('evaluator_name','')} | {curr_disp_dt}"
    base_txt = f"ครั้งที่ (Baseline): {baseline.get('rank','')} |  {baseline.get('evaluator_name','')} | {base_disp_dt}"

    story = [
        _p("รายงานการเปรียบเทียบกับผล", size=20, bold=True, align="CENTER"),
        Spacer(1, 3*mm),
        _p(f"โรงพยาบาล: {current.get('hospital_name', '')} | จอภาพ: {cmp_stype} | รอบ: {cmp_period}", size=13),
        _p(f"{now_txt}", size=12),
        _p(f"{base_txt}", size=12),
        Spacer(1, 4*mm),
    ]

    # portrait A4 usable ≈ 595 – 30mm = 510pt ≈ 180mm
    col_w = [46*mm, 20*mm, 20*mm, 40*mm, 54*mm]

    TAG_FG = {
        "degraded": colors.HexColor("#cc0000"),
        "drift":    colors.HexColor("#b36b00"),
        "no_ans":   colors.HexColor("#888888"),
        "same":     colors.HexColor("#333333"),
    }

    data = [[
        _p("หัวข้อประเมิน",                      12, bold=True),
        _p("Baseline",                            12, bold=True, align="CENTER"),
        _p("ครั้งที่",                                 12, bold=True, align="CENTER"),
        _p("ผลการเปรียบเทียบ",                   12, bold=True),
        _p("คำอธิบายเพิ่มเติมจากการเปรียบเทียบ", 12, bold=True),
    ]]
    style_extra = []

    for row in row_data:
        ri = len(data)
        if row["is_group"]:
            data.append([_p(row["title"], 12, bold=True),
                         _p(""), _p(""), _p(""), _p("")])
            style_extra += [
                ("BACKGROUND", (0, ri), (-1, ri), colors.HexColor("#c8c8c8")),
                ("SPAN",       (0, ri), (-1, ri)),
            ]
        else:
            fg = TAG_FG.get(row["tag"], colors.black)
            data.append([
                _p(row["title"],       11, fg=fg),
                _p(row["b_text"],      11, fg=fg, align="CENTER"),
                _p(row["c_text"],      11, fg=fg, align="CENTER"),
                _p(row["result_text"], 11, fg=fg),
                _p(row["description"], 11, fg=fg),
            ])

    tbl = Table(data, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle(_BASE_STYLE + style_extra))
    story.append(tbl)

    # ── signature block (bottom right) ──────────────────────────────────
    story.append(Spacer(1, 10*mm))
    sig_data = [[
        _p(""),
        Table(
            [
                [_p("ลงชื่อ ....................................................", 12, align="CENTER")],
                [_p("(.................................................)", 12, align="CENTER")],
                [_p("ผู้ประเมิน", 12, align="CENTER")],
            ],
            colWidths=[70*mm],
            style=TableStyle([
                ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",    (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]),
        ),
    ]]
    sig_tbl = Table(sig_data, colWidths=[107*mm, 70*mm])
    sig_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
    ]))
    story.append(sig_tbl)

    if copies > 1:
        full = []
        for i in range(copies):
            full.extend(story)
            if i < copies - 1:
                full.append(PageBreak())
        doc.build(full)
    else:
        doc.build(story)
