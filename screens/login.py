import tkinter as tk
import tkinter.ttk as ttk
from datetime import datetime
from screens.base import (BaseScreen, CARD_COLOR, ENTRY_BG,
                           TEXT_COLOR, thai_font)
from config import PERIOD_LABELS
from database import get_settings, get_all_users, verify_login


class LoginScreen(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app)

        # ── style สำหรับ Combobox ────────────────────────────────────────────
        style = ttk.Style()
        style.theme_use("default")
        fname, fsize, _ = thai_font(self.fs(26))
        style.configure("Login.TCombobox",
                        font=(fname, fsize),
                        fieldbackground=ENTRY_BG,
                        background=ENTRY_BG,
                        foreground=TEXT_COLOR,
                        selectbackground=ENTRY_BG,
                        selectforeground=TEXT_COLOR,
                        padding=4)
        style.map("Login.TCombobox",
                  fieldbackground=[("readonly", ENTRY_BG)],
                  foreground=[("readonly", TEXT_COLOR)])

        card = self.card(self)
        card.place(relx=0.5, rely=0.5, anchor="center", width=self.CARD_W, height=self.CARD_HL)

        self.card_header(card, "Log-in", size=self.fs(24))

        body = tk.Frame(card, bg=CARD_COLOR)
        body.pack(fill="both", expand=True, padx=36, pady=20)

        self._period_bar = tk.Frame(body, height=10)
        self._period_bar.pack(fill="x", pady=(0, 6))

        self.title_lbl = tk.Label(body, text="", font=thai_font(self.fs(16), "bold"),
                                  bg=CARD_COLOR, fg=TEXT_COLOR)
        self.title_lbl.pack(anchor="w", pady=(0, 4))

        tk.Label(body, text="กรุณากรอกรายละเอียดการประเมิน",
                 font=thai_font(self.fs(35)), bg=CARD_COLOR, fg=TEXT_COLOR).pack(anchor="w", pady=(0, 14))

        form = tk.Frame(body, bg=CARD_COLOR)
        form.pack(fill="x", pady=4)

        lbl_font = thai_font(self.fs(26))
        val_font  = thai_font(self.fs(26))

        # ── ชื่อโรงพยาบาล (Label) ────────────────────────────────────────────
        tk.Label(form, text="ชื่อโรงพยาบาล :", font=lbl_font, bg=CARD_COLOR,
                 fg=TEXT_COLOR, anchor="e").grid(row=0, column=0, sticky="e",
                                                  padx=(0, 10), pady=8)
        self.hospital_lbl = tk.Label(form, text="", font=val_font, bg=CARD_COLOR,
                                     fg=TEXT_COLOR, anchor="w")
        self.hospital_lbl.grid(row=0, column=1, sticky="w", pady=8)

        # ── หมายเลขคุรุภัณฑ์ (Label) ─────────────────────────────────────────
        tk.Label(form, text="หมายเลขคุรุภัณฑ์ :", font=lbl_font, bg=CARD_COLOR,
                 fg=TEXT_COLOR, anchor="e").grid(row=1, column=0, sticky="e",
                                                   padx=(0, 10), pady=8)
        self.equipment_lbl = tk.Label(form, text="", font=val_font, bg=CARD_COLOR,
                                      fg=TEXT_COLOR, anchor="w")
        self.equipment_lbl.grid(row=1, column=1, sticky="w", pady=8)

        # ── ชื่อผู้ประเมิน (Combobox + filter) ───────────────────────────────
        tk.Label(form, text="ชื่อผู้ประเมิน :", font=lbl_font, bg=CARD_COLOR,
                 fg=TEXT_COLOR, anchor="e").grid(row=2, column=0, sticky="e",
                                                  padx=(0, 10), pady=8)
        self._all_names: list[str] = []
        self.name_combo = ttk.Combobox(form, style="Login.TCombobox",
                                       font=val_font, width=32, state="readonly")
        self.name_combo.grid(row=2, column=1, sticky="w", pady=8)

        # ── รหัสผ่าน ──────────────────────────────────────────────────────────
        tk.Label(form, text="รหัสผ่าน :", font=lbl_font, bg=CARD_COLOR,
                 fg=TEXT_COLOR, anchor="e").grid(row=3, column=0, sticky="e",
                                                  padx=(0, 10), pady=8)
        self.pw_entry = tk.Entry(form, font=val_font, bg=ENTRY_BG, fg=TEXT_COLOR,
                                 relief="sunken", bd=2, width=34, show="*")
        self.pw_entry.grid(row=3, column=1, sticky="w", pady=8)

        self.error_lbl = tk.Label(body, text="", font=thai_font(self.fs(22)),
                                  bg=CARD_COLOR, fg="#cc0000")
        self.error_lbl.pack(anchor="w")

        self.dt_lbl = tk.Label(body, text="", font=thai_font(self.fs(26)),
                               bg=CARD_COLOR, fg=TEXT_COLOR)
        self.dt_lbl.pack(anchor="w", pady=(8, 0))

        # ปุ่มล่าง
        btn_row = tk.Frame(card, bg=CARD_COLOR)
        btn_row.pack(side="bottom", fill="x", padx=16, pady=12)
        self.primary_btn(btn_row, "ถัดไป",    self._next, fontsize=self.fs(26), width=12).pack(side="right", padx=4)
        self.back_btn(btn_row, "ย้อนกลับ", self._back, fontsize=self.fs(26), width=12).pack(side="right", padx=4)

    # ── helpers ───────────────────────────────────────────────────────────────

    def on_show(self, **_):
        session = self.app.session
        period = session.get("period", "")
        screen_type = session.get("screen_type", "")
        period_lbl = PERIOD_LABELS.get(period, period)
        type_map = {"diagnostic": "Diagnostic", "modality": "Modality",
                    "clinic": "Clinical Review", "ehr": "Electronic Health Record"}
        period_colors = {"monthly": "#3b82f6", "quarterly": "#16a34a", "annual": "#f97316"}
        bar_color = period_colors.get(period, "#888888")
        self._period_bar.configure(bg=bar_color)
        self.title_lbl.configure(
            text=f"{period_lbl} ({type_map.get(screen_type, '')})", font=thai_font(self.fs(40)))

        settings = get_settings()
        self.hospital_lbl.configure(
            text=settings["hospital_name"] if settings else "-")
        self.equipment_lbl.configure(
            text=settings["screen_model"] if settings else "-")
        if settings:
            session["hospital_name"] = settings["hospital_name"]
            session["screen_model"]  = settings["screen_model"]

        users = get_all_users()
        self._all_names = [
            f"{u['name']} {u.get('lastname', '')}".strip() for u in users
        ]
        self.name_combo["values"] = self._all_names
        self.name_combo.set(session.get("evaluator_name", ""))

        self.pw_entry.delete(0, "end")
        self.pw_entry.configure(highlightthickness=0)
        self.error_lbl.configure(text="")

        now = datetime.now()
        thai_year = now.year + 543
        self.dt_lbl.configure(
            text=f"วันที่และเวลาในการทดสอบ : {now.strftime('%d/%m/')}{thai_year}  {now.strftime('%H:%M:%S')}")
        session["eval_datetime"] = now.strftime("%Y-%m-%d %H:%M:%S")

    # ── actions ───────────────────────────────────────────────────────────────

    def _back(self):
        for key in ("evaluator_name", "eval_datetime"):
            self.app.session.pop(key, None)
        self.name_combo.set("")
        self.pw_entry.delete(0, "end")
        self.error_lbl.configure(text="")
        self.app.show("select_period")

    def _next(self):
        session = self.app.session
        name = self.name_combo.get().strip()
        pw   = self.pw_entry.get().strip()
        has_error = False

        # validate name
        if not name:
            has_error = True

        # validate password
        if not pw:
            self.pw_entry.configure(highlightbackground="#cc0000",
                                    highlightthickness=2, highlightcolor="#cc0000")
            has_error = True
        else:
            self.pw_entry.configure(highlightthickness=0)

        if has_error:
            self.error_lbl.configure(text="กรุณากรอกข้อมูลให้ครบ")
            return

        if not verify_login(name, pw):
            self.pw_entry.configure(highlightbackground="#cc0000",
                                    highlightthickness=2, highlightcolor="#cc0000")
            self.error_lbl.configure(text="ชื่อหรือรหัสผ่านไม่ถูกต้อง")
            return

        self.error_lbl.configure(text="")
        session["evaluator_name"] = name
        self.app.show("confirm")
