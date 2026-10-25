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


def _bind_click(widget, cmd):
    """Bind click recursively so the whole bar is clickable."""
    widget.bind("<Button-1>", lambda _: cmd())
    widget.configure(cursor="hand2")
    for child in widget.winfo_children():
        _bind_click(child, cmd)


class SelectTypeScreen(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._thumbs = []

        card = self.card(self)
        card_h = max(680, int(980 * self._s))
        card.place(relx=0.5, rely=0.5, anchor="center", width=self.CARD_W, height=card_h)

        self.card_header(card, "โปรแกรมตรวจคุณภาพหน้าจอ", size=self.fs(24))

        body = tk.Frame(card, bg=CARD_COLOR)
        body.pack(fill="both", expand=True, padx=20, pady=(10, 0))

        self.title_label(body, "โปรดเลือกชนิดหน้าจอ", size=self.fs(36)).pack(pady=(10, 14))

        thumb_h = max(74, int(94 * self._s))

        for info in _TYPES:
            img_path = os.path.join(_DISPLAY_DIR, info["img"])
            thumb = _load_thumb(img_path, thumb_h)
            if thumb:
                self._thumbs.append(thumb)

            outer = tk.Frame(body, bg=CARD_COLOR)
            outer.pack(fill="x", pady=5)

            # ── main bar (full-width orange, image + title + desc) ───────
            bar = tk.Frame(outer, bg=BTN_BG)
            bar.pack(fill="x")

            if thumb:
                tk.Label(bar, image=thumb, bg=BTN_BG,
                         padx=8, pady=8).pack(side="left")

            text_side = tk.Frame(bar, bg=BTN_BG)
            text_side.pack(side="left", fill="both", expand=True,
                           padx=(4, 10), pady=6)

            tk.Label(text_side, text=info["label"],
                     font=thai_font(self.fs(30), "bold"),
                     bg=BTN_BG, fg=BTN_FG,
                     justify="center", anchor="center").pack(fill="x")

            tk.Label(text_side, text=info["desc"],
                     font=thai_font(self.fs(22)),
                     bg=BTN_BG, fg=BTN_FG,
                     justify="center", anchor="center",
                     wraplength=1).pack(fill="x")

            _bind_click(bar, lambda k=info["key"]: self._select(k))

            # hover effect
            def _enter(_, w=bar): w.configure(bg=BTN_ACTIVE)
            def _leave(_, w=bar): w.configure(bg=BTN_BG)
            bar.bind("<Enter>", _enter)
            bar.bind("<Leave>", _leave)
            for child in bar.winfo_children():
                child.bind("<Enter>", _enter)
                child.bind("<Leave>", _leave)
                for grandchild in child.winfo_children():
                    grandchild.bind("<Enter>", _enter)
                    grandchild.bind("<Leave>", _leave)

            # auto-wrap description label when bar resizes
            desc_lbl = text_side.winfo_children()[-1]
            bar.bind("<Configure>",
                     lambda e, lbl=desc_lbl: lbl.configure(
                         wraplength=max(60, e.width - (thumb_h * 2) - 40)))

        bottom = tk.Frame(card, bg=CARD_COLOR)
        bottom.pack(side="bottom", fill="x", padx=16, pady=12)
        self.back_btn(bottom, "ย้อนกลับ", lambda: app.show("home"),
                      fontsize=self.fs(26), width=12).pack(side="right", padx=4)

    def _select(self, screen_type: str):
        self.app.session["screen_type"] = screen_type
        self.app.show("select_period")

