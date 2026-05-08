import re as _re
import tkinter as tk
import platform

# ── Colors ───────────────────────────────────────────────────────────────────
BG_COLOR   = "#BFBFBF"   # medium gray background
CARD_COLOR = "#FFFFFF"   # white card surface
HEADER_BG  = "#474747"   # dark charcoal header
HDR_TEXT   = "#FFFFFF"   # white text on dark header
TEXT_COLOR = "#474747"   # dark text on light surfaces
BTN_BG     = "#FD9E50"   # orange button
BTN_ACTIVE = "#e08840"   # darker orange on hover
BTN_FG     = "#474747"   # dark text on orange (better contrast)
PASS_GREEN = "#16a34a"   # green
FAIL_RED   = "#dc2626"   # red
ENTRY_BG   = "#FFFFFF"   # white input
BORDER_CLR = "#474747"   # dark border / separator

# Reference card sizes at 1920×1080 — actual sizes computed per-screen relative to screen resolution
_REF_W   = 1920
_REF_H   = 1080
CARD_W  = 820   # fallback (overridden by self.CARD_W in each BaseScreen instance)
CARD_H  = 540
CARD_HL = 680


def thai_font(size: int = 14, weight: str = "normal") -> tuple:
    system = platform.system()
    if system == "Darwin":
        families = ["TH Sarabun New", "TH SarabunNew", "Krungthep", "Thonburi", "Arial Unicode MS"]
    elif system == "Windows":
        families = ["TH SarabunNew", "TH Sarabun New", "Leelawadee UI", "Leelawadee", "Browallia New", "Cordia New", "Tahoma"]
    else:
        families = ["Garuda", "Norasi", "DejaVu Sans"]

    try:
        import tkinter.font as tkfont
        available = set(tkfont.families())
        family = next((f for f in families if f in available), "TkDefaultFont")
    except Exception:
        family = "TkDefaultFont"

    bold = "bold" if weight == "bold" else "normal"
    return (family, size, bold)


def strip_markup(text: str) -> str:
    """Strip <u>...</u> markup tags, returning plain text."""
    return _re.sub(r'</?u>', '', text)


def rich_label(parent, text, font, fg, bg, padx=0, pady=0,
               anchor="nw", justify="left"):
    """
    Returns a tk.Label for plain text, or a read-only tk.Text widget when
    text contains <u>...</u> markup (renders underlined spans).
    """
    if "<u>" not in text:
        return tk.Label(parent, text=text, font=font, fg=fg, bg=bg,
                        anchor=anchor, justify=justify,
                        padx=padx, pady=pady)

    parts = _re.split(r'(<u>.*?</u>)', text, flags=_re.DOTALL)

    txt = tk.Text(parent, font=font, fg=fg, bg=bg,
                  relief="flat", bd=0, highlightthickness=0,
                  padx=padx, pady=pady, cursor="arrow",
                  wrap="word", width=1, height=1)
    txt.tag_configure("u", underline=True)

    for part in parts:
        if part.startswith("<u>") and part.endswith("</u>"):
            txt.insert("end", part[3:-4], "u")
        else:
            if part:
                txt.insert("end", part)

    txt.configure(state="disabled")

    def _fit_height():
        try:
            nlines = txt.count("1.0", "end", "displaylines")[0]
            txt.configure(height=max(1, nlines))
        except Exception:
            pass

    txt.bind("<Configure>", lambda _e: txt.after_idle(_fit_height))
    return txt


def bind_treeview_tooltip(tree):
    """แสดง tooltip ข้อความเต็มเมื่อ hover เหนือ cell ใน Treeview"""
    tip_window = [None]

    def _hide(_=None):
        if tip_window[0]:
            tip_window[0].destroy()
            tip_window[0] = None

    def _show(event):
        _hide()
        row = tree.identify_row(event.y)
        col = tree.identify_column(event.x)
        if not row or not col:
            return
        col_idx = int(col[1:]) - 1
        cols = tree["columns"]
        if col_idx < 0 or col_idx >= len(cols):
            return
        text = tree.set(row, cols[col_idx])
        if not text:
            return
        tip = tk.Toplevel(tree)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{event.x_root + 12}+{event.y_root + 16}")
        lbl = tk.Label(tip, text=text, font=thai_font(14),
                       bg="#ffffe0", fg="#000000", relief="solid", bd=1,
                       wraplength=700, justify="left", padx=8, pady=6)
        lbl.pack()
        tip_window[0] = tip

    tree.bind("<Motion>", _show)
    tree.bind("<Leave>", _hide)
    tree.bind("<ButtonPress>", _hide)


def _round_rect(canvas, x1, y1, x2, y2, r, **kw):
    """วาด rounded rectangle บน Canvas ด้วย smooth polygon."""
    pts = [x1+r, y1,  x2-r, y1,
           x2,   y1,  x2,   y1+r,
           x2,   y2-r, x2,  y2,
           x2-r, y2,  x1+r, y2,
           x1,   y2,  x1,   y2-r,
           x1,   y1+r, x1,  y1]
    canvas.create_polygon(pts, smooth=True, **kw)


class BaseScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app
        sw = app.winfo_screenwidth()
        sh = app.winfo_screenheight()
        # Keep original design sizes on all platforms (scaling caused distortion)
        self._s = 1.0
        _ = sw, sh  # screen size available if needed later
        self.CARD_W  = max(500, int(820 * self._s))
        self.CARD_H  = max(360, int(540 * self._s))
        self.CARD_HL = max(460, int(680 * self._s))

    def fs(self, n: int) -> int:
        """Scale a font size relative to screen resolution."""
        return max(8, int(n * self._s))

    def on_show(self, **kwargs):
        pass

    # ── helpers ──────────────────────────────────────────────────────────────

    def _bg(self, parent) -> str:
        try:
            return parent.cget("bg")
        except Exception:
            return CARD_COLOR

    def title_label(self, parent, text: str, size: int = 22):
        return tk.Label(
            parent, text=text,
            font=thai_font(size, "bold"),
            bg=self._bg(parent), fg=TEXT_COLOR,
        )

    def label(self, parent, text: str, size: int = 14,
              bold: bool = False, color: str = TEXT_COLOR,
              wraplength: int = 0, anchor: str = "w", justify: str = "left"):
        return tk.Label(
            parent, text=text,
            font=thai_font(size, "bold" if bold else "normal"),
            bg=self._bg(parent), fg=color,
            wraplength=wraplength, anchor=anchor, justify=justify,
        )

    def primary_btn(self, parent, text: str, command,
                    width: int = 14, height=None, fontsize: int = 13,
                    pady: int = None, padx: int = None,
                    btn_bg: str = None, btn_fg: str = None, btn_active: str = None):
        _bg     = btn_bg     or BTN_BG
        _fg     = btn_fg     or BTN_FG
        _active = btn_active or BTN_ACTIVE

        _pady = pady if pady is not None else max(8, fontsize // 2)
        _padx = padx if padx is not None else max(14, fontsize)

        # wrapper frame ใช้เป็น 1px border
        wrapper = tk.Frame(parent, bg=_active, cursor="hand2")
        btn = tk.Label(
            wrapper, text=text,
            font=thai_font(fontsize),
            bg=_bg, fg=_fg,
            relief="flat",
            highlightthickness=0,
            padx=_padx,
            pady=_pady,
            width=width,
            justify="center",
            cursor="hand2",
        )
        btn.pack(padx=1, pady=1)

        for widget in (wrapper, btn):
            widget.bind("<ButtonRelease-1>", lambda _: command())
            widget.bind("<Enter>",           lambda _: btn.configure(bg=_active))
            widget.bind("<Leave>",           lambda _: btn.configure(bg=_bg))
        return wrapper

    def grey_btn(self, parent, text: str, command, width: int = 14, height=None,
                 fontsize: int = 13, pady: int = None, padx: int = None):
        """ปุ่มสีเทา (#BFBFBF) สำหรับ action รอง"""
        return self.primary_btn(parent, text, command, width, fontsize=fontsize,
                                pady=pady, padx=padx,
                                btn_bg="#BFBFBF", btn_fg="#474747", btn_active="#a8a8a8")

    def back_btn(self, parent, text: str, command, width: int = 14, height=None,
                 fontsize: int = 13, pady: int = None, padx: int = None):
        """ปุ่มย้อนกลับ สี #BFBFBF"""
        return self.primary_btn(parent, text, command, width, fontsize=fontsize,
                                pady=pady, padx=padx,
                                btn_bg="#EEEEEE", btn_fg="#474747", btn_active="#c4c4c4")

    def dark_btn(self, parent, text: str, command, width: int = 14, height=None,
                 fontsize: int = 13, pady: int = None, padx: int = None):
        """ปุ่มสีเข้ม (#474747 + ข้อความขาว) สำหรับ action หลักในหน้าคำถาม"""
        return self.primary_btn(parent, text, command, width, fontsize=fontsize,
                                pady=pady, padx=padx,
                                btn_bg="#474747", btn_fg="#FFFFFF", btn_active="#5a5a5a")

    def rounded_card(self, parent, width: int, height: int, radius: int = 20):
        """Card ขอบมน — คืน (canvas, inner_frame)"""
        cvs = tk.Canvas(parent, width=width, height=height,
                        bg=self._bg(parent), highlightthickness=0)
        _round_rect(cvs, 0, 0, width, height, radius,
                    fill=CARD_COLOR, outline=BORDER_CLR)
        # inset เพื่อให้มุม Frame อยู่ภายในส่วนโค้ง
        inset = max(1, int(radius * 0.30) + 1)
        inner = tk.Frame(cvs, bg=CARD_COLOR, highlightthickness=0)
        cvs.create_window(width // 2, height // 2, window=inner, anchor="center",
                          width=width - 2 * inset, height=height - 2 * inset)
        return cvs, inner

    def confirm_dialog(self, title: str, message: str,
                       yes_text: str = "ใช่", no_text: str = "ยกเลิก") -> bool:
        """Custom confirm dialog — ปุ่ม Yes สีน้ำเงิน, คืน True/False"""
        result = [False]

        dlg = tk.Toplevel(self.app)
        dlg.title(title)
        dlg.configure(bg=CARD_COLOR)
        dlg.resizable(False, False)
        dlg.transient(self.app)
        dlg.grab_set()

        w, h = int(420 * self._s), int(180 * self._s)
        px = self.app.winfo_x() + self.app.winfo_width()  // 2 - w // 2
        py = self.app.winfo_y() + self.app.winfo_height() // 2 - h // 2
        dlg.geometry(f"{w}x{h}+{px}+{py}")

        tk.Label(dlg, text=message, font=thai_font(self.fs(22)),
                 bg=CARD_COLOR, fg=TEXT_COLOR,
                 wraplength=380, justify="center").pack(expand=True, pady=(20, 10))

        btn_bar = tk.Frame(dlg, bg=CARD_COLOR)
        btn_bar.pack(fill="x", padx=24, pady=(0, 16))

        def _yes():
            result[0] = True
            dlg.destroy()

        self.primary_btn(btn_bar, yes_text, _yes, fontsize=self.fs(22), width=10).pack(side="left", padx=(0, 8))
        self.grey_btn(btn_bar, no_text, dlg.destroy, fontsize=self.fs(22), width=10).pack(side="left")

        dlg.wait_window()
        return result[0]

    def card(self, parent, **kwargs):
        return tk.Frame(
            parent, bg=CARD_COLOR,
            relief="flat",
            highlightbackground=BORDER_CLR,
            highlightthickness=1,
            **kwargs,
        )

    def card_header(self, card, text: str, bg: str = HEADER_BG, size: int = 12,
                    fg: str = HDR_TEXT):
        hdr = tk.Canvas(card, height=max(31, size + 18), bg=bg, highlightthickness=0)
        hdr.pack(fill="x", side="top")
        h = max(30, size + 17)
        hdr.bind("<Configure>", lambda e: (
            hdr.delete("all"),
            hdr.create_rectangle(0, 0, e.width, h, fill=bg, outline=""),
            hdr.create_text(16, h // 2, text=text, font=thai_font(size, "bold"), fill=fg, anchor="w"),
        ))
        return hdr

    def entry(self, parent, width: int = 36):
        return tk.Entry(
            parent, font=thai_font(13),
            bg=ENTRY_BG, fg=TEXT_COLOR,
            relief="sunken", bd=2,
            width=width,
        )
