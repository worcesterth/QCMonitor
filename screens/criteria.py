import tkinter as tk
from tkinter import ttk
from screens.base import (
    BaseScreen, BG_COLOR, CARD_COLOR, TEXT_COLOR, BORDER_CLR, thai_font,
    rich_label,
)
from config import TEST_CONFIG, SCREEN_TYPES, PERIOD_LABELS

_COL_HEADS = ["หัวข้อและเกณฑ์การประเมิน",
              "วิธีการแก้ไขปัญหากรณีไม่ผ่านเกณฑ์การประเมิน"]
_PAD_X     = 12
_PAD_Y     = 10
_GROUP_BG  = "#c4c4c4"
_ITEM_BG   = "#ffffff"


class CriteriaScreen(BaseScreen):
    """เกณฑ์และวิธีการแก้ไขปัญหา"""

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # ── title ─────────────────────────────────────────────────────────
        self.card_header(self, "เกณฑ์และวิธีการแก้ไขปัญหา", size=24)


        # ── filter bar (ซ่อนได้) ──────────────────────────────────────────
        self._filter_bar = tk.Frame(self, bg=BG_COLOR)
        self._filter_bar.pack(fill="x", padx=20, pady=(8, 4))
        tk.Label(self._filter_bar, text="ชนิดหน้าจอ:", font=thai_font(26),
                 bg=BG_COLOR, fg=TEXT_COLOR).pack(side="left")
        btn_f = tk.Frame(self._filter_bar, bg=BG_COLOR)
        btn_f.pack(side="left", padx=8)
        for key, val in SCREEN_TYPES.items():
            label = val.split("(")[0].strip()
            self.primary_btn(btn_f, label,
                             command=lambda k=key: self._populate(k, ""),
                             fontsize=26, width=12).pack(side="left", padx=2)

        # ── scrollable body ───────────────────────────────────────────────
        body_outer = tk.Frame(self, bg=BG_COLOR)
        body_outer.pack(fill="both", expand=True, padx=24, pady=(4, 12))

        self._canvas = tk.Canvas(body_outer, bg=_ITEM_BG, highlightthickness=0)
        vbar = ttk.Scrollbar(body_outer, orient="vertical",
                             command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vbar.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")

        self._body = tk.Frame(self._canvas, bg=_ITEM_BG)
        self._win  = self._canvas.create_window((0, 0), window=self._body,
                                                anchor="nw")
        self._body.bind("<Configure>",
                        lambda _: self._canvas.configure(
                            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
                          lambda e: self._canvas.itemconfig(
                              self._win, width=e.width))
        self._canvas.bind("<MouseWheel>",
                          lambda e: self._canvas.yview_scroll(
                              -1 if e.delta > 0 else 1, "units"))

        # ── bottom bar ────────────────────────────────────────────────────
        btn_bar = tk.Frame(self, bg=BG_COLOR)
        btn_bar.pack(side="bottom", fill="x", padx=20, pady=12)
        self.back_btn(btn_bar, "ย้อนกลับ", self._back,
                      fontsize=26, width=12).pack(side="right", padx=4)

    # ── on_show ───────────────────────────────────────────────────────────

    def on_show(self, **_):
        session     = self.app.session
        screen_type = session.get("screen_type", "diagnostic")
        period      = session.get("period", "")
        from_eval   = session.get("criteria_from", "")

        if from_eval:
            self._filter_bar.pack_forget()
            self._populate(screen_type, period)
        else:
            self._filter_bar.pack(fill="x", padx=20, pady=(8, 4))
            self._populate(screen_type, "")

    # ── build rows ────────────────────────────────────────────────────────

    def _populate(self, screen_type: str, period: str):
        for w in self._body.winfo_children():
            w.destroy()

        # ทุก row ใช้ grid เดียวกันใน self._body → column ตรงกันแน่นอน
        # col 0 = left (weight 1), col 1 = separator, col 2 = right (weight 2)
        self._body.columnconfigure(0, weight=1)
        self._body.columnconfigure(1, weight=0, minsize=1)
        self._body.columnconfigure(2, weight=1)

        r = [0]

        def _hsep(bg=BORDER_CLR):
            tk.Frame(self._body, bg=bg, height=1).grid(
                row=r[0], column=0, columnspan=3, sticky="ew")
            r[0] += 1

        def _cell(text, col, bg, font, colspan=1):
            w = rich_label(self._body, text=text, font=font, fg=TEXT_COLOR, bg=bg,
                           padx=_PAD_X, pady=_PAD_Y)
            w.grid(row=r[0], column=col, columnspan=colspan, sticky="nsew")
            if isinstance(w, tk.Label):
                w.configure(wraplength=1)
                w.bind("<Configure>",
                       lambda e, l=w: l.configure(
                           wraplength=max(60, e.width - _PAD_X * 2)))
            return w

        # ── header row ────────────────────────────────────────────────
        font_h = thai_font(26, "bold")
        _cell(_COL_HEADS[0], 0, "#FFFFFF", font_h)
        tk.Frame(self._body, bg=BORDER_CLR, width=1).grid(
            row=r[0], column=1, sticky="ns")
        _cell(_COL_HEADS[1], 2, "#FFFFFF", font_h)
        r[0] += 1
        _hsep()

        # ── content ───────────────────────────────────────────────────
        type_config = TEST_CONFIG.get(screen_type, {})
        for period_key, groups in type_config.items():
            if period and period_key != period:
                continue
            if not period:
                _cell(f"── {PERIOD_LABELS.get(period_key, period_key)} ──",
                      0, _GROUP_BG, thai_font(26, "bold"), colspan=3)
                r[0] += 1
                _hsep()
            for group in groups:
                _cell(group["group_title"], 0, _GROUP_BG,
                      thai_font(26, "bold"), colspan=3)
                r[0] += 1
                _hsep()
                for item in group["items"]:
                    criterion = item.get("pass_criterion", "")
                    if criterion:
                        # ใช้ frame ห่อ 2 label แยก เพื่อไม่ให้ tk.Text ทำ layout พัง
                        frame = tk.Frame(self._body, bg=_ITEM_BG)
                        frame.grid(row=r[0], column=0, sticky="nsew")
                        lbl_title = tk.Label(frame, text=item["title"],
                                             font=thai_font(26), fg=TEXT_COLOR,
                                             bg=_ITEM_BG, anchor="nw",
                                             justify="left", wraplength=1,
                                             padx=_PAD_X, pady=_PAD_Y)
                        lbl_title.pack(fill="x", anchor="w")
                        lbl_crit = rich_label(frame,
                                              text=f"<u>เกณฑ์:</u> {criterion}",
                                              font=thai_font(26), fg=TEXT_COLOR,
                                              bg=_ITEM_BG, padx=_PAD_X, pady=0)
                        lbl_crit.pack(fill="x", anchor="w")
                        def _bind(f, lt, lc):
                            def _resize(e):
                                w = max(60, e.width - _PAD_X * 2)
                                lt.configure(wraplength=w)
                                if isinstance(lc, tk.Label):
                                    lc.configure(wraplength=w)
                            f.bind("<Configure>", _resize)
                        _bind(frame, lbl_title, lbl_crit)
                    else:
                        _cell(item["title"], 0, _ITEM_BG, thai_font(26))
                    tk.Frame(self._body, bg=BORDER_CLR, width=1).grid(
                        row=r[0], column=1, sticky="ns")
                    _cell(item.get("fix_guide", ""), 2, _ITEM_BG, thai_font(26))
                    r[0] += 1
                    _hsep()

    # ── back ──────────────────────────────────────────────────────────────

    def _back(self):
        src = self.app.session.pop("criteria_from", "")
        if src == "after_save":
            self.app.show("after_save")
        elif self.app.session.get("eval_id"):
            self.app.show("results")
        else:
            self.app.show("home")
