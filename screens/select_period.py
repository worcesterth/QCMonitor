import tkinter as tk
from screens.base import BaseScreen, CARD_COLOR
from config import PERIODS, PERIOD_LABELS


class SelectPeriodScreen(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app)

        card = self.card(self)
        card.place(relx=0.5, rely=0.5, anchor="center", width=self.CARD_W, height=self.CARD_H)

        self.card_header(card, "โปรแกรมตรวจคุณภาพหน้าจอ", size=self.fs(24))

        self.body = tk.Frame(card, bg=CARD_COLOR)
        self.body.pack(fill="both", expand=True)

        bottom = tk.Frame(card, bg=CARD_COLOR)
        bottom.pack(side="bottom", fill="x", padx=16, pady=16)
        self.back_btn(bottom, "ย้อนกลับ", lambda: self.app.show("select_type"), fontsize=self.fs(26), width=12).pack(side="right", padx=4)

    def on_show(self, **_):
        for w in self.body.winfo_children():
            w.destroy()

        screen_type = self.app.session.get("screen_type", "diagnostic")
        periods = PERIODS.get(screen_type, [])

        self.title_label(self.body, "โปรดเลือกรูปแบบการประเมิน", size=self.fs(50)).pack(pady=(40, 50))

        period_colors = {
            "monthly":   ("#3b82f6", "#2563eb"),
            "quarterly": ("#16a34a", "#15803d"),
            "annual":    ("#f97316", "#ea6c0a"),
        }

        for period in periods:
            label = PERIOD_LABELS.get(period, period)
            bg, active = period_colors.get(period, ("#FD9E50", "#e08840"))
            self.primary_btn(
                self.body, label,
                command=lambda p=period: self._select(p),
                fontsize=self.fs(26), padx=20, pady=6,
                width=30,
                btn_bg=bg, btn_fg="#ffffff", btn_active=active,
            ).pack(pady=10)

    def _select(self, period: str):
        self.app.session["period"] = period
        self.app.show("login")
