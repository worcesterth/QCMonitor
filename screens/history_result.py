# -*- coding: utf-8 -*-
import os
import platform
import subprocess
import tempfile
import tkinter as tk
from tkinter import ttk
from screens.base import (
    BaseScreen, BG_COLOR, CARD_COLOR, TEXT_COLOR, BORDER_CLR,
    PASS_GREEN, FAIL_RED, thai_font,
)
from config import TEST_CONFIG

_HEADS      = ["หัวข้อการประเมิน", "ผลการประเมิน", "หมายเหตุ"]
_ANCHORS    = ["w", "center", "w"]
_WIDTHS_REF = [500, 140]   # คอลัมน์สุดท้าย (หมายเหตุ) flexible
ALT_ROW     = "#f5f5f5"


def _send_to_printer(path: str):
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


class HistoryResultScreen(BaseScreen):
    """Read-only version of results.py — shows a saved evaluation from history."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._widths = [int(w * self._s) for w in _WIDTHS_REF]

        self.card_header(self, "ผลการประเมิน (ประวัติ)", size=self.fs(24))

        # ── info bar ──────────────────────────────────────────────────────
        info_bar = tk.Frame(self, bg=BG_COLOR, bd=1, relief="solid")
        info_bar.pack(fill="x", padx=20, pady=(8, 4))
        self.info_lbl = tk.Label(info_bar, text="", font=thai_font(self.fs(26)),
                                  bg=BG_COLOR, fg=TEXT_COLOR)
        self.info_lbl.pack(side="left")

        # ── table container ───────────────────────────────────────────────
        tbl = tk.Frame(self, bg=BG_COLOR)
        tbl.pack(fill="both", expand=True, padx=24, pady=(4, 12))

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

        # ── bottom bar ────────────────────────────────────────────────────
        btn_bar = tk.Frame(self, bg=BG_COLOR)
        btn_bar.pack(side="bottom", fill="x", padx=20, pady=12)

        self.primary_btn(btn_bar, "เปรียบเทียบครั้งก่อนหน้า",
                         self._compare, fontsize=self.fs(26), width=22).pack(side="left", padx=4)
        self.primary_btn(btn_bar, "ดาวน์โหลด PDF",
                         self._export_pdf, fontsize=self.fs(26), width=16).pack(side="left", padx=4)
        self.primary_btn(btn_bar, "พิมพ์",
                         self._print_result, fontsize=self.fs(26), width=10).pack(side="left", padx=4)
        self.back_btn(btn_bar, "กลับ",
                      lambda: app.show("history"), fontsize=self.fs(26), width=14).pack(side="right", padx=4)

    # ── table helpers ─────────────────────────────────────────────────────

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

    # ── on_show ───────────────────────────────────────────────────────────

    def on_show(self, **_):
        ev = self.app.session.get("history_eval")
        if not ev:
            return

        import datetime
        import database as _db
        type_map   = {"diagnostic": "Diagnostic", "modality": "Modality", "clinic": "Clinical Review"}
        period_map = {"monthly": "รายเดือน", "quarterly": "ราย 3 เดือน", "annual": "ประจำปี"}
        stype  = type_map.get(ev.get("screen_type", ""), "")
        period = period_map.get(ev.get("period", ""), "")
        self._current_rank = _db.get_eval_rank(ev.get("screen_type", ""), ev.get("period", ""), ev["id"])
        rank = self._current_rank
        baseline_mark = "  ★ Baseline" if ev.get("is_baseline") else ""

        eval_dt_str = ev.get('eval_datetime', '')
        try:
            dt_obj = datetime.datetime.strptime(eval_dt_str, "%Y-%m-%d %H:%M:%S")
            display_date = f"{dt_obj.day:02d}/{dt_obj.month:02d}/{dt_obj.year + 543} {dt_obj.strftime('%H:%M:%S')}"
        except Exception:
            display_date = eval_dt_str

        self.info_lbl.configure(
            text=f"โรงพยาบาล: {ev.get('hospital_name','')}  |  ผู้ประเมิน: {ev.get('evaluator_name','')}  |  ครั้งที่ {rank}  |  ประเภท: {stype}  |  รอบ: {period}  |  วันที่: {display_date}{baseline_mark}"
        )

        self._clear()
        screen_type = ev.get("screen_type", "")
        period_key  = ev.get("period", "")
        groups  = TEST_CONFIG.get(screen_type, {}).get(period_key, [])
        answers = ev.get("answers", {})
        row_idx = 0

        for group in groups:
            self._build_row(self._body,
                            [group["group_title"], "", ""],
                            "#BFBFBF", TEXT_COLOR,
                            thai_font(self.fs(26), "bold"), pady=10)

            for item in group["items"]:
                item_id = item["item_id"]
                ans = answers.get(item_id)
                if ans:
                    result_text = "ผ่าน" if ans["passed"] else "ไม่ผ่าน"
                    fg = PASS_GREEN if ans["passed"] else FAIL_RED
                    notes = ans.get("notes", "")
                    if ans.get("failed_channels"):
                        fc = ans["failed_channels"]
                        ch_str = ", ".join(str(c) for c in fc)
                        if item.get("question_type") == "yes_no_channels_text":
                            notes = (f"จำนวนภาพที่ Pixel ไม่สม่ำเสมอ: {len(fc)} ช่อง\n"
                                     f"ค่า Pixel ของช่องที่ไม่เห็น: {ch_str}") + (f"  {notes}" if notes else "")
                        else:
                            notes = f"ค่า Pixel ของช่องที่ไม่เห็น: {ch_str}" + (f"  {notes}" if notes else "")
                else:
                    result_text = "ไม่ได้ตอบ"
                    fg = "#888888"
                    notes = ""

                row_bg = CARD_COLOR if row_idx % 2 == 0 else ALT_ROW
                row_idx += 1
                note_lbl = self._build_row(self._body,
                                           [f"  {item['title']}", result_text, notes],
                                           row_bg, fg, thai_font(self.fs(26)), pady=8)
                if note_lbl:
                    self._note_labels.append(note_lbl)

        self.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._canvas.yview_moveto(0)
        self.after(10, self._refresh_note_wrap)

    # ── actions ───────────────────────────────────────────────────────────

    def _print_result(self):
        from tkinter import messagebox
        from reports.pdf_export import export_history_result
        ev = self.app.session.get("history_eval")
        if not ev:
            return
        if not messagebox.askyesno("ยืนยันการพิมพ์", "ต้องการพิมพ์ผลการประเมินนี้ ใช่หรือไม่?"):
            return
        try:
            screen_type = ev.get("screen_type", "")
            period_key  = ev.get("period", "")
            groups = TEST_CONFIG.get(screen_type, {}).get(period_key, [])
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                tmp = f.name
            export_history_result(ev, groups, tmp, rank=getattr(self, "_current_rank", 0))
            _send_to_printer(tmp)
            messagebox.showinfo("ส่งพิมพ์สำเร็จ", "ส่งรายการพิมพ์เรียบร้อยแล้ว")
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถพิมพ์ได้\n{e}")

    def _export_pdf(self):
        from tkinter import filedialog, messagebox
        from reports.pdf_export import export_history_result
        ev = self.app.session.get("history_eval")
        if not ev:
            return
        screen_type = ev.get("screen_type", "")
        period_key  = ev.get("period", "")
        groups = TEST_CONFIG.get(screen_type, {}).get(period_key, [])
        default_name = f"ผลการประเมิน_{ev.get('hospital_name','')}_{ev.get('eval_datetime','')}.pdf".replace(" ", "_").replace(":", "-")
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=default_name,
        )
        if not path:
            return
        try:
            export_history_result(ev, groups, path, rank=getattr(self, "_current_rank", 0))
            messagebox.showinfo("บันทึกสำเร็จ", f"บันทึก PDF เรียบร้อย\n{path}")
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถสร้าง PDF ได้\n{e}")

    def _compare(self):
        from tkinter import messagebox
        import database
        import datetime
        from screens.base import CARD_COLOR, TEXT_COLOR, BORDER_CLR, thai_font, ENTRY_BG

        ev = self.app.session.get("history_eval")
        if not ev:
            return

        prev_evals = database.get_evaluations_before(
            ev.get("screen_type", ""), ev.get("period", ""),
            before_id=ev["id"],
        )
        if not prev_evals:
            messagebox.showinfo("เปรียบเทียบ", "นี่คือการประเมินครั้งแรก ยังไม่มีผลก่อนหน้าให้เปรียบเทียบ")
            return

        dlg = tk.Toplevel(self.app)
        dlg.title("เลือกรอบที่ต้องการเปรียบเทียบ")
        dlg.configure(bg=CARD_COLOR)
        dlg.resizable(False, False)
        dlg.transient(self.app)
        dlg.grab_set()

        w, h = int(680 * self._s), int(520 * self._s)
        px = self.app.winfo_x() + self.app.winfo_width()  // 2 - w // 2
        py = self.app.winfo_y() + self.app.winfo_height() // 2 - h // 2
        dlg.geometry(f"{w}x{h}+{px}+{py}")

        tk.Label(dlg, text="เลือกรอบที่ต้องการเทียบ Baseline",
                 font=thai_font(self.fs(26), "bold"), bg=CARD_COLOR,
                 fg=TEXT_COLOR).pack(anchor="w", padx=20, pady=(16, 6))
        tk.Frame(dlg, bg=BORDER_CLR, height=1).pack(fill="x", padx=20)

        lb_frame = tk.Frame(dlg, bg=CARD_COLOR)
        lb_frame.pack(fill="both", expand=True, padx=20, pady=10)

        sb = tk.Scrollbar(lb_frame, orient="vertical")
        lb = tk.Listbox(lb_frame, font=thai_font(self.fs(24)), yscrollcommand=sb.set,
                        bg=ENTRY_BG, fg=TEXT_COLOR, selectbackground="#3b9be8",
                        selectforeground="white", activestyle="none",
                        height=min(8, len(prev_evals)), relief="flat", bd=0)
        sb.configure(command=lb.yview)
        sb.pack(side="right", fill="y")
        lb.pack(side="left", fill="both", expand=True)

        for e in prev_evals:
            try:
                dt_obj = datetime.datetime.strptime(e['eval_datetime'], "%Y-%m-%d %H:%M:%S")
                disp_dt = f"{dt_obj.day:02d}/{dt_obj.month:02d}/{dt_obj.year + 543} {dt_obj.strftime('%H:%M:%S')}"
            except Exception:
                disp_dt = e['eval_datetime']
            lb.insert("end", f"ครั้งที่ {e['rank']}:  {disp_dt}  {e['evaluator_name']}")

        default_idx = len(prev_evals) - 1
        lb.selection_set(default_idx)
        lb.see(default_idx)

        err_lbl = tk.Label(dlg, text="", font=thai_font(self.fs(20)),
                           bg=CARD_COLOR, fg="#cc0000")
        err_lbl.pack(anchor="w", padx=20)

        btn_bar = tk.Frame(dlg, bg=CARD_COLOR)
        btn_bar.pack(fill="x", padx=20, pady=(4, 16))

        def confirm():
            sel = lb.curselection()
            if not sel:
                err_lbl.configure(text="กรุณาเลือกรอบที่ต้องการเทียบ")
                return
            chosen = prev_evals[sel[0]]
            baseline = database.get_evaluation(chosen["id"])
            if not baseline:
                err_lbl.configure(text="ไม่พบข้อมูลรอบที่เลือก")
                return
            dlg.destroy()
            self.app.session["compare_current"]  = ev
            self.app.session["compare_baseline"] = baseline
            self.app.show("comparison")

        self.primary_btn(btn_bar, "ยืนยัน", confirm,
                         fontsize=self.fs(24), width=12).pack(side="left", padx=(0, 8))
        self.primary_btn(btn_bar, "ยกเลิก", dlg.destroy,
                         fontsize=self.fs(24), width=12).pack(side="left")
