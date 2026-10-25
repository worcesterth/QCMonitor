import os
import tkinter as tk
from PIL import Image, ImageTk
from screens.base import (BaseScreen, CARD_COLOR, TEXT_COLOR, thai_font,
                          BTN_BG, BTN_ACTIVE, BTN_FG)

_DISPLAY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "display")

_TYPES = [
    {
        "key":   "diagnostic",
        "label": "หน้าจอชนิดใช้วินิจฉัยทางการแพทย์\n(Diagnostic display)",
        "img":   "Diagnosis displays.png",
        "desc":  "เป็นหน้าจอสำหรับรังสีแพทย์ที่ใช้ในการอ่านภาพเอกซเรย์",
    },
    {
        "key":   "modality",
        "label": "หน้าจอชนิดใช้แสดงทางการแพทย์\n(Modality display)",
        "img":   "Modality displays.png",
        "desc":  "เป็นหน้าจอสำหรับนักรังสีเทคนิคใช้งานในการสร้างและประมวลผลภาพ",
    },
    {
        "key":   "clinic",
        "label": "หน้าจอตรวจทานทางการแพทย์\n(Clinical Review display)",
        "img":   "Clinical review displays.png",
        "desc":  "เป็นจอแสดงผลสำหรับแพทย์เฉพาะทางในแผนกต่าง ๆ ใช้งานเพื่อประกอบการตัดสินใจในการรักษา เช่น หน้าจอในห้องผ่าตัด",
    },
    {
        "key":   "ehr",
        "label": "หน้าจอสำหรับงานเวชระเบียน\n(Electronic Health Record)",
        "img":   "Electronic health record (EHR) displays.png",
        "desc":  "จอแสดงผลในห้องตรวจแพทย์ทั่วไปที่มีการดูภาพซ้ำหลังวินิจฉัยหลักไปแล้วรวมถึงหน้าจอสำหรับงานเวชระเบียนต่าง ๆ",
    },
]


def _load_thumb(path: str, height: int):
    try:
        img = Image.open(path).convert("RGB")
        w = int(img.width * height / img.height)
        img = img.resize((w, height), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


class SelectTypeScreen(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._thumbs = []

        card = self.card(self)
        card_h = max(560, int(820 * self._s))
        card.place(relx=0.5, rely=0.5, anchor="center", width=self.CARD_W, height=card_h)

        self.card_header(card, "โปรแกรมตรวจคุณภาพหน้าจอ", size=self.fs(24))

        body = tk.Frame(card, bg=CARD_COLOR)
        body.pack(fill="both", expand=True, padx=20, pady=(10, 0))

        self.title_label(body, "โปรดเลือกชนิดหน้าจอ", size=self.fs(36)).pack(pady=(10, 14))

        thumb_h = max(64, int(80 * self._s))
        small_font = thai_font(self.fs(20))  # used for desc_lbl

        for info in _TYPES:
            img_path = os.path.join(_DISPLAY_DIR, info["img"])
            thumb = _load_thumb(img_path, thumb_h)
            if thumb:
                self._thumbs.append(thumb)

            # ── orange bar ──────────────────────────────────────────────
            bar = tk.Frame(body, bg=BTN_BG, cursor="hand2")
            bar.pack(fill="x", pady=3)

            # image — flush left
            if thumb:
                img_lbl = tk.Label(bar, image=thumb, bg=BTN_BG)
                img_lbl.pack(side="left")

            # right side: title (top) + info link (bottom-right)
            right = tk.Frame(bar, bg=BTN_BG)
            right.pack(side="left", fill="both", expand=True)

            title_lbl = tk.Label(right, text=info["label"],
                                 font=thai_font(self.fs(30), "bold"),
                                 bg=BTN_BG, fg=BTN_FG,
                                 justify="left", anchor="w",
                                 padx=14, pady=4)
            title_lbl.pack(fill="x")

            desc_lbl = tk.Label(right, text=info["desc"],
                                font=small_font,
                                bg=BTN_BG, fg=BTN_FG,
                                justify="left", anchor="w",
                                padx=14, pady=(0, 6),
                                wraplength=1)
            desc_lbl.pack(fill="x")
            right.bind("<Configure>",
                       lambda e, l=desc_lbl: l.configure(wraplength=max(40, e.width - 20)))

            # click bar / image / title / desc → select type
            select_cmd = lambda k=info["key"]: self._select(k)
            for w in (bar, right, title_lbl, desc_lbl) + ((img_lbl,) if thumb else ()):
                w.bind("<Button-1>", lambda _, c=select_cmd: c())

            # hover
            hover_w = [bar, right, title_lbl, desc_lbl] + ([img_lbl] if thumb else [])
            def _enter(_, ws=hover_w):
                for w in ws: w.configure(bg=BTN_ACTIVE)
            def _leave(_, ws=hover_w):
                for w in ws: w.configure(bg=BTN_BG)
            for w in hover_w:
                w.bind("<Enter>", _enter)
                w.bind("<Leave>", _leave)

        bottom = tk.Frame(card, bg=CARD_COLOR)
        bottom.pack(side="bottom", fill="x", padx=16, pady=12)
        self.back_btn(bottom, "ย้อนกลับ", lambda: app.show("home"),
                      fontsize=self.fs(26), width=12).pack(side="right", padx=4)

    def _select(self, screen_type: str):
        self.app.session["screen_type"] = screen_type
        self.app.show("select_period")

