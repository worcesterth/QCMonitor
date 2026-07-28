import os
import tkinter as tk
from PIL import Image, ImageTk
from screens.base import (
    BaseScreen, CARD_COLOR,
    TEXT_COLOR, thai_font,
)

_LOGO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo")


def _load_logo(path: str, height: int) -> ImageTk.PhotoImage | None:
    try:
        img   = Image.open(path).convert("RGBA")
        w, h  = img.size
        img   = img.resize((int(w * height / h), height), Image.LANCZOS)
        bg    = Image.new("RGBA", img.size, (255, 255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        return ImageTk.PhotoImage(bg.convert("RGB"))
    except Exception:
        return None


class HomeScreen(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app)

        _logo_sizes = {
            "NULOGO-Download.png":       int(90 * self._s),
            "logo-คณะ-สี-ภาษาไทย.png": int(130 * self._s),
        }

        card = self.card(self)
        card.place(relx=0.5, rely=0.5, anchor="center", width=self.CARD_W, height=self.CARD_HL)

        self.card_header(card, "โปรแกรมตรวจคุณภาพหน้าจอ", size=self.fs(24))

        # ── bottom bar: ทีมผู้พัฒนา ──────────────────────────────────────
        bottom = tk.Frame(card, bg=CARD_COLOR)
        bottom.pack(side="bottom", fill="x", padx=16, pady=(0, 8))

        dev_lbl = tk.Label(bottom, text="ทีมผู้พัฒนา ▸",
                           font=thai_font(self.fs(18)), bg=CARD_COLOR,
                           fg="#888888", cursor="hand2")
        dev_lbl.pack(side="right")
        dev_lbl.bind("<ButtonRelease-1>", lambda _: self._show_team())
        dev_lbl.bind("<Enter>", lambda _: dev_lbl.configure(fg=TEXT_COLOR))
        dev_lbl.bind("<Leave>", lambda _: dev_lbl.configure(fg="#888888"))

        ref_lbl = tk.Label(bottom, text="เอกสารอ้างอิง ▸",
                           font=thai_font(self.fs(18)), bg=CARD_COLOR,
                           fg="#888888", cursor="hand2")
        ref_lbl.pack(side="right", padx=(0, 16))
        ref_lbl.bind("<ButtonRelease-1>", lambda _: self._show_references())
        ref_lbl.bind("<Enter>", lambda _: ref_lbl.configure(fg=TEXT_COLOR))
        ref_lbl.bind("<Leave>", lambda _: ref_lbl.configure(fg="#888888"))

        # ── body ────────────────────────────────────────────────────────
        body = tk.Frame(card, bg=CARD_COLOR)
        body.pack(fill="both", expand=True)

        # โลโก้คู่
        logo_row = tk.Frame(body, bg=CARD_COLOR)
        logo_row.pack(pady=(20, 4))

        self._logo_refs: list = []
        for fname, h in _logo_sizes.items():
            photo = _load_logo(os.path.join(_LOGO_DIR, fname), h)
            if photo:
                self._logo_refs.append(photo)
                tk.Label(logo_row, image=photo, bg=CARD_COLOR).pack(side="left", padx=24)

        # title + ปุ่ม
        self.title_label(body, "TG270 Monitor QC System", size=self.fs(50)).pack(pady=(6, 24))

        self.primary_btn(
            body, "เริ่มการทดสอบ",
            command=lambda: app.show("select_type"),
            width=20, fontsize=self.fs(40), pady=10, padx=20,
        ).pack()

        self.primary_btn(
            body, "ประวัติการทดสอบ",
            command=lambda: app.show("history"),
            width=20, fontsize=self.fs(40), pady=10, padx=20,
        ).pack(pady=(14, 0))

        self.primary_btn(
            body, "ลงทะเบียน",
            command=lambda: app.show("register"),
            width=20, fontsize=self.fs(40), pady=10, padx=20,
        ).pack(pady=(14, 0))

    # ── เอกสารอ้างอิง popup ─────────────────────────────────────────────

    def _show_references(self):
        dlg = tk.Toplevel(self.app)
        dlg.title("เอกสารอ้างอิง")
        dlg.configure(bg=CARD_COLOR)
        dlg.resizable(False, False)
        dlg.transient(self.app)
        dlg.grab_set()

        w, h = int(780 * self._s), int(480 * self._s)
        px = self.app.winfo_x() + self.app.winfo_width()  // 2 - w // 2
        py = self.app.winfo_y() + self.app.winfo_height() // 2 - h // 2
        dlg.geometry(f"{w}x{h}+{px}+{py}")

        hdr = tk.Frame(dlg, bg="#474747", height=38)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="เอกสารอ้างอิง", font=thai_font(self.fs(20), "bold"),
                 bg="#474747", fg="#FFFFFF").pack(side="left", padx=16, pady=10)

        content = tk.Frame(dlg, bg=CARD_COLOR)
        content.pack(fill="both", expand=True, padx=24, pady=16)

        refs = [
            ("1.", "Bevins NB, Badano A, et al. Display Quality Assurance - The Report of AAPM Task Group 270. "
                   "American Association of Physicists in Medicine. Alexandria; 2019,\n"
                   "https://www.aapm.org/pubs/reports/RPT_270.pdf"),
            ("2.", "International Atomic Energy Agency. IAEA Human Health Series No. 47 - Handbook of Basic Quality Control Tests for Diagnostic Radiology. "
                   "Vienna; 2023,\n"
                   "https://www-pub.iaea.org/MTCD/Publications/PDF/PUB2021_web.pdf"),
            ("3.", "กรมวิทยาศาสตร์การแพทย์ กระทรวงสาธารณสุข. การควบคุมคุณภาพเครื่องเอกซเรย์วินิจฉัยทางการแพทย์. "
                   "นนทบุรี: กรมวิทยาศาสตร์การแพทย์; 2022."),
            ("4.", "American College of Radiology, American Association of Physicists in Medicine, Society for Imaging Informatics in Medicine. "
                   "ACR-AAPM-SIIM Technical Standard for Electronic Practice of Medical Imaging. "
                   "Reston (VA): American College of Radiology; 2022,\n"
                   "https://gravitas.acr.org/PPTS/GetDocumentView?docId=136"),
        ]

        for num, text in refs:
            row = tk.Frame(content, bg=CARD_COLOR)
            row.pack(fill="x", pady=(0, 14), anchor="w")
            tk.Label(row, text=num, font=thai_font(self.fs(20), "bold"),
                     bg=CARD_COLOR, fg=TEXT_COLOR, anchor="nw", width=3).pack(side="left", anchor="nw")
            tk.Label(row, text=text, font=thai_font(self.fs(18)),
                     bg=CARD_COLOR, fg="#555555", anchor="w",
                     justify="left", wraplength=int(680 * self._s)).pack(side="left", anchor="nw")

        btn_bar = tk.Frame(dlg, bg=CARD_COLOR)
        btn_bar.pack(fill="x", padx=24, pady=(0, 16))
        self.primary_btn(btn_bar, "ปิด", dlg.destroy,
                         fontsize=self.fs(22), width=10).pack(side="right")

    # ── ทีมผู้พัฒนา popup ───────────────────────────────────────────────

    def _show_team(self):
        dlg = tk.Toplevel(self.app)
        dlg.title("ทีมผู้พัฒนา")
        dlg.configure(bg=CARD_COLOR)
        dlg.resizable(False, False)
        dlg.transient(self.app)
        dlg.grab_set()

        w, h = int(520 * self._s), int(380 * self._s)
        px = self.app.winfo_x() + self.app.winfo_width()  // 2 - w // 2
        py = self.app.winfo_y() + self.app.winfo_height() // 2 - h // 2
        dlg.geometry(f"{w}x{h}+{px}+{py}")

        # header
        hdr = tk.Frame(dlg, bg="#474747", height=38)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="ทีมผู้พัฒนา", font=thai_font(self.fs(20), "bold"),
                 bg="#474747", fg="#FFFFFF").pack(side="left", padx=16, pady=10)

        # content
        content = tk.Frame(dlg, bg=CARD_COLOR)
        content.pack(fill="both", expand=True, padx=28, pady=20)

        members = [
            # ("ที่ปรึกษา",     ""),
            # ("",               ""),
            ("ผู้พัฒนาระบบ", "1. นายณัฐวุฒิ โรจน์บุณถึง\n2. นายอธิวัฒน์ ยศปัญญา\n  3. นางสาววรฤทัย มหาวงษ์"),
        #     ("",               ""),
        #     ("สังกัด",         "ภาควิชาวิทยาการคอมพิวเตอร์ คณะวิทยาศาสต  มหาวิทยาลัยนเรศวร"),
       
        ]
        for role, name in members:
            row = tk.Frame(content, bg=CARD_COLOR)
            row.pack(fill="x", pady=2)
            if role:
                tk.Label(row, text=role, font=thai_font(self.fs(22), "bold"),
                         bg=CARD_COLOR, fg=TEXT_COLOR,
                         width=16, anchor="w").pack(side="left")
            if name:
                tk.Label(row, text=name, font=thai_font(self.fs(20)),
                         bg=CARD_COLOR, fg="#555555", anchor="w").pack(side="left")

        # close
        btn_bar = tk.Frame(dlg, bg=CARD_COLOR)
        btn_bar.pack(fill="x", padx=24, pady=(0, 16))
        self.primary_btn(btn_bar, "ปิด", dlg.destroy,
                         fontsize=self.fs(22), width=10).pack(side="right")
