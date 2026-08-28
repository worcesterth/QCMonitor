import tkinter as tk
from screens.base import BaseScreen, CARD_COLOR, TEXT_COLOR, thai_font
from config import TEST_CONFIG

INSTRUCTION_LINES = [
    "1. เปิดหน้าจอไว้ก่อน 30 นาที ก่อนเริ่มการทดสอบ เปิดหน้าต่างโปรแกรมให้เต็มจอก่อนเริ่มการทดสอบ เพื่อให้แสดงแบบประเมินได้ครบถ้วน",
    "2. ระยะห่างของการทดสอบตั้งแต่ระยะสายตาของผู้ทดสอบถึงหน้าจอ ควรมีระยะห่างประมาณ\nหนึ่งช่วงแขน (ประมาณ 65 เซนติเมตร) เพื่อให้การทดสอบมีความแม่นยำมากขึ้น",
    "3. ก่อนการทำการประเมินตรวจสอบดูว่ามีรอยนิ้วมือและฝุ่นหรือไม่ เช็ดทำความสะอาดด้วยผ้าไร้ฝุ่น (lint-free cloth)  หรือตามที่บริษัทแนะนำ",
    "4. เปิดไฟในห้องตามการใช้งานจริง",
    "5. เตรียมแว่นขยายไว้สำหรับการประเมิน spatial resolution",
]


class InstructionsScreen(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app)

        card = self.card(self)
        card.place(relx=0.5, rely=0.5, anchor="center", width=self.CARD_W, height=self.CARD_HL)

        self.card_header(card, "คำแนะนำในการทดสอบระบบ", size=self.fs(24))

        btn_frame = tk.Frame(card, bg=CARD_COLOR)
        btn_frame.pack(side="bottom", fill="x", padx=16, pady=12)

        body = tk.Frame(card, bg=CARD_COLOR)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        self.title_label(body, "คำแนะนำก่อนการประเมิน", size=self.fs(35)).pack(pady=(4, 12))

        for line in INSTRUCTION_LINES:
            tk.Label(body, text=line, font=thai_font(self.fs(28)), bg=CARD_COLOR,
                     fg=TEXT_COLOR, anchor="w", justify="left",
                     wraplength=int(760 * self._s)).pack(anchor="w", pady=5)
        self.primary_btn(btn_frame, "ถัดไป",    self._next,                  fontsize=self.fs(26), width=12).pack(side="right", padx=4)
        self.back_btn(btn_frame, "ย้อนกลับ", lambda: app.show("confirm"), fontsize=self.fs(26), width=12).pack(side="right", padx=4)

    def on_show(self, **_):
        session = self.app.session
        screen_type = session.get("screen_type", "diagnostic")
        period      = session.get("period", "monthly")

        groups = TEST_CONFIG.get(screen_type, {}).get(period, [])
        items = []
        for group in groups:
            for item in group["items"]:
                items.append({**item,
                               "group_id":    group["group_id"],
                               "group_title": group["group_title"],
                               "group_title_Q": group.get("group_title_Q", "")})

        session["test_items"]       = items
        session["current_item_idx"] = 0
        session["answers"]          = {}

    def _next(self):
        self.app.show("test_runner")
