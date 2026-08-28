import os
import platform
import subprocess
import tempfile
import tkinter as tk
from tkinter import ttk
from screens.base import (
    BaseScreen, BG_COLOR, CARD_COLOR, TEXT_COLOR, BORDER_CLR,
    PASS_GREEN, FAIL_RED, thai_font, HEADER_BG, HDR_TEXT, count_fc,
)
from config import TEST_CONFIG


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


# สีสำหรับผลเปรียบเทียบ
CLR_SAME     = "#16a34a"   # เท่าเดิม  – green
CLR_DEGRADED = "#dc2626"   # ลดลง     – red
CLR_DRIFT    = "#d97706"   # คลาดเคลื่อน – amber
CLR_NO_ANS   = "#94a3b8"   # ไม่มีข้อมูล – slate

ALT_ROW      = "#f5f5f5"   # สีแถวสลับ (ขาวอมเทาอ่อน)

_HEADS   = ["หัวข้อประเมิน", "Baseline", "ครั้งนี้",
            "ผลการเปรียบเทียบ", "คำอธิบายเพิ่มเติมจากการเปรียบเทียบ"]
_WEIGHTS      = [3, 1, 1, 2, 3]   # ratio 3:1:1:2:3 (all columns weight-based)
_WEIGHT_TOTAL = 10
_ANCHORS = ["w", "center", "center", "w", "w"]

_TAG_COLOR = {
    "same":     CLR_SAME,
    "degraded": CLR_DEGRADED,
    "drift":    CLR_DRIFT,
    "no_ans":   CLR_NO_ANS,
}


class ComparisonScreen(BaseScreen):
    """เปรียบเทียบผลการประเมินปัจจุบัน (หรือ history) กับครั้งก่อนหน้า"""

    def __init__(self, parent, app):
        super().__init__(parent, app)

        self.card_header(self, "เปรียบเทียบกับครั้งก่อนหน้า", bg=HEADER_BG, fg=HDR_TEXT, size=self.fs(26))

        # ── header labels ─────────────────────────────────────────────────
        meta_bar = tk.Frame(self, bg=BG_COLOR)
        meta_bar.pack(fill="x", padx=24, pady=(8, 2))

        self.current_lbl = tk.Label(meta_bar, text="", font=thai_font(self.fs(26)),
                                    bg=BG_COLOR, fg="#000000")
        self.current_lbl.pack(side="left")

        self.baseline_lbl = tk.Label(meta_bar, text="", font=thai_font(self.fs(26)),
                                     bg=BG_COLOR, fg="#000000")
        self.baseline_lbl.pack(side="right")

        # ── table container ───────────────────────────────────────────────
        tbl = tk.Frame(self, bg=BG_COLOR)
        tbl.pack(fill="both", expand=True, padx=24, pady=(4, 12))

        # column header row (outside canvas — synced via _on_canvas_resize)
        head_bar = tk.Frame(tbl, bg=BG_COLOR)
        head_bar.pack(fill="x")
        self._head_row = tk.Frame(head_bar, bg="#ffffff")
        self._head_row.pack(fill="x")
        for i, wt in enumerate(_WEIGHTS):
            self._head_row.columnconfigure(i, weight=wt)
        self._head_labels = []
        for i, (text, anchor) in enumerate(zip(_HEADS, _ANCHORS)):
            lbl = tk.Label(self._head_row, text=text,
                           font=thai_font(self.fs(26), "bold"),
                           fg=TEXT_COLOR, bg="#ffffff",
                           anchor=anchor, padx=10, pady=10,
                           wraplength=200, justify="left")
            lbl.grid(row=0, column=i, sticky="nsew")
            self._head_labels.append(lbl)

        def _on_head_resize(e, lbls=self._head_labels):
            if e.width < 100:
                return
            for i, lbl in enumerate(lbls):
                col_w = e.width * _WEIGHTS[i] // _WEIGHT_TOTAL
                lbl.configure(wraplength=max(40, col_w - 20))
        self._head_row.bind("<Configure>", _on_head_resize)

        tk.Frame(tbl, bg=BORDER_CLR, height=2).pack(fill="x")

        # scrollable body
        body_outer = tk.Frame(tbl, bg=BG_COLOR)
        body_outer.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(body_outer, bg=CARD_COLOR, highlightthickness=0)
        vbar = ttk.Scrollbar(body_outer, orient="vertical",
                             command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vbar.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")

        self._body = tk.Frame(self._canvas, bg=CARD_COLOR)
        self._win  = self._canvas.create_window((0, 0), window=self._body,
                                                anchor="nw")

        self._body.bind("<Configure>",
                        lambda _: self._canvas.configure(
                            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", self._on_canvas_resize)
        self._canvas.bind("<MouseWheel>",
                          lambda e: self._canvas.yview_scroll(
                              -1 if e.delta > 0 else 1, "units"))

        self._rows_data: list[dict] = []

        # ── bottom ────────────────────────────────────────────────────────
        btn_bar = tk.Frame(self, bg=BG_COLOR)
        btn_bar.pack(side="bottom", fill="x", padx=20, pady=12)
        self.primary_btn(btn_bar, "ดาวน์โหลด PDF",
                         self._export_pdf, fontsize=self.fs(26), width=16).pack(side="left", padx=4)
        self.primary_btn(btn_bar, "พิมพ์",
                         self._print_pdf, fontsize=self.fs(26), width=10).pack(side="left", padx=4)
        self.back_btn(btn_bar, "กลับ", self._back,
                      fontsize=self.fs(26), width=12).pack(side="right", padx=4)

    # ── table helpers ─────────────────────────────────────────────────────

    def _build_row(self, parent, values, bg, fg, font, pady=6):
        """col สุดท้ายใช้ Text(wrap=word) เพื่อไม่ตัดกลางคำไทย"""
        row = tk.Frame(parent, bg=bg)
        row.pack(fill="x")
        for i, wt in enumerate(_WEIGHTS):
            row.columnconfigure(i, weight=wt)

        labels = []
        for i, (text, anchor) in enumerate(zip(values, _ANCHORS)):
            if anchor == "w":  # left-aligned cols → Text(wrap=word) ไม่ตัดกลางคำไทย
                cell = tk.Frame(row, bg=bg)
                cell.grid(row=0, column=i, sticky="nsew")
                txt = tk.Text(cell, font=font, fg=fg, bg=bg,
                              wrap="word", padx=10, pady=pady,
                              relief="flat", borderwidth=0,
                              highlightthickness=0, cursor="arrow",
                              width=1, height=1, state="normal")
                txt.tag_configure("c", foreground=fg)
                txt.insert("1.0", text, "c")
                txt.configure(state="disabled")
                txt.pack(fill="x")
                txt.bind("<MouseWheel>",
                         lambda e: self._canvas.yview_scroll(
                             -1 if e.delta > 0 else 1, "units"))
                _lh = [0]
                def _refit(_, w=txt, lh=_lh):
                    w.update_idletasks()
                    try:
                        h = max(1, w.count("1.0", "end", "displaylines")[0])
                    except Exception:
                        h = 1
                    if h != lh[0]:
                        lh[0] = h
                        w.configure(height=h)
                cell.bind("<Configure>", _refit)
                labels.append(txt)
            else:  # centered cols (Baseline, ครั้งนี้) → Label ชิดบน
                lbl = tk.Label(row, text=text, font=font, fg=fg, bg=bg,
                               anchor="n", padx=10, pady=pady,
                               wraplength=200, justify="center")
                lbl.grid(row=0, column=i, sticky="nsew")
                labels.append(lbl)

        def _on_resize(e, r=row, lbls=labels):
            if e.width < 100:
                return
            total = e.width
            for i, wt in enumerate(_WEIGHTS):
                col_w = total * wt // _WEIGHT_TOTAL
                wgt = 1 if i == len(_WEIGHTS) - 1 else 0
                r.columnconfigure(i, minsize=col_w, weight=wgt)
            for i, lbl in enumerate(lbls):
                if isinstance(lbl, tk.Label):
                    col_w = total * _WEIGHTS[i] // _WEIGHT_TOTAL
                    lbl.configure(wraplength=max(20, col_w - 20))
        row.bind("<Configure>", _on_resize)

        return labels[-1]

    def _on_canvas_resize(self, e):
        canvas_w = e.width
        self._canvas.itemconfig(self._win, width=canvas_w)
        if canvas_w < 100:
            return
        # sync header column widths to exactly match canvas body columns
        for i, wt in enumerate(_WEIGHTS):
            col_w = canvas_w * wt // _WEIGHT_TOTAL
            w = 1 if i == len(_WEIGHTS) - 1 else 0
            self._head_row.columnconfigure(i, minsize=col_w, weight=w)
        for i, lbl in enumerate(self._head_labels):
            col_w = canvas_w * _WEIGHTS[i] // _WEIGHT_TOTAL
            lbl.configure(wraplength=max(40, col_w - 20))

    def _clear(self):
        for w in self._body.winfo_children():
            w.destroy()
        self._rows_data.clear()
        self._canvas.yview_moveto(0)

    # ── on_show ───────────────────────────────────────────────────────────

    def on_show(self, **_):
        session  = self.app.session
        baseline = session.get("compare_baseline")
        current  = session.get("compare_current") or self._session_as_eval(session)

        if not baseline or not current:
            return

        import database as _db
        def _rank(ev):
            eid = ev.get("id")
            if not eid:
                return "-"
            return _db.get_eval_rank(ev.get("screen_type", ""), ev.get("period", ""), eid)
            
        def _format_dt(dt_str):
            if not dt_str: return ""
            try:
                import datetime
                dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                thai_year = dt_obj.year + 543
                return f"{dt_obj.day:02d}/{dt_obj.month:02d}/{thai_year} {dt_obj.strftime('%H:%M:%S')}"
            except Exception:
                return dt_str

        self.current_lbl.configure(
            text=f"ครั้งที่ {_rank(current)} : {current.get('hospital_name','')}  {current.get('evaluator_name','')}  {_format_dt(current.get('eval_datetime',''))}"
        )
        self.baseline_lbl.configure(
            text=f"Baseline (ครั้งที่ {_rank(baseline)}): {baseline.get('hospital_name','')}  {baseline.get('evaluator_name','')}  {_format_dt(baseline.get('eval_datetime',''))}"
        )

        screen_type = current.get("screen_type") or baseline.get("screen_type", "")
        period      = current.get("period")      or baseline.get("period", "")
        groups = TEST_CONFIG.get(screen_type, {}).get(period, [])

        cur_answers  = current.get("answers",  {})
        base_answers = baseline.get("answers", {})

        self._clear()
        row_idx = 0

        for group in groups:
            # group header spans full width
            g_row = tk.Frame(self._body, bg="#BFBFBF")
            g_row.pack(fill="x")
            g_lbl = tk.Label(g_row, text=group["group_title"],
                             font=thai_font(26, "bold"), fg=TEXT_COLOR,
                             bg="#BFBFBF", anchor="w", padx=10, pady=10,
                             wraplength=1, justify="left")
            g_lbl.pack(fill="x")
            g_row.bind("<Configure>",
                       lambda e, l=g_lbl: l.configure(wraplength=max(20, e.width - 20)))
            self._rows_data.append({"is_group": True, "title": group["group_title"]})

            for item in group["items"]:
                iid   = item["item_id"]
                b_ans = base_answers.get(iid)
                c_ans = cur_answers.get(iid)

                b_text = _ans_text(b_ans, item)
                c_text = _ans_text(c_ans, item)
                result_text, tag, description = _compare_result(item, b_ans, c_ans)

                fg     = _TAG_COLOR.get(tag, TEXT_COLOR)
                row_bg = CARD_COLOR if row_idx % 2 == 0 else ALT_ROW
                row_idx += 1

                display_title = item.get("criteria_title", item["title"])
                self._build_row(
                    self._body,
                    [f"  {display_title}", b_text, c_text, result_text, description],
                    row_bg, fg, thai_font(26), pady=10,
                )
                self._rows_data.append({
                    "is_group":    False,
                    "title":       f"  {display_title}",
                    "b_text":      b_text,
                    "c_text":      c_text,
                    "result_text": result_text,
                    "description": description,
                    "tag":         tag,
                })

        self.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._canvas.yview_moveto(0)

    # ── helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _session_as_eval(session: dict) -> dict:
        return {
            "hospital_name": session.get("hospital_name", ""),
            "eval_datetime": session.get("eval_datetime", ""),
            "screen_type":   session.get("screen_type", ""),
            "period":        session.get("period", ""),
            "answers":       session.get("answers", {}),
        }

    @staticmethod
    def _with_rank(ev: dict) -> dict:
        """คืน copy ของ ev พร้อม key 'rank' ที่คำนวณจาก database"""
        import database as _db
        ev = dict(ev)
        eid = ev.get("id")
        if eid:
            ev["rank"] = _db.get_eval_rank(ev.get("screen_type", ""), ev.get("period", ""), eid)
        return ev

    def _print_pdf(self):
        from tkinter import messagebox
        from reports.pdf_export import export_comparison
        session  = self.app.session
        baseline = session.get("compare_baseline")
        current  = session.get("compare_current") or ComparisonScreen._session_as_eval(session)
        if not baseline or not current or not self._rows_data:
            return
        if not messagebox.askyesno("ยืนยันการพิมพ์", "ต้องการพิมพ์ผลการเปรียบเทียบนี้ ใช่หรือไม่?"):
            return
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                tmp = f.name
            export_comparison(self._with_rank(current), self._with_rank(baseline), self._rows_data, tmp)
            _send_to_printer(tmp)
            messagebox.showinfo("ส่งพิมพ์สำเร็จ", "ส่งรายการพิมพ์เรียบร้อยแล้ว")
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถพิมพ์ได้\n{e}")

    def _export_pdf(self):
        from tkinter import filedialog, messagebox
        from reports.pdf_export import export_comparison
        session  = self.app.session
        baseline = session.get("compare_baseline")
        current  = session.get("compare_current") or ComparisonScreen._session_as_eval(session)
        if not baseline or not current or not self._rows_data:
            return
        default_name = f"เปรียบเทียบ_{current.get('hospital_name','')}_{current.get('eval_datetime','')}.pdf".replace(" ", "_").replace(":", "-")
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=default_name,
        )
        if not path:
            return
        try:
            export_comparison(self._with_rank(current), self._with_rank(baseline), self._rows_data, path)
            messagebox.showinfo("บันทึกสำเร็จ", f"บันทึก PDF เรียบร้อย\n{path}")
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถสร้าง PDF ได้\n{e}")

    def _back(self):
        session = self.app.session
        if session.get("eval_id"):
            self.app.show("after_save")
        elif session.get("compare_current"):
            self.app.show("history_result")
        else:
            self.app.show("home")


# ── helper functions ──────────────────────────────────────────────────────────

def _ans_text(ans, item: dict = None) -> str:
    if ans is None:
        return "ไม่มีข้อมูล"
    if ans["passed"]:
        return "ผ่าน"
    fc = ans.get("failed_channels", [])
    if fc:
        item = item or {}
        if item.get("question_type") == "yes_no_channels_text":
            return f"ไม่ผ่าน ({count_fc(fc)} ภาพ)"
        ch_lbl = item.get("channel_label", "ช่อง")
        return f"ไม่ผ่าน ({count_fc(fc)} {ch_lbl})"
    return "ไม่ผ่าน"


def _compare_result(item: dict, b_ans, c_ans) -> tuple[str, str, str]:
    """คืน (ผลเปรียบเทียบ, tag, คำอธิบายเพิ่มเติม) ตามตาราง Excel"""
    if b_ans is None or c_ans is None:
        return "ไม่มีข้อมูล", "no_ans", "-"

    b_pass = b_ans["passed"]
    c_pass = c_ans["passed"]
    qtype  = item.get("question_type", "yes_no")
    drift  = item.get("cmp_drift", "A")

    # ทั้งคู่ผ่าน
    if b_pass and c_pass:
        desc = "ผลที่ได้จากการทดสอบ ครั้งนี้ และผลที่ได้จาก baseline ผ่านเกณฑ์ทั้งคู่"
        return "คุณภาพของหน้าจอเท่าเดิม", "same", desc

    # baseline ผ่าน ปัจจุบันไม่ผ่าน
    if b_pass and not c_pass:
        desc = "ผลที่ได้จากการทดสอบ ครั้งนี้ ไม่ผ่านเกณฑ์และผลที่ได้จาก baseline ผ่านเกณฑ์"
        return "คุณภาพของหน้าจอลดลง", "degraded", desc

    # baseline ไม่ผ่าน ปัจจุบันผ่าน
    if not b_pass and c_pass:
        desc = "ผลที่ได้จากการทดสอบ ครั้งนี้ ผ่านเกณฑ์และผลที่ได้จาก baseline ไม่ผ่านเกณฑ์"
        if drift == "A":
            return "ผลการทดสอบคลาดเคลื่อนอาจเกิดจากการเปลี่ยนผู้ประเมินหรือปัจจัยอื่นที่เกี่ยวข้อง", "drift", desc
        else:
            return "ผลการทดสอบคลาดเคลื่อนเนื่องมาจากมีการเปลี่ยนผู้ประเมินและปัจจัยที่เกี่ยวข้องอื่น ๆ", "drift", desc

    # ทั้งคู่ไม่ผ่าน
    if qtype == "yes_no":
        desc = "ผลการประเมินไม่ผ่านทั้งคู่"
        return "คุณภาพของหน้าจอเท่าเดิม", "same", desc

    # yes_no_channels / yes_no_channels_text — เปรียบเทียบจำนวนช่องที่ไม่ผ่าน
    b_fc = count_fc(b_ans.get("failed_channels", []))
    c_fc = count_fc(c_ans.get("failed_channels", []))
    base_desc = "ผลที่ได้จากการทดสอบ ครั้งนี้ และผลที่ได้จาก baseline ไม่ผ่านเกณฑ์"

    if qtype == "yes_no_channels_text":
        if c_fc > b_fc:
            desc = (f"{base_desc}แต่พบว่าจำนวนภาพที่มองเห็นไม่สม่ำเสมอใน ครั้งนี้ "
                    f"มากกว่า จำนวนภาพที่มองเห็นไม่สม่ำเสมอของ baseline")
            return "คุณภาพของหน้าจอลดลง", "degraded", desc
        elif c_fc == b_fc:
            desc = (f"{base_desc}แต่พบว่าจำนวนกลุ่มภาพที่มองเห็นได้ไม่สม่ำเสมอใน "
                    f"ครั้งนี้ และ baseline มีจำนวนเท่ากัน")
            return "คุณภาพของหน้าจอเท่าเดิม", "same", desc
        else:
            desc = (f"{base_desc}แต่พบว่าจำนวนภาพที่มองเห็นไม่สม่ำเสมอใน ครั้งนี้ "
                    f"น้อยกว่า จำนวนภาพที่มองเห็นไม่สม่ำเสมอของ baseline")
            if drift == "A":
                return "ผลการทดสอบคลาดเคลื่อนอาจเกิดจากการเปลี่ยนผู้ประเมินหรือปัจจัยอื่นที่เกี่ยวข้อง", "drift", desc
            else:
                return "ผลการทดสอบคลาดเคลื่อนเนื่องมาจากมีการเปลี่ยนผู้ประเมินและปัจจัยที่เกี่ยวข้องอื่น ๆ", "drift", desc
    else:
        # yes_no_channels
        if c_fc > b_fc:
            desc = (f"{base_desc} แต่พบว่าจำนวนกลุ่มเส้นคู่ที่มองเห็นใน ครั้งนี้ "
                    f"น้อยกว่า จำนวนกลุ่มเส้นคู่ของ baseline")
            return "คุณภาพของหน้าจอลดลง", "degraded", desc
        elif c_fc == b_fc:
            desc = (f"{base_desc} แต่พบว่าจำนวนกลุ่มเส้นคู่ที่มองเห็นใน ครั้งนี้ "
                    f"และ baseline มีจำนวนเท่ากัน")
            return "คุณภาพของหน้าจอเท่าเดิม", "same", desc
        else:
            desc = (f"{base_desc} แต่พบว่าจำนวนกลุ่มเส้นคู่ที่มองเห็นใน ครั้งนี้ "
                    f"มากกว่า จำนวนกลุ่มเส้นคู่ของ baseline")
            if drift == "A":
                return "ผลการทดสอบคลาดเคลื่อนอาจเกิดจากการเปลี่ยนผู้ประเมินหรือปัจจัยอื่นที่เกี่ยวข้อง", "drift", desc
            else:
                return "ผลการทดสอบคลาดเคลื่อนเนื่องมาจากมีการเปลี่ยนผู้ประเมินและปัจจัยที่เกี่ยวข้องอื่น ๆ", "drift", desc
