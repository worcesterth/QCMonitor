# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
from screens.base import (
    BaseScreen, BG_COLOR, CARD_COLOR, TEXT_COLOR,
    BORDER_CLR, PASS_GREEN, FAIL_RED, thai_font,
)

_HEADS      = ["หัวข้อการประเมิน", "ผลการประเมิน", "หมายเหตุ"]
_ANCHORS    = ["w", "center", "w"]
_WIDTHS_REF = [620, 140]   # คอลัมน์สุดท้าย (หมายเหตุ) flexible
ALT_ROW     = "#f5f5f5"


class ResultsScreen(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._widths = [int(w * self._s) for w in _WIDTHS_REF]

        # ── header ────────────────────────────────────────────────────
        self.card_header(self, "ผลการประเมินคุณภาพหน้าจอ", size=self.fs(26))

        # ── info bar ──────────────────────────────────────────────────
        info_bar = tk.Frame(self, bg=BG_COLOR, bd=1, relief="solid")
        info_bar.pack(fill="x", padx=20, pady=(8, 4))
        self.info_lbl = tk.Label(info_bar, text="", font=thai_font(self.fs(26)),
                                  bg=BG_COLOR, fg=TEXT_COLOR)
        self.info_lbl.pack(side="left")

        # ── table container ───────────────────────────────────────────
        tbl = tk.Frame(self, bg=BG_COLOR)
        tbl.pack(fill="both", expand=True, padx=20, pady=4)

        # header row (fixed)
        head_bar = tk.Frame(tbl, bg=BG_COLOR)
        head_bar.pack(fill="x")
        self._build_row(head_bar, _HEADS, "#ffffff", TEXT_COLOR,
                        thai_font(self.fs(26), "bold"), pady=10)
        tk.Frame(tbl, bg=BORDER_CLR, height=2).pack(fill="x")

        # scrollable body
        body_outer = tk.Frame(tbl, bg=BG_COLOR)
        body_outer.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(body_outer, bg=CARD_COLOR, highlightthickness=0)
        vbar = ttk.Scrollbar(body_outer, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vbar.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")

        self._body = tk.Frame(self._canvas, bg=CARD_COLOR)
        self._win  = self._canvas.create_window((0, 0), window=self._body, anchor="nw")

        self._body.bind("<Configure>",
                        lambda _: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", self._on_canvas_resize)
        self._canvas.bind("<MouseWheel>",
                          lambda e: self._canvas.yview_scroll(-1 if e.delta > 0 else 1, "units"))

        self._note_labels: list[tk.Label] = []

        # ── ปุ่มล่าง ──────────────────────────────────────────────────
        btn_bar = tk.Frame(self, bg=BG_COLOR)
        btn_bar.pack(side="bottom", fill="x", padx=20, pady=12)

        self.primary_btn(btn_bar, "บันทึกผล",
                         self._save, fontsize=self.fs(26), width=14).pack(side="right", padx=4)
        self.primary_btn(btn_bar, "ไม่บันทึกผล",
                         self._discard, fontsize=self.fs(26), width=14).pack(side="right", padx=4)
        self.primary_btn(btn_bar, "ทดสอบใหม่",
                         self._retest, fontsize=self.fs(26), width=14).pack(side="left", padx=4)

    # ── table helpers ─────────────────────────────────────────────────

    def _build_row(self, parent, values, bg, fg, font, pady=6):
        row = tk.Frame(parent, bg=bg)
        row.pack(fill="x")
        for i, w in enumerate(self._widths):
            row.columnconfigure(i, minsize=w, weight=0)
        row.columnconfigure(len(self._widths), weight=1)
        note_lbl = None
        for i, (text, anchor) in enumerate(zip(values, _ANCHORS)):
            w = self._widths[i] if i < len(self._widths) else 0
            lbl = tk.Label(row, text=text, font=font, fg=fg, bg=bg,
                           anchor=anchor, padx=10, pady=pady,
                           wraplength=max(0, w - 12) if w else 0,
                           justify="left")
            lbl.grid(row=0, column=i, sticky="nsew")
            if i == len(self._widths):
                note_lbl = lbl
        return note_lbl

    def _on_canvas_resize(self, e):
        self._canvas.itemconfig(self._win, width=e.width)
        self._refresh_note_wrap(e.width)

    def _refresh_note_wrap(self, canvas_w=None):
        if canvas_w is None:
            canvas_w = self._canvas.winfo_width()
        note_w = max(80, canvas_w - sum(self._widths) - 12)
        for lbl in self._note_labels:
            lbl.configure(wraplength=note_w)

    def _clear(self):
        for w in self._body.winfo_children():
            w.destroy()
        self._note_labels.clear()
        self._canvas.yview_moveto(0)

    # ── on_show ───────────────────────────────────────────────────────

    def on_show(self, **_):
        session = self.app.session
        items   = session.get("test_items", [])
        answers = session.get("answers", {})

        type_map   = {"diagnostic": "Diagnostic", "modality": "Modality", "clinic": "Clinical Review"}
        period_map = {"monthly": "ประจำเดือน", "quarterly": "ประจำ 3 เดือน", "annual": "ประจำปี"}
        stype  = type_map.get(session.get("screen_type", ""), "")
        period = period_map.get(session.get("period", ""), "")

        eval_dt_str = session.get("eval_datetime", "")
        try:
            import datetime
            dt_obj = datetime.datetime.strptime(eval_dt_str, "%Y-%m-%d %H:%M:%S")
            thai_year = dt_obj.year + 543
            display_date = f"{dt_obj.day:02d}/{dt_obj.month:02d}/{thai_year} {dt_obj.strftime('%H:%M:%S')}"
        except Exception:
            display_date = eval_dt_str

        self.info_lbl.configure(
            text=f"{session.get('hospital_name','')}  |  {session.get('evaluator_name','')}  |  {stype}  |  {period}  |  {display_date}"
        )

        self._clear()
        overall_pass = True
        current_group = None
        row_idx = 0

        for item in items:
            if item["group_id"] != current_group:
                current_group = item["group_id"]
                self._build_row(self._body,
                                [item["group_title"], "", ""],
                                "#BFBFBF", TEXT_COLOR,
                                thai_font(self.fs(26), "bold"), pady=10)

            ans = answers.get(item["item_id"])
            if ans:
                result_text = "ผ่าน" if ans["passed"] else "ไม่ผ่าน"
                fg = PASS_GREEN if ans["passed"] else FAIL_RED
                notes = ans.get("notes", "")
                if ans.get("failed_channels"):
                    fc = ans["failed_channels"]
                    ch_str = ", ".join(str(c) for c in fc)
                    if item.get("question_type") == "yes_no_channels_text":
                        notes = (f"จำนวนภาพที่ Pixel ไม่สม่ำเสมอ: {len(fc)} ภาพ\n"
                                 f"ค่า Pixel ของภาพที่ไม่เห็น: {ch_str}") + (f"  {notes}" if notes else "")
                    else:
                        ch_lbl = item.get("channel_label", "ช่อง")
                        notes = f"ค่า Pixel ของ{ch_lbl}ที่ไม่เห็น: {ch_str}" + (f"  {notes}" if notes else "")
                if not ans["passed"]:
                    overall_pass = False
            else:
                result_text = "ไม่ได้ตอบ"
                fg = "#888888"
                notes = ""
                overall_pass = False

            row_bg = CARD_COLOR if row_idx % 2 == 0 else ALT_ROW
            row_idx += 1
            note_lbl = self._build_row(self._body,
                                       [f"  {item['title']}", result_text, notes],
                                       row_bg, fg, thai_font(self.fs(26)), pady=8)
            if note_lbl:
                self._note_labels.append(note_lbl)

        session["overall_pass"] = overall_pass
        self.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._canvas.yview_moveto(0)
        self.after(10, self._refresh_note_wrap)

    # ── actions ───────────────────────────────────────────────────────

    def _save(self):
        self.app.show("after_save")

    def _discard(self):
        self.app.session.clear()
        self.app.show("home")

    def _retest(self):
        session = self.app.session
        session["current_item_idx"] = 0
        session["answers"] = {}
        self.app.show("test_runner")

    def _print_dialog(self):
        from tkinter import filedialog, messagebox
        from screens.base import CARD_COLOR, TEXT_COLOR, ENTRY_BG, thai_font
        from config import TEST_CONFIG
        from reports.pdf_export import export_history_result
        import os

        session = self.app.session

        dlg = tk.Toplevel(self.app)
        dlg.title("บันทึก PDF")
        dlg.configure(bg=CARD_COLOR)
        dlg.resizable(False, False)
        dlg.transient(self.app)
        dlg.grab_set()
        w, h = int(400 * self._s), int(200 * self._s)
        px = self.app.winfo_x() + self.app.winfo_width()  // 2 - w // 2
        py = self.app.winfo_y() + self.app.winfo_height() // 2 - h // 2
        dlg.geometry(f"{w}x{h}+{px}+{py}")

        tk.Label(dlg, text="จำนวนชุดที่ต้องการ", font=thai_font(self.fs(26), "bold"),
                 bg=CARD_COLOR, fg=TEXT_COLOR).pack(pady=(20, 8))

        spin_var = tk.IntVar(value=1)
        tk.Spinbox(dlg, from_=1, to=99, textvariable=spin_var,
                   font=thai_font(self.fs(26)), width=6, justify="center",
                   bg=ENTRY_BG, fg=TEXT_COLOR, relief="sunken", bd=2).pack()

        err_lbl = tk.Label(dlg, text="", font=thai_font(self.fs(20)), bg=CARD_COLOR, fg="#cc0000")
        err_lbl.pack(pady=(4, 0))

        btn_bar = tk.Frame(dlg, bg=CARD_COLOR)
        btn_bar.pack(pady=12)

        def save():
            copies = spin_var.get()
            ev = {
                "hospital_name":  session.get("hospital_name", ""),
                "evaluator_name": session.get("evaluator_name", ""),
                "eval_datetime":  session.get("eval_datetime", ""),
                "screen_type":    session.get("screen_type", ""),
                "period":         session.get("period", ""),
                "answers":        session.get("answers", {}),
            }
            groups = TEST_CONFIG.get(ev["screen_type"], {}).get(ev["period"], [])
            base_name = (f"ผลการประเมิน_{ev['hospital_name']}_{ev['eval_datetime']}"
                         .replace(" ", "_").replace(":", "-"))

            if copies == 1:
                path = filedialog.asksaveasfilename(
                    parent=dlg, defaultextension=".pdf",
                    filetypes=[("PDF files", "*.pdf")],
                    initialfile=f"{base_name}.pdf",
                )
                if not path:
                    return
                paths = [path]
            else:
                folder = filedialog.askdirectory(parent=dlg, title="เลือกโฟลเดอร์ที่จะบันทึก")
                if not folder:
                    return
                paths = [os.path.join(folder, f"{base_name}_{i+1}.pdf") for i in range(copies)]

            try:
                for path in paths:
                    export_history_result(ev, groups, path)
                dlg.destroy()
                messagebox.showinfo("บันทึกสำเร็จ", f"บันทึก PDF {copies} ชุด เรียบร้อย")
            except Exception as e:
                err_lbl.configure(text=f"ไม่สามารถสร้าง PDF ได้: {e}")

        self.primary_btn(btn_bar, "บันทึก PDF", save,
                         fontsize=self.fs(24), width=14).pack(side="left", padx=(0, 8))
        self.primary_btn(btn_bar, "ยกเลิก", dlg.destroy,
                         fontsize=self.fs(24), width=10).pack(side="left")
