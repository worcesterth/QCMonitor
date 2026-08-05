import tkinter as tk
from screens.base import BaseScreen, CARD_COLOR, TEXT_COLOR, thai_font


class SelectTypeScreen(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app)

        card = self.card(self)
        card_h = max(500, int(760 * self._s))
        card.place(relx=0.5, rely=0.5, anchor="center", width=self.CARD_W, height=card_h)

        self.card_header(card, "โปรแกรมตรวจคุณภาพหน้าจอ", size=self.fs(24))

        body = tk.Frame(card, bg=CARD_COLOR)
        body.pack(fill="both", expand=True)

        self.title_label(body, "โปรดเลือกชนิดหน้าจอ", size=self.fs(36)).pack(pady=(20, 20))

        types = [
            ("diagnostic", "หน้าจอชนิดใช้วินิจฉัยทางการแพทย์\n(Diagnostic display)"),
            ("modality",   "หน้าจอชนิดใช้แสดงทางการแพทย์\n(Modality display)"),
            ("clinic",     "หน้าจอตรวจทานทางการแพทย์\n(Clinical Review display)"),
            ("ehr",        "หน้าจอสำหรับงานเวชระเบียน\n(Electronic Health Record display)"),
        ]

        for key, label in types:
            self.primary_btn(
                body, label,
                command=lambda k=key: self._select(k),
                fontsize=self.fs(32), padx=20, pady=6,
                width=46,
            ).pack(pady=5)

        bottom = tk.Frame(card, bg=CARD_COLOR)
        bottom.pack(side="bottom", fill="x", padx=16, pady=12)
        self.back_btn(bottom, "ย้อนกลับ", lambda: app.show("home"), fontsize=self.fs(26), width=12).pack(side="right", padx=4)

    def _select(self, screen_type: str):
        self.app.session["screen_type"] = screen_type
        self.app.show("select_period")
