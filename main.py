import tkinter as tk
import os, shutil, platform
import os
print("PID:", os.getpid())

def _fix_windows_dpi():
    """แก้ DPI scaling บน Windows ไม่ให้ขยาย UI อัตโนมัติ"""
    if platform.system() != "Windows":
        return
    try:
        import ctypes
        # Windows 8.1+: per-monitor DPI aware
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            # Windows Vista+: system DPI aware (fallback)
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


_fix_windows_dpi()

from screens.base import BG_COLOR


def _install_font():
    """โหลด THSarabunNew.ttf เข้าระบบ (macOS: copy → ~/Library/Fonts, Windows: GDI AddFontResource)"""
    import sys
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    src  = os.path.join(base, "assets", "fonts", "THSarabunNew.ttf")
    if not os.path.exists(src):
        return

    if platform.system() == "Darwin":
        dst = os.path.expanduser("~/Library/Fonts/THSarabunNew.ttf")
        if not os.path.exists(dst):
            shutil.copy2(src, dst)

    elif platform.system() == "Windows":
        # โหลด font เข้า GDI แบบ public เพื่อให้ tkinter เห็น
        try:
            import ctypes
            ctypes.windll.gdi32.AddFontResourceExW(ctypes.c_wchar_p(src), 0, 0)
            # broadcast WM_FONTCHANGE ให้ทุก process (รวม tkinter) รู้ว่ามี font ใหม่
            HWND_BROADCAST = 0xFFFF
            WM_FONTCHANGE  = 0x001D
            ctypes.windll.user32.PostMessageW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0)
        except Exception as e:
            print(f"Windows font load error: {e}")


_install_font()


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # ── Windows DPI fix ───────────────────────────────────────────────
        # tkinter บน Windows ใช้ DPI จริงของจอ (96+) แทน 72 ของ macOS
        # ทำให้ font ใหญ่กว่าที่ออกแบบไว้ → reset scaling ให้ตรงกับ macOS
        if platform.system() == "Windows":
            self.tk.call("tk", "scaling", 1.0)

        self.title("TG270 Monitor QC System")
        self.resizable(True, True)
        self.minsize(900, 600)
        self.configure(bg=BG_COLOR)

        # ── App icon ─────────────────────────────────────────────────────────
        try:
            from PIL import Image as _Img, ImageTk as _ITk
            _icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "assets", "logo", "App_Logo.jpg")
            _icon_img = _Img.open(_icon_path).convert("RGBA").resize((64, 64))
            self._app_icon = _ITk.PhotoImage(_icon_img)
            self.wm_iconphoto(True, self._app_icon)
        except Exception:
            pass

        # เปิดเต็มจอ
        self.after(0, self._maximize)

        # shared state
        self.session: dict = {}

        # full-window container
        self.container = tk.Frame(self, bg=BG_COLOR)
        self.container.pack(fill="both", expand=True)

        # register screens
        self.screens: dict = {}
        self._register_screens()

        self.show("home")

    def _maximize(self):
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        self.geometry(f"{ws}x{hs}+0+0")

    def _register_screens(self):
        from screens.home           import HomeScreen
        from screens.select_type    import SelectTypeScreen
        from screens.select_period  import SelectPeriodScreen
        from screens.login          import LoginScreen
        from screens.confirm        import ConfirmScreen
        from screens.instructions   import InstructionsScreen
        from screens.test_runner    import TestRunnerScreen
        from screens.results        import ResultsScreen
        from screens.after_save     import AfterSaveScreen
        from screens.criteria       import CriteriaScreen
        from screens.comparison     import ComparisonScreen
        from screens.history        import HistoryScreen
        from screens.history_result import HistoryResultScreen
        from screens.register       import RegisterScreen
        from screens.user_list      import UserListScreen

        screen_classes = {
            "home":           HomeScreen,
            "select_type":    SelectTypeScreen,
            "select_period":  SelectPeriodScreen,
            "login":          LoginScreen,
            "confirm":        ConfirmScreen,
            "instructions":   InstructionsScreen,
            "test_runner":    TestRunnerScreen,
            "results":        ResultsScreen,
            "after_save":     AfterSaveScreen,
            "criteria":       CriteriaScreen,
            "comparison":     ComparisonScreen,
            "history":        HistoryScreen,
            "history_result": HistoryResultScreen,
            "register":       RegisterScreen,
            "user_list":      UserListScreen,
        }

        for name, cls in screen_classes.items():
            frame = cls(self.container, self)
            self.screens[name] = frame

    def show(self, name: str, **kwargs):
        screen = self.screens[name]
        screen.place(relx=0, rely=0, relwidth=1, relheight=1)
        screen.lift()
        if hasattr(screen, "on_show"):
            screen.on_show(**kwargs)
        self.update_idletasks()
        for s in self.screens.values():
            if s is not screen:
                if hasattr(s, "on_hide"):
                    s.on_hide()
                s.place_forget()


if __name__ == "__main__":
    app = App()
    app.mainloop()
