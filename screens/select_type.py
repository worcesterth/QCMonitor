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
        card_h = max(580, int(880 * self._s))
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
            outer.pack(fill="x", pady=4)

            # ── main bar (full-width orange, image + label) ──────────────
            bar = tk.Frame(outer, bg=BTN_BG)
            bar.pack(fill="x")

            if thumb:
                tk.Label(bar, image=thumb, bg=BTN_BG,
                         padx=8, pady=6).pack(side="left")

            tk.Label(bar, text=info["label"],
                     font=thai_font(self.fs(30), "bold"),
                     bg=BTN_BG, fg=BTN_FG,
                     justify="center", anchor="center",
                     padx=10, pady=8).pack(side="left", fill="both", expand=True)

            _bind_click(bar, lambda k=info["key"]: self._select(k))

            # hover effect
            def _enter(_, w=bar): w.configure(bg=BTN_ACTIVE)
            def _leave(_, w=bar): w.configure(bg=BTN_BG)
            bar.bind("<Enter>", _enter)
            bar.bind("<Leave>", _leave)
            for child in bar.winfo_children():
                child.bind("<Enter>", _enter)
                child.bind("<Leave>", _leave)

            # ── info link below bar ──────────────────────────────────────
            info_bar = tk.Frame(outer, bg=CARD_COLOR)
            info_bar.pack(fill="x")
            tk.Button(
                info_bar, text="ℹ  นิยาม  →",
                font=thai_font(self.fs(20)),
                bg=CARD_COLOR, fg="#4a90d9",
                relief="flat", bd=0, cursor="hand2",
                activeforeground="#1a5fa8", activebackground=CARD_COLOR,
                command=lambda i=info, ip=img_path: self._show_info(i, ip),
            ).pack(side="right", pady=(2, 0))

        bottom = tk.Frame(card, bg=CARD_COLOR)
        bottom.pack(side="bottom", fill="x", padx=16, pady=12)
        self.back_btn(bottom, "ย้อนกลับ", lambda: app.show("home"),
                      fontsize=self.fs(26), width=12).pack(side="right", padx=4)

    def _select(self, screen_type: str):
        self.app.session["screen_type"] = screen_type
        self.app.show("select_period")

    def _show_info(self, info: dict, img_path: str):
        popup = tk.Toplevel(self)
        popup.title(info["label"].replace("\n", " "))
        popup.configure(bg=CARD_COLOR)
        popup.resizable(False, False)
        popup.grab_set()

        try:
            img = Image.open(img_path).convert("RGB")
            pw = 420
            ph = int(img.height * pw / img.width)
            img = img.resize((pw, ph), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._thumbs.append(photo)
            tk.Label(popup, image=photo, bg=CARD_COLOR).pack(padx=20, pady=(16, 8))
        except Exception:
            pass

        tk.Label(popup, text=info["label"],
                 font=thai_font(self.fs(28), "bold"),
                 bg=CARD_COLOR, fg=TEXT_COLOR,
                 justify="center").pack(padx=20)

        tk.Label(popup, text=info["desc"],
                 font=thai_font(self.fs(24)),
                 bg=CARD_COLOR, fg=TEXT_COLOR,
                 justify="left", wraplength=400).pack(padx=20, pady=(10, 14))

        tk.Button(popup, text="ปิด",
                  font=thai_font(self.fs(24)),
                  bg="#e0e0e0", fg=TEXT_COLOR,
                  relief="flat", padx=20, pady=6,
                  cursor="hand2", command=popup.destroy).pack(pady=(0, 16))

        popup.update_idletasks()
        w = popup.winfo_width()
        h = popup.winfo_height()
        x = (popup.winfo_screenwidth() - w) // 2
        y = (popup.winfo_screenheight() - h) // 2
        popup.geometry(f"+{x}+{y}")
