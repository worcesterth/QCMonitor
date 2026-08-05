import tkinter as tk
from screens.base import BaseScreen, CARD_COLOR, TEXT_COLOR, thai_font
from config import PERIOD_LABELS


class ConfirmScreen(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app)

        card = self.card(self)
        card.place(relx=0.5, rely=0.5, anchor="center", width=self.CARD_W, height=self.CARD_H)

        self.card_header(card, "ยืนยันข้อมูล", size=self.fs(24))

        body = tk.Frame(card, bg=CARD_COLOR)
        body.pack(fill="both", expand=True, padx=36, pady=20)

        self._period_bar = tk.Frame(body, height=10)
        self._period_bar.pack(fill="x", pady=(0, 6))

        self.title_lbl = tk.Label(body, text="", font=thai_font(self.fs(16), "bold"), bg=CARD_COLOR, fg=TEXT_COLOR)
        self.title_lbl.pack(anchor="w", pady=(0, 4))

        tk.Label(body, text="กรุณาตรวจสอบข้อมูลก่อนเริ่มการทดสอบ",
                 font=thai_font(self.fs(35)), bg=CARD_COLOR, fg=TEXT_COLOR).pack(anchor="w", pady=(0, 14))

        info = tk.Frame(body, bg=CARD_COLOR)
        info.pack(fill="x")

        self.info_labels: dict[str, tk.Label] = {}
        rows = [
            ("ชื่อโรงพยาบาล:", "hospital_name"),
            ("ชื่อผู้ประเมิน:", "evaluator_name"),
            ("หมายเลขคุรุภัณฑ์:", "screen_model"),
        ]
        for row, (lbl, key) in enumerate(rows):
            tk.Label(info, text=lbl, font=thai_font(self.fs(26)), bg=CARD_COLOR,
                     fg=TEXT_COLOR, anchor="e").grid(
                row=row, column=0, sticky="e", padx=(0, 10), pady=6)
            val_lbl = tk.Label(info, text="", font=thai_font(self.fs(26)), bg=CARD_COLOR,
                               fg=TEXT_COLOR, anchor="w")
            val_lbl.grid(row=row, column=1, sticky="w", pady=6)
            self.info_labels[key] = val_lbl

        self.dt_lbl = tk.Label(body, text="", font=thai_font(self.fs(26)), bg=CARD_COLOR, fg=TEXT_COLOR)
        self.dt_lbl.pack(anchor="w", pady=(16, 0))

        btn_row = tk.Frame(card, bg=CARD_COLOR)
        btn_row.pack(side="bottom", fill="x", padx=16, pady=12)
        self.primary_btn(btn_row, "เริ่มการทดสอบ", self._start, fontsize=self.fs(26), width=16).pack(side="right", padx=4)
        self.primary_btn(btn_row, "แก้ไข",         self._edit,  fontsize=self.fs(26), width=12).pack(side="right", padx=4)

    def on_show(self, **_):
        session = self.app.session
        period = session.get("period", "")
        screen_type = session.get("screen_type", "")
        period_lbl = PERIOD_LABELS.get(period, period)
        type_map = {"diagnostic": "Diagnostic", "modality": "Modality", "clinic": "Clinical Review", "ehr": "Electronic Health Record"}

        self.title_lbl.configure(text=f"{period_lbl} ({type_map.get(screen_type, '')})", font=thai_font(self.fs(40)))

        period_colors = {"monthly": "#3b82f6", "quarterly": "#16a34a", "annual": "#f97316"}
        self._period_bar.configure(bg=period_colors.get(period, "#888888"))

        for key, lbl in self.info_labels.items():
            lbl.configure(text=session.get(key, ""))

        import datetime
        eval_dt_str = session.get('eval_datetime', '')
        try:
            dt_obj = datetime.datetime.strptime(eval_dt_str, "%Y-%m-%d %H:%M:%S")
            display_date = f"{dt_obj.day:02d}/{dt_obj.month:02d}/{dt_obj.year + 543} {dt_obj.strftime('%H:%M:%S')}"
        except Exception:
            display_date = eval_dt_str

        self.dt_lbl.configure(text=f"วันที่และเวลาในการทดสอบ: {display_date}")

    def _edit(self):
        self.app.show("login")

    def _start(self):
        self.app.show("instructions")
