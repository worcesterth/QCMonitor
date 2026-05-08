import os
import re
import glob
import tkinter as tk
from PIL import Image, ImageTk

from screens.base import (
    BaseScreen, CARD_COLOR, TEXT_COLOR,
    ENTRY_BG, thai_font, FAIL_RED, _round_rect,
)

BTN_BG = "#333333"

PATTERN_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           "assets", "test_patterns")
FRAME_DELAY_MS = 80   # ความเร็วเล่น frame (ms)


class TestRunnerScreen(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._img_ref         = None
        self._frames          = []
        self._frame_idx       = 0
        self._after_id        = None
        self._slider_job      = None
        self._current_path    = None
        self._has_channels    = False
        self._has_text_ch     = False
        self._text_ch_var     = tk.StringVar()

        # ── รูปเต็มจอ ────────────────────────────────────────────────
        self.img_canvas = tk.Canvas(self, bg="#1a1a1a", highlightthickness=0)
        self.img_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.img_canvas.bind("<Configure>", self._on_canvas_resize)

        # ── control bar ด้านล่าง (multi-frame) ───────────────────────
        self.ctrl_bar = tk.Frame(self, bg="#111111")
        self._is_playing = False
        self._slider_var = tk.IntVar(value=0)

        ctrl_inner = tk.Frame(self.ctrl_bar, bg="#111111")
        ctrl_inner.pack(fill="x", padx=10, pady=4)

        self.playpause_btn = tk.Button(
            ctrl_inner, text="⏸ หยุด", font=thai_font(self.fs(16)),
            bg="#555555", fg="#000000", relief="raised", bd=2,
            activebackground="#777777", activeforeground="white",
            command=self._toggle_play, width=8,
        )
        self.playpause_btn.pack(side="left", padx=(0, 8))

        self.replay_bar_btn = tk.Button(
            ctrl_inner, text="เล่นซ้ำ", font=thai_font(self.fs(16)),
            bg="#555555", fg="#000000", relief="raised", bd=2,
            activebackground="#777777", activeforeground="white",
            command=self._replay, width=8,
        )
        self.replay_bar_btn.pack(side="left", padx=(0, 12))

        self.frame_counter = tk.Label(ctrl_inner, text="0 / 0",
                                      font=thai_font(self.fs(14)), bg="#111111", fg="#ffffff")
        self.frame_counter.pack(side="right", padx=(8, 0))

        self.slider = tk.Scale(
            ctrl_inner, orient="horizontal", variable=self._slider_var,
            from_=0, to=1, showvalue=False,
            bg="#111111", fg="white", troughcolor="#444444",
            highlightthickness=0, sliderrelief="flat",
            command=self._on_slider,
        )
        self.slider.pack(side="left", fill="x", expand=True)

        # ── overlay label ตอนเล่น frame ──────────────────────────────
        self.play_lbl = tk.Label(self, text="", font=thai_font(self.fs(14)),
                                 bg="#1a1a1a", fg="#cccccc")


        # ── Floating window ───────────────────────────────────────────
        self.card_win = tk.Toplevel(app)
        self.card_win.title("คำถามและการประเมิน")
        self.card_win.configure(bg=CARD_COLOR)
        self.card_win.protocol("WM_DELETE_WINDOW", lambda: None)
        self.card_win.resizable(True, True)
        self.card_win.minsize(int(600 * self._s), int(360 * self._s))
        self.card_win.withdraw()

        # ── แถบบนสุด: ชื่อกลุ่ม + badge ข้อ X/Y มุมขวาบน ────────────
        top_bar = tk.Frame(self.card_win, bg="#FFFFFF", height=int(46 * self._s))
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)

        _BW, _BH, _BR = int(110 * self._s), int(34 * self._s), int(11 * self._s)
        self._badge_cvs = tk.Canvas(top_bar, width=_BW, height=_BH,
                                    bg="#F4F4F4", highlightthickness=0)
        self._badge_cvs.pack(side="right", padx=10, pady=6)

        def _draw_badge(text: str):
            self._badge_cvs.delete("all")
            _round_rect(self._badge_cvs, 1, 1, _BW - 1, _BH - 1, _BR,
                        fill="#F4F4F4", outline="")
            self._badge_cvs.create_text(_BW // 2, _BH // 2, text=text,
                                        font=thai_font(self.fs(16), "bold"), fill="#000000")
        self._draw_badge = _draw_badge
        self._draw_badge("- / -")

        # ── body ───────────────────────────────────────────────────────
        body = tk.Frame(self.card_win, bg=CARD_COLOR)
        body.pack(fill="x", expand=False, padx=12, pady=8)

        self.item_lbl = tk.Text(
            body, font=thai_font(self.fs(26)),
            bg=CARD_COLOR, fg=TEXT_COLOR,
            relief="flat", bd=0, highlightthickness=0,
            wrap="word", width=1, height=1,
            cursor="arrow", state="disabled",
        )
        self.item_lbl.tag_configure("u", underline=True)
        self.item_lbl.pack(anchor="w", fill="x", pady=(0, 8))
        self.item_lbl.bind("<Configure>",
                           lambda _e: self.item_lbl.after_idle(self._fit_item_lbl_height))

        q_row = tk.Frame(body, bg=CARD_COLOR)
        q_row.pack(anchor="w", pady=(0, 6))

        self._answer_var = tk.StringVar(value="")
        self._warn_lbl = tk.Label(body, text="*กรุณาตอบคำถาม",
                                  font=thai_font(self.fs(16)), bg=CARD_COLOR, fg=FAIL_RED)

        for val, txt in [("pass", "ใช่"), ("fail", "ไม่ใช่")]:
            tk.Radiobutton(
                q_row, text=txt, variable=self._answer_var,
                value=val, font=thai_font(self.fs(26)),
                bg=CARD_COLOR, fg=TEXT_COLOR,
                activebackground=CARD_COLOR, selectcolor=CARD_COLOR,
                tristatevalue="none",
                command=self._on_answer,
            ).pack(side="left", padx=16)

        self.channels_outer = tk.Frame(body, bg=CARD_COLOR)
        self.channels_outer.pack(anchor="w", fill="x")
        self.ch_vars: list[tk.BooleanVar] = []

        self.note_row = tk.Frame(body, bg=CARD_COLOR)
        self.note_row.pack(fill="x", pady=(8, 0))
        tk.Label(self.note_row, text="หมายเหตุ (ถ้ามี):", font=thai_font(self.fs(22)),
                 bg="#F4F4F4", fg=TEXT_COLOR).pack(side="left")
        self.notes_var = tk.StringVar()
        tk.Entry(self.note_row, textvariable=self.notes_var,
                 font=thai_font(self.fs(22)), bg="#F4F4F4", fg=TEXT_COLOR,
                 relief="flat", bd=0, width=18).pack(side="left", padx=6)

        # ── ปุ่มล่าง ──────────────────────────────────────────────────
        btn_bar = tk.Frame(self.card_win, bg=CARD_COLOR)
        btn_bar.pack(fill="x", padx=12, pady=8)

        nav = tk.Frame(btn_bar, bg=CARD_COLOR)
        nav.pack(fill="x")
        self.next_btn   = self.primary_btn(nav, "ถัดไป",    self._next,   fontsize=self.fs(26), width=10,
                                           btn_bg="#AFAFAF", btn_active="#999999", btn_fg="#474747")
        self.prev_btn   = self.grey_btn(nav, "ก่อนหน้า", self._prev,   fontsize=self.fs(26), width=10)
        self.replay_btn = self.grey_btn(nav, "เล่นซ้ำ",  self._replay, fontsize=self.fs(26), width=10)
        self.next_btn.pack(side="right", padx=2)
        self.prev_btn.pack(side="right", padx=2)
        self.replay_btn.pack(side="left", padx=2)

    # ── Item label helpers ────────────────────────────────────────────────

    def _update_item_lbl(self, text: str):
        self.item_lbl.configure(state="normal")
        self.item_lbl.delete("1.0", "end")
        for part in re.split(r'(<u>.*?</u>)', text, flags=re.DOTALL):
            if part.startswith("<u>") and part.endswith("</u>"):
                self.item_lbl.insert("end", part[3:-4], "u")
            elif part:
                self.item_lbl.insert("end", part)
        self.item_lbl.configure(state="disabled")
        self.item_lbl.after_idle(self._fit_item_lbl_height)

    def _fit_item_lbl_height(self):
        try:
            nlines = self.item_lbl.count("1.0", "end", "displaylines")[0]
            self.item_lbl.configure(height=max(1, nlines))
        except Exception:
            pass

    # ── Window helpers ────────────────────────────────────────────────────

    def _show_card_win(self):
        self.card_win.deiconify()
        self.card_win.lift()

    def on_hide(self):
        self.card_win.withdraw()
        self._stop_playback()

    # ── Load ──────────────────────────────────────────────────────────────

    def on_show(self, **_):
        self._load_item()

    def _load_item(self):
        session = self.app.session
        items   = session.get("test_items", [])
        idx     = session.get("current_item_idx", 0)
        if not items:
            return

        item  = items[idx]
        total = len(items)

        criterion = item.get("pass_criterion", "")
        title     = item.get("title", "")
        display   = f"{title}: {criterion}" if criterion else title
        self._update_item_lbl(display)
        self.card_win.title(item.get("group_title_Q", item.get("group_title", "")))
        self._draw_badge(f"ข้อ {idx+1}/{total}")

        saved = session.get("answers", {}).get(item["item_id"], {})

        if item.get("question_type") == "yes_no_channels_text":
            def _do_load():
                self._finish_load_item(item, saved, idx)
            def _do_prev():
                if idx > 0:
                    session["current_item_idx"] = idx - 1
                    self._load_item()
            self._show_uniformity_intro(_do_load, _do_prev)
            return

        self._finish_load_item(item, saved, idx)

    def _finish_load_item(self, item, saved, idx):
        self._answer_var.set(saved.get("result", ""))
        self.notes_var.set(saved.get("notes", ""))
        self._warn_lbl.pack_forget()

        self._load_image(self._resolve_image(item))
        self._setup_channels(item, saved)
        self._fit_card_win()

        inner = self.prev_btn.winfo_children()
        if inner:
            inner[0].configure(fg="#aaaaaa" if idx == 0 else TEXT_COLOR)

    def _fit_card_win(self):
        self.card_win.update_idletasks()
        w = max(self.card_win.winfo_reqwidth(),  self.card_win.winfo_width())
        h = self.card_win.winfo_reqheight()
        x = self.card_win.winfo_x()
        y = self.card_win.winfo_y()
        self.card_win.geometry(f"{w}x{h}+{x}+{y}")

    def _show_uniformity_intro(self, on_next, on_prev):
        dlg = tk.Toplevel(self.app)
        dlg.title("สำหรับการประเมินในหัวข้อถัดไป")
        dlg.resizable(False, False)
        dlg.configure(bg=CARD_COLOR)
        dlg.transient(self.app)
        dlg.protocol("WM_DELETE_WINDOW", lambda: None)

        w, h = int(700 * self._s), int(520 * self._s)
        px = self.app.winfo_x() + self.app.winfo_width()  // 2 - w // 2
        py = self.app.winfo_y() + self.app.winfo_height() // 2 - h // 2
        dlg.geometry(f"{w}x{h}+{px}+{py}")
        dlg.update()
        dlg.grab_set()
        dlg.focus_force()

        tk.Label(dlg,
                 text="การประเมินด้านความสม่ำเสมอของค่า pixel (uniformity)",
                 font=thai_font(self.fs(24), "bold"), bg=CARD_COLOR, fg=TEXT_COLOR,
                 wraplength=int(660 * self._s), justify="left",
                 ).pack(anchor="w", padx=24, pady=(24, 10))

        body = (
            "สังเกตหาจุดที่ไม่สม่ำเสมอหรือจุดด่างในแต่ละระดับค่า pixel ที่แสดง "
            "ซึ่งภาพที่แสดงต่อไปนี้เป็นภาพที่มีระดับค่า pixel ตั้งแต่ 0-255 "
            "โปรดมองอย่างละเอียดแล้วทำการเลื่อนเมาส์ดูภาพตั้งแต่ภาพที่แสดงค่า pixel ตั้งแต่ 0 "
            "ถึงภาพที่แสดงค่า pixel เท่ากับ 255"
        )
        tk.Label(dlg, text=body, font=thai_font(self.fs(24)), bg=CARD_COLOR, fg=TEXT_COLOR,
                 wraplength=int(660 * self._s), justify="left",
                 ).pack(anchor="w", padx=24, pady=(0, 20))

        btn_bar = tk.Frame(dlg, bg=CARD_COLOR)
        btn_bar.pack(side="bottom", fill="x", padx=24, pady=16)

        def go_next():
            dlg.destroy()
            on_next()

        def go_prev():
            dlg.destroy()
            on_prev()

        self.primary_btn(btn_bar, "ถัดไป",    go_next, fontsize=self.fs(18), width=10).pack(side="right", padx=4)
        self.back_btn(btn_bar, "ก่อนหน้า", go_prev, fontsize=self.fs(18), width=10).pack(side="right", padx=4)

    def _resolve_image(self, item: dict) -> str:
        session     = self.app.session
        screen_type = session.get("screen_type", "diagnostic")
        period      = session.get("period", "monthly")

        type_map   = {"diagnostic": "diagnostic", "modality": "modality", "clinic": "clinical"}
        period_map = {"monthly": "m", "quarterly": "3m", "annual": "y"}

        t = type_map.get(screen_type, screen_type)
        p = period_map.get(period, period)
        n = item.get("image_index", 1)

        for ext in ("png", "TIFF", "tiff", "jpg", "jpeg"):
            fname = f"{t}_{p}_{n}.{ext}"
            if os.path.exists(os.path.join(PATTERN_DIR, fname)):
                return fname
        return item.get("image", "tg270_luminance.png")

    def _load_image(self, filename: str):
        self._stop_playback()
        path = os.path.join(PATTERN_DIR, filename)

        if os.path.isdir(path):
            files = sorted(
                glob.glob(os.path.join(path, "*.tif")) +
                glob.glob(os.path.join(path, "*.tiff")) +
                glob.glob(os.path.join(path, "*.png"))
            )
            if files:
                self._frames     = files
                self._frame_idx  = 0
                self._is_playing = True
                self.slider.configure(to=len(files) - 1)
                self._slider_var.set(0)
                self.frame_counter.configure(text=f"1 / {len(files)}")
                self.playpause_btn.configure(text="⏸ หยุด")
                self.ctrl_bar.place(relx=0, rely=1.0, relwidth=1,
                                    height=int(52 * self._s), anchor="sw")
                self.play_lbl.place(relx=0.5, rely=0.92, anchor="s")
                self.replay_btn.pack(side="left", padx=2)
                self._show_card_win()
                self._play_next_frame()
                return

        self._frames = []
        self.ctrl_bar.place_forget()
        self.play_lbl.place_forget()
        self.replay_btn.pack_forget()
        self._show_card_win()
        self._show_single(path)

    def _play_next_frame(self):
        if not self._is_playing:
            return
        if self._frame_idx >= len(self._frames):
            self._is_playing = False
            self.play_lbl.place_forget()
            self.playpause_btn.configure(text="▶ เล่น")
            self._show_card_win()
            return

        self._show_frame(self._frame_idx)
        self._frame_idx += 1
        self._after_id = self.after(FRAME_DELAY_MS, self._play_next_frame)

    def _show_frame(self, idx: int):
        total = len(self._frames)
        self._show_single(self._frames[idx])
        self.play_lbl.configure(text=f"{idx + 1} / {total}")
        self._slider_var.set(idx)
        self.frame_counter.configure(text=f"{idx + 1} / {total}")

    def _on_canvas_resize(self, *_):
        if self._current_path and not self._frames:
            self._show_single(self._current_path)

    def _show_single(self, path: str):
        self._current_path = path
        self.img_canvas.delete("all")
        if not os.path.exists(path):
            self.img_canvas.create_text(
                400, 300, text=f"ไม่พบ:\n{path}",
                fill="white", font=thai_font(self.fs(14)), justify="center",
            )
            return
        cw = self.img_canvas.winfo_width()  or self.app.winfo_width()  or 1280
        ch = self.img_canvas.winfo_height() or self.app.winfo_height() or 800
        img = Image.open(path).convert("RGB")
        img = img.resize((cw, ch), Image.BILINEAR)
        self._img_ref = ImageTk.PhotoImage(img)
        self.img_canvas.create_image(0, 0, anchor="nw", image=self._img_ref)

    def _stop_playback(self):
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None

    # ── Channels ─────────────────────────────────────────────────────────

    def _setup_channels(self, item, saved):
        for w in self.channels_outer.winfo_children():
            w.destroy()
        self.ch_vars.clear()

        qtype = item.get("question_type", "")

        if qtype == "yes_no_channels_text":
            self._has_channels = True
            self._has_text_ch  = True
            saved_text = " ".join(str(c) for c in saved.get("failed_channels", []))
            self._text_ch_var.set(saved_text)

            tk.Label(self.channels_outer,
                     text="ระบุค่าที่ไม่ผ่าน (0–255 คั่นด้วยช่องว่าง):",
                     font=thai_font(self.fs(22)), bg=CARD_COLOR, fg=TEXT_COLOR
                     ).grid(row=0, column=0, sticky="w", pady=(4, 2))
            tk.Entry(self.channels_outer, textvariable=self._text_ch_var,
                     font=thai_font(self.fs(22)), bg=ENTRY_BG, fg=TEXT_COLOR,
                     relief="sunken", bd=2, width=30
                     ).grid(row=1, column=0, sticky="w", padx=2, pady=(0, 4))
            self._show_channels(saved.get("result") == "fail")
            return

        if qtype != "yes_no_channels":
            self._has_channels = False
            self._has_text_ch  = False
            self._show_channels(False)
            return

        self._has_channels = True
        self._has_text_ch  = False
        total_ch   = item.get("total_channels", 18)
        saved_fail = saved.get("failed_channels", [])

        _row_ids = {"mod_lum_lines_3m", "clin_lum_lines_3m", "diag_lum_lines_3m"}
        _ch_label = "ระบุแถวที่มองไม่เห็น:" if item.get("item_id") in _row_ids else "ระบุช่องที่มองไม่เห็น:"
        tk.Label(self.channels_outer, text=_ch_label,
                 font=thai_font(self.fs(22)), bg=CARD_COLOR, fg=TEXT_COLOR
                 ).grid(row=0, column=0, columnspan=9, sticky="w", pady=(4, 2))

        cols = 9
        for i in range(total_ch):
            var = tk.BooleanVar(value=(i + 1) in saved_fail)
            tk.Checkbutton(
                self.channels_outer, text=str(i + 1),
                variable=var, font=thai_font(self.fs(20)),
                bg=CARD_COLOR, fg=TEXT_COLOR,
                activebackground=CARD_COLOR, selectcolor=ENTRY_BG,
            ).grid(row=1 + i // cols, column=i % cols, sticky="w", padx=2)
            self.ch_vars.append(var)

        self._show_channels(saved.get("result") == "fail")

    def _show_channels(self, show: bool):
        if show:
            self.channels_outer.pack_propagate(True)
            for w in self.channels_outer.winfo_children():
                w.grid()
        else:
            for w in self.channels_outer.winfo_children():
                w.grid_remove()
            self.channels_outer.configure(height=1)
            self.channels_outer.pack_propagate(False)
        self.card_win.after_idle(self._fit_card_win)

    # ── Answer / Nav ─────────────────────────────────────────────────────

    def _on_answer(self):
        self._warn_lbl.pack_forget()
        if self._has_channels:
            self._show_channels(self._answer_var.get() == "fail")
        self.card_win.after_idle(self._fit_card_win)

    def _save_current(self):
        session = self.app.session
        items   = session.get("test_items", [])
        idx     = session.get("current_item_idx", 0)
        if not items:
            return
        item = items[idx]
        ans  = self._answer_var.get()
        if not ans:
            return

        if self._has_text_ch:
            seen = set()
            failed_ch = []
            for part in self._text_ch_var.get().split():
                try:
                    v = int(part)
                    if 0 <= v <= 255 and v not in seen:
                        seen.add(v)
                        failed_ch.append(v)
                except ValueError:
                    pass
        else:
            failed_ch = [i + 1 for i, v in enumerate(self.ch_vars) if v.get()]
        session["answers"][item["item_id"]] = {
            "result":          ans,
            "passed":          ans == "pass",
            "notes":           self.notes_var.get().strip(),
            "failed_channels": failed_ch,
            "group_id":        item["group_id"],
            "group_title":     item["group_title"],
            "item_id":         item["item_id"],
            "item_title":      item["title"],
        }

    def _next(self):
        if not self._answer_var.get():
            self._warn_lbl.pack(anchor="w", pady=(0, 4))
            self._fit_card_win()
            return
        if self._has_channels and self._answer_var.get() == "fail":
            if self._has_text_ch:
                parts = [p for p in self._text_ch_var.get().split()
                         if p.isdigit() and 0 <= int(p) <= 255]
                if not parts:
                    self._warn_lbl.configure(text="*กรุณาระบุค่าที่ไม่ผ่านอย่างน้อย 1 ค่า (0–255)")
                    self._warn_lbl.pack(anchor="w", pady=(0, 4))
                    self._fit_card_win()
                    return
            else:
                if not any(v.get() for v in self.ch_vars):
                    self._warn_lbl.configure(text="*กรุณาเลือกช่องที่มองไม่เห็นอย่างน้อย 1 ช่อง")
                    self._warn_lbl.pack(anchor="w", pady=(0, 4))
                    self._fit_card_win()
                    return
        self._warn_lbl.configure(text="*กรุณาตอบคำถาม")
        self._save_current()
        session = self.app.session
        items   = session.get("test_items", [])
        idx     = session.get("current_item_idx", 0)
        if idx + 1 < len(items):
            session["current_item_idx"] = idx + 1
            self._load_item()
        else:
            self.card_win.withdraw()
            self.app.show("results")

    def _prev(self):
        self._stop_playback()
        self._save_current()
        session = self.app.session
        idx = session.get("current_item_idx", 0)
        if idx > 0:
            session["current_item_idx"] = idx - 1
            self._load_item()

    def _toggle_play(self):
        if not self._frames:
            return
        if self._is_playing:
            self._stop_playback()
            self._is_playing = False
            self.playpause_btn.configure(text="▶ เล่น")
        else:
            if self._frame_idx >= len(self._frames):
                self._frame_idx = 0
            self._is_playing = True
            self.playpause_btn.configure(text="⏸ หยุด")
            self.play_lbl.place(relx=0.5, rely=0.92, anchor="s")
            self._play_next_frame()

    def _on_slider(self, val):
        if not self._frames:
            return
        idx = int(float(val))
        idx = max(0, min(idx, len(self._frames) - 1))
        self._stop_playback()
        self._is_playing = False
        self.playpause_btn.configure(text="▶ เล่น")
        self._frame_idx = idx
        # debounce: render เมื่อหยุดลากแล้ว 40ms
        if self._slider_job:
            self.after_cancel(self._slider_job)
        self._slider_job = self.after(40, lambda i=idx: self._render_slider(i))

    def _render_slider(self, idx: int):
        self._slider_job = None
        self._show_frame(idx)
        if idx >= len(self._frames) - 1:
            self.play_lbl.place_forget()
            self._show_card_win()
        else:
            self.play_lbl.place(relx=0.5, rely=0.92, anchor="s")

    def _replay(self):
        if self._frames:
            self._stop_playback()
            self._frame_idx  = 0
            self._is_playing = True
            self.playpause_btn.configure(text="⏸ หยุด")
            self.play_lbl.place(relx=0.5, rely=0.92, anchor="s")
            self._play_next_frame()
