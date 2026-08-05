import calendar
import datetime
import os
import platform
import subprocess
import tempfile
import tkinter as tk
from tkinter import ttk
from screens.base import (
    BaseScreen, BG_COLOR, CARD_COLOR, TEXT_COLOR, BORDER_CLR, BTN_BG, BTN_ACTIVE, thai_font,
    bind_treeview_tooltip,
)
from config import PERIOD_LABELS, SCREEN_TYPES
import database


def _show_calendar(root, anchor_widget, date_var: tk.StringVar):
    """เปิด popup calendar ใกล้ anchor_widget; date_var รับค่า DD/MM/YYYY"""
    # อ่านค่าเดิมถ้ามี
    try:
        d, m, y = date_var.get().split("/")
        sel = datetime.date(int(y), int(m), int(d))
    except Exception:
        sel = datetime.date.today()

    state = {"year": sel.year, "month": sel.month, "selected": sel}

    popup = tk.Toplevel(root)
    popup.overrideredirect(True)
    popup.configure(bg=BORDER_CLR)
    popup.resizable(False, False)

    # วางตำแหน่งใต้ anchor widget
    popup.update_idletasks()
    ax = anchor_widget.winfo_rootx()
    ay = anchor_widget.winfo_rooty() + anchor_widget.winfo_height()
    popup.geometry(f"+{ax}+{ay}")

    # ปิด popup เมื่อคลิกนอก
    def _close_if_outside(e):
        wx, wy = popup.winfo_rootx(), popup.winfo_rooty()
        ww, wh = popup.winfo_width(), popup.winfo_height()
        if not (wx <= e.x_root <= wx + ww and wy <= e.y_root <= wy + wh):
            popup.destroy()

    root.bind("<Button-1>", _close_if_outside, add=True)
    popup.bind("<Destroy>", lambda _: root.unbind("<Button-1>"))

    # ขนาด cell และ font ใหญ่ขึ้นให้กดง่าย
    _CW, _CH = 42, 36          # cell width / height (px)
    _FONT_HDR  = thai_font(18, "bold")
    _FONT_DAY  = thai_font(18)
    _FONT_DOW  = thai_font(15, "bold")
    _FONT_NAV  = thai_font(20, "bold")
    _FONT_CLR  = thai_font(15)

    frame = tk.Frame(popup, bg=CARD_COLOR, padx=8, pady=8)
    frame.pack(padx=1, pady=1)

    _MONTHS_TH = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน",
                  "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม",
                  "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]

    # ── header row ────────────────────────────────────────────────────────
    hdr = tk.Frame(frame, bg=CARD_COLOR)
    hdr.pack(fill="x", pady=(0, 6))

    prev_yr  = tk.Label(hdr, text="«", font=_FONT_NAV, bg=CARD_COLOR,
                        fg=TEXT_COLOR, cursor="hand2", padx=4, pady=4)
    prev_yr.pack(side="left")
    prev_lbl = tk.Label(hdr, text="‹", font=_FONT_NAV, bg=CARD_COLOR,
                        fg=TEXT_COLOR, cursor="hand2", padx=4, pady=4)
    prev_lbl.pack(side="left")

    month_lbl = tk.Label(hdr, text="", font=_FONT_HDR,
                         bg=CARD_COLOR, fg=TEXT_COLOR, anchor="center")
    month_lbl.pack(side="left", expand=True)

    next_yr  = tk.Label(hdr, text="»", font=_FONT_NAV, bg=CARD_COLOR,
                        fg=TEXT_COLOR, cursor="hand2", padx=4, pady=4)
    next_yr.pack(side="right")
    next_lbl = tk.Label(hdr, text="›", font=_FONT_NAV, bg=CARD_COLOR,
                        fg=TEXT_COLOR, cursor="hand2", padx=4, pady=4)
    next_lbl.pack(side="right")

    tk.Frame(frame, bg=BORDER_CLR, height=1).pack(fill="x", pady=(0, 6))

    day_frame = tk.Frame(frame, bg=CARD_COLOR)
    day_frame.pack()

    def _build(year, month):
        for w in day_frame.winfo_children():
            w.destroy()
        month_lbl.configure(text=f"{_MONTHS_TH[month]}  {year + 543}")

        for col, d in enumerate(["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]):
            tk.Label(day_frame, text=d, font=_FONT_DOW,
                     bg="#f0f0f0", fg="#555555",
                     width=0, anchor="center").grid(
                row=0, column=col, padx=2, pady=2,
                ipadx=0, ipady=4, sticky="nsew")
            day_frame.columnconfigure(col, minsize=_CW)

        today = datetime.date.today()
        for r, week in enumerate(calendar.monthcalendar(year, month), start=1):
            for c, day in enumerate(week):
                if day == 0:
                    tk.Label(day_frame, text="", bg=CARD_COLOR).grid(
                        row=r, column=c, padx=2, pady=2, sticky="nsew")
                    continue
                this_date = datetime.date(year, month, day)
                is_sel   = (this_date == state["selected"])
                is_today = (this_date == today)
                bg = BTN_BG    if is_sel   else ("#c8e6ff" if is_today else "#f7f7f7")
                fg = "#ffffff" if is_sel   else TEXT_COLOR
                btn = tk.Label(day_frame, text=str(day), font=_FONT_DAY,
                               bg=bg, fg=fg, anchor="center",
                               relief="flat", cursor="hand2")
                btn.grid(row=r, column=c, padx=2, pady=2,
                         ipadx=4, ipady=6, sticky="nsew")

                def _pick(dt=this_date):
                    state["selected"] = dt
                    date_var.set(f"{dt.day:02d}/{dt.month:02d}/{dt.year}")
                    popup.destroy()

                btn.bind("<ButtonRelease-1>", lambda _, fn=_pick: fn())
                btn.bind("<Enter>",  lambda _, b=btn, s=is_sel: b.configure(
                    bg=BTN_ACTIVE if s else "#daeeff"))
                btn.bind("<Leave>",  lambda _, b=btn, s=is_sel, od=bg: b.configure(bg=od))

    def _prev():
        m, y = state["month"] - 1, state["year"]
        if m < 1: m, y = 12, y - 1
        state["month"], state["year"] = m, y
        _build(y, m)

    def _next():
        m, y = state["month"] + 1, state["year"]
        if m > 12: m, y = 1, y + 1
        state["month"], state["year"] = m, y
        _build(y, m)

    def _prev_year():
        state["year"] -= 1
        _build(state["year"], state["month"])

    def _next_year():
        state["year"] += 1
        _build(state["year"], state["month"])

    prev_yr.bind("<ButtonRelease-1>",  lambda _: _prev_year())
    prev_lbl.bind("<ButtonRelease-1>", lambda _: _prev())
    next_lbl.bind("<ButtonRelease-1>", lambda _: _next())
    next_yr.bind("<ButtonRelease-1>",  lambda _: _next_year())

    # ── ปุ่มล้างวันที่ ──────────────────────────────────────────────────
    tk.Frame(frame, bg=BORDER_CLR, height=1).pack(fill="x", pady=(6, 4))
    clear_bar = tk.Frame(frame, bg=CARD_COLOR)
    clear_bar.pack(fill="x")
    clear_lbl = tk.Label(clear_bar, text="ล้างวันที่", font=_FONT_CLR,
                         bg=CARD_COLOR, fg="#0055cc", cursor="hand2", pady=2)
    clear_lbl.pack(side="right", padx=4)
    clear_lbl.bind("<ButtonRelease-1>", lambda _: [date_var.set(""), popup.destroy()])

    _build(state["year"], state["month"])


def _send_to_printer(path: str):
    """ส่งไฟล์ PDF ไปยังเครื่องพิมพ์ default"""
    system = platform.system()
    if system == "Darwin":
        result = subprocess.run(["open", "--print", path])
        if result.returncode != 0:
            subprocess.run(["open", path], check=True)
    elif system == "Windows":
        try:
            os.startfile(path, "print")
        except OSError:
            os.startfile(path)
    else:
        subprocess.run(["lp", path], check=True)


class HistoryScreen(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app)

        self.card_header(self, "ประวัติการทดสอบ", size=self.fs(24))

        # ── search bar ────────────────────────────────────────────────────
        search_bar = tk.Frame(self, bg=CARD_COLOR, bd=1, relief="solid")
        search_bar.pack(fill="x", padx=20, pady=(8, 4))
        
        search_inner = tk.Frame(search_bar, bg=CARD_COLOR)
        search_inner.pack(fill="x", expand=True, padx=16, pady=12)

        # Configure columns to distribute space evenly
        for i in range(6):
            search_inner.columnconfigure(i, weight=1 if i % 2 != 0 else 0)

        # Row 1
        tk.Label(search_inner, text="ชื่อผู้ประเมิน:", font=thai_font(self.fs(22)), bg=CARD_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, sticky="e", padx=(0, 8), pady=8)
        self.evaluator_var = tk.StringVar()
        tk.Entry(search_inner, textvariable=self.evaluator_var, font=thai_font(self.fs(22)), bg="#ffffff", relief="sunken", bd=1).grid(row=0, column=1, sticky="ew", padx=(0, 24), pady=8)

        self.hospital_var = tk.StringVar()
        self.asset_var = tk.StringVar()

        tk.Label(search_inner, text="ชนิดหน้าจอ:", font=thai_font(self.fs(22)), bg=CARD_COLOR, fg=TEXT_COLOR).grid(row=0, column=2, sticky="e", padx=(0, 8), pady=8)
        screen_type_frame = tk.Frame(search_inner, bg=CARD_COLOR)
        screen_type_frame.grid(row=0, column=3, sticky="ew", padx=(0, 24), pady=8)
        self.screen_type_var = tk.StringVar(value="")
        screen_type_choices = [("ทั้งหมด", "")] + [("Diagnostic", "diagnostic"), ("Modality", "modality"), ("Clinical", "clinic"), ("EHR", "ehr")]
        self._screen_type_menu = self._build_optionmenu(screen_type_frame, self.screen_type_var, screen_type_choices)
        self._screen_type_menu.pack(fill="x", expand=True)

        tk.Label(search_inner, text="รอบ:", font=thai_font(self.fs(22)), bg=CARD_COLOR, fg=TEXT_COLOR).grid(row=0, column=4, sticky="e", padx=(0, 8), pady=8)
        period_frame = tk.Frame(search_inner, bg=CARD_COLOR)
        period_frame.grid(row=0, column=5, sticky="ew", pady=8)
        self.period_var = tk.StringVar(value="")
        period_choices = [("ทั้งหมด", "")] + [(v, k) for k, v in PERIOD_LABELS.items()]
        self._period_menu = self._build_optionmenu(period_frame, self.period_var, period_choices)
        self._period_menu.pack(fill="x", expand=True)

        # Row 2
        date_frame = tk.Frame(search_inner, bg=CARD_COLOR)
        date_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=8)

        tk.Label(date_frame, text="วันที่:", font=thai_font(self.fs(22)), bg=CARD_COLOR, fg=TEXT_COLOR).pack(side="left", padx=(0, 8))

        self.date_from_var = tk.StringVar()
        tk.Entry(date_frame, textvariable=self.date_from_var, font=thai_font(self.fs(22)), width=10, bg="#ffffff", relief="sunken", bd=1, state="readonly", readonlybackground="#ffffff").pack(side="left", fill="x", expand=True)
        cal_from = tk.Label(date_frame, text="📅", font=thai_font(self.fs(18)), bg=CARD_COLOR, cursor="hand2")
        cal_from.pack(side="left", padx=(4, 8))
        cal_from.bind("<ButtonRelease-1>", lambda _: _show_calendar(self.app, cal_from, self.date_from_var))

        tk.Label(date_frame, text="ถึง", font=thai_font(self.fs(22)), bg=CARD_COLOR, fg=TEXT_COLOR).pack(side="left", padx=(0, 8))

        self.date_to_var = tk.StringVar()
        tk.Entry(date_frame, textvariable=self.date_to_var, font=thai_font(self.fs(22)), width=10, bg="#ffffff", relief="sunken", bd=1, state="readonly", readonlybackground="#ffffff").pack(side="left", fill="x", expand=True)
        cal_to = tk.Label(date_frame, text="📅", font=thai_font(self.fs(18)), bg=CARD_COLOR, cursor="hand2")
        cal_to.pack(side="left", padx=(4, 0))
        cal_to.bind("<ButtonRelease-1>", lambda _: _show_calendar(self.app, cal_to, self.date_to_var))

        search_btn_frame = tk.Frame(search_inner, bg=CARD_COLOR)
        search_btn_frame.grid(row=1, column=4, columnspan=2, sticky="e", pady=8)
        search_icon = tk.Label(search_btn_frame, text="🔍 ค้นหา", font=thai_font(self.fs(22), "bold"), bg=BTN_BG, fg="white", cursor="hand2", padx=24, pady=4, relief="flat")
        search_icon.pack(side="right")
        search_icon.bind("<ButtonRelease-1>", lambda _: self._search())
        search_icon.bind("<Enter>", lambda e: e.widget.configure(bg=BTN_ACTIVE))
        search_icon.bind("<Leave>", lambda e: e.widget.configure(bg=BTN_BG))

        # ── table ─────────────────────────────────────────────────────────
        table_frame = tk.Frame(self, bg=BG_COLOR)
        table_frame.pack(fill="both", expand=True, padx=24, pady=(4, 12))

        style = ttk.Style()
        style.configure("History.Treeview",
                         font=thai_font(self.fs(26)),
                         rowheight=max(22, int(36 * self._s)),
                         background=CARD_COLOR,
                         fieldbackground=CARD_COLOR,
                         foreground=TEXT_COLOR)
        style.configure("History.Treeview.Heading",
                         font=thai_font(self.fs(26), "bold"),
                         background=BG_COLOR,
                         foreground=TEXT_COLOR,
                         relief="flat")
        style.map("History.Treeview",
                  background=[("selected", "#b0c8e8")])

        cols = ("ครั้งที่", "วันที่", "โรงพยาบาล", "ชนิดจอ", "รอบ", "ผู้ประเมิน", "คุรุภัณฑ์")
        self.tree = ttk.Treeview(table_frame, columns=cols,
                                  show="headings", style="History.Treeview",
                                  selectmode="extended")

        widths  = [int(w * self._s) for w in [80, 180, 220, 140, 130, 180, 200]]
        anchors = ["center", "center", "w", "center", "center", "w", "w"]
        for col, w, a in zip(cols, widths, anchors):
            self.tree.heading(col, text=col, anchor=a)
            self.tree.column(col, width=w, anchor=a, stretch=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                   command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")
        bind_treeview_tooltip(self.tree)

        self.tree.bind("<Double-1>", self._on_double_click)

        # ── bottom bar ────────────────────────────────────────────────────
        btn_bar = tk.Frame(self, bg=BG_COLOR)
        btn_bar.pack(side="bottom", fill="x", padx=20, pady=12)

        self.primary_btn(btn_bar, "ดูรายละเอียด",
                         self._view_selected, fontsize=self.fs(26), width=14).pack(side="left", padx=4)
        self.primary_btn(btn_bar, "ดาวน์โหลด PDF",
                         self._download_selected, fontsize=self.fs(26), width=16).pack(side="left", padx=4)
        self.primary_btn(btn_bar, "พิมพ์",
                         self._print_selected, fontsize=self.fs(26), width=10).pack(side="left", padx=4)
        self._hint_lbl = tk.Label(btn_bar, text="", font=thai_font(self.fs(22)),
                                  bg=BG_COLOR, fg="#cc0000")
        self._hint_lbl.pack(side="left", padx=8)
        self.back_btn(btn_bar, "กลับหน้าหลัก",
                      lambda: app.show("home"), fontsize=self.fs(26), width=14).pack(side="right", padx=4)

        self._rows: list[dict] = []

    # ── helpers ───────────────────────────────────────────────────────────

    def _build_optionmenu(self, parent, var, choices):
        labels = [c[0] for c in choices]
        values = [c[1] for c in choices]
        var.set(values[0])

        wrapper = tk.Frame(parent, bg=BORDER_CLR)
        display_var = tk.StringVar(value=labels[0])
        inner = tk.Label(wrapper, textvariable=display_var, font=thai_font(self.fs(26)),
                          bg="#ffffff", fg=TEXT_COLOR, padx=6, pady=2, cursor="hand2")

        def pick(lbl, val):
            var.set(val)
            display_var.set(lbl)
            menu.unpost()

        menu = tk.Menu(wrapper, tearoff=0, font=thai_font(self.fs(26)))
        for lbl, val in zip(labels, values):
            menu.add_command(label=lbl, command=lambda l=lbl, v=val: pick(l, v))

        def show_menu(e):
            try:
                menu.tk_popup(inner.winfo_rootx(), inner.winfo_rooty() + inner.winfo_height())
            finally:
                menu.grab_release()

        inner.bind("<ButtonRelease-1>", show_menu)
        inner.pack(padx=1, pady=1, fill="both", expand=True)
        return wrapper

    # ── on_show ───────────────────────────────────────────────────────────

    def on_show(self, **_):
        self._search()

    @staticmethod
    def _parse_date(text: str) -> str:
        """แปลง DD/MM/YYYY → YYYY-MM-DD สำหรับ SQLite; คืน "" ถ้าไม่ถูกต้อง"""
        text = text.strip()
        if not text:
            return ""
        try:
            parts = text.split("/")
            if len(parts) != 3:
                return ""
            d, m, y = parts
            return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
        except Exception:
            return ""

    def _search(self):
        rows = database.search_evaluations(
            evaluator=self.evaluator_var.get().strip(),
            hospital=self.hospital_var.get().strip(),
            screen_model=self.asset_var.get().strip(),
            screen_type=self.screen_type_var.get(),
            period=self.period_var.get(),
            date_from=self._parse_date(self.date_from_var.get()),
            date_to=self._parse_date(self.date_to_var.get()),
        )
        self._rows = rows
        self.tree.delete(*self.tree.get_children())

        type_map   = {"diagnostic": "Diagnostic", "modality": "Modality", "clinic": "Clinical", "ehr": "EHR"}
        period_map = {"monthly": "รายเดือน", "quarterly": "ราย 3 เดือน", "annual": "ประจำปี"}

        for r in rows:
            eval_dt_str = r["eval_datetime"]
            try:
                # Expected format from DB: "YYYY-MM-DD HH:MM:SS"
                dt_obj = datetime.datetime.strptime(eval_dt_str, "%Y-%m-%d %H:%M:%S")
                thai_year = dt_obj.year + 543
                display_date = f"{dt_obj.day:02d}/{dt_obj.month:02d}/{thai_year} {dt_obj.strftime('%H:%M:%S')}"
            except Exception:
                display_date = eval_dt_str

            rank = database.get_eval_rank(r["screen_type"], r["period"], r["id"])

            self.tree.insert("", "end", iid=str(r["id"]), values=(
                rank,
                display_date,
                r["hospital_name"],
                type_map.get(r["screen_type"], r["screen_type"]),
                period_map.get(r["period"], r["period"]),
                r["evaluator_name"],
                r["screen_model"],
            ))
    def _selected_id(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _on_double_click(self, _event):
        self._view_selected()

    def _download_selected(self):
        from tkinter import filedialog, messagebox
        from config import TEST_CONFIG
        from reports.pdf_export import export_history_result
        import os

        ids = [int(iid) for iid in self.tree.selection()]
        if not ids:
            self._hint_lbl.configure(text="กรุณาเลือกรายการที่ต้องการดาวน์โหลดก่อน")
            return
        self._hint_lbl.configure(text="")

        if len(ids) == 1:
            ev = database.get_evaluation(ids[0])
            if not ev:
                return
            groups = TEST_CONFIG.get(ev["screen_type"], {}).get(ev["period"], [])
            default = (f"ผลการประเมิน_{ev['hospital_name']}_{ev['eval_datetime']}.pdf"
                       .replace(" ", "_").replace(":", "-"))
            path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=default,
            )
            if not path:
                return
            try:
                r = database.get_eval_rank(ev["screen_type"], ev["period"], ev["id"])
                export_history_result(ev, groups, path, rank=r)
                messagebox.showinfo("บันทึกสำเร็จ", f"บันทึก PDF เรียบร้อย\n{path}")
            except Exception as e:
                messagebox.showerror("ข้อผิดพลาด", str(e))
        else:
            folder = filedialog.askdirectory(title=f"เลือกโฟลเดอร์บันทึก PDF {len(ids)} ชุด")
            if not folder:
                return
            errors = []
            for eval_id in ids:
                ev = database.get_evaluation(eval_id)
                if not ev:
                    continue
                groups = TEST_CONFIG.get(ev["screen_type"], {}).get(ev["period"], [])
                fname = (f"ผลการประเมิน_{ev['hospital_name']}_{ev['eval_datetime']}.pdf"
                         .replace(" ", "_").replace(":", "-"))
                try:
                    r = database.get_eval_rank(ev["screen_type"], ev["period"], ev["id"])
                    export_history_result(ev, groups, os.path.join(folder, fname), rank=r)
                except Exception as e:
                    errors.append(f"{fname}: {e}")
            if errors:
                messagebox.showerror("ข้อผิดพลาด", "\n".join(errors))
            else:
                messagebox.showinfo("บันทึกสำเร็จ",
                                    f"บันทึก PDF {len(ids)} ไฟล์ เรียบร้อย\nโฟลเดอร์: {folder}")

    def _print_selected(self):
        from config import TEST_CONFIG
        from reports.pdf_export import export_history_result

        ids = [int(iid) for iid in self.tree.selection()]
        if not ids:
            self._hint_lbl.configure(text="กรุณาเลือกรายการที่ต้องการพิมพ์ก่อน")
            return
        self._hint_lbl.configure(text="")

        from tkinter import messagebox
        if not messagebox.askyesno("ยืนยันการพิมพ์", f"ต้องการพิมพ์รายการที่เลือก {len(ids)} ชุด ใช่หรือไม่?"):
            return
        try:
            for eval_id in ids:
                ev = database.get_evaluation(eval_id)
                if not ev:
                    continue
                groups = TEST_CONFIG.get(ev["screen_type"], {}).get(ev["period"], [])
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                    tmp = f.name
                r = database.get_eval_rank(ev["screen_type"], ev["period"], ev["id"])
                export_history_result(ev, groups, tmp, rank=r)
                _send_to_printer(tmp)
            messagebox.showinfo("ส่งพิมพ์สำเร็จ", f"ส่งรายการพิมพ์ {len(ids)} ชุด เรียบร้อยแล้ว")
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถพิมพ์ได้\n{e}")

    def _view_selected(self):
        eval_id = self._selected_id()
        if eval_id is None:
            self._hint_lbl.configure(text="กรุณาเลือกรายการก่อน หรือดับเบิลคลิกที่แถว")
            return
        self._hint_lbl.configure(text="")
        ev = database.get_evaluation(eval_id)
        if not ev:
            return
        self.app.session["history_eval"] = ev
        self.app.show("history_result")
