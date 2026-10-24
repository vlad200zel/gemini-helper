"""Gemini Helper — ответ на скопированный вопрос по горячей клавише.

Скопируйте вопрос (Ctrl+C), нажмите Ctrl+Shift+Q — в левом верхнем углу
появится краткий ответ от Gemini. Окно поверх всех, без рамки, перетаскивается
мышью и не забирает фокус.
"""

import ctypes
import os
import sys
import threading
from ctypes import wintypes

import pyperclip
from google import genai
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

# ==============================================================================
#  ОБЯЗАТЕЛЬНО: ВСТАВЬТЕ СВОЙ API-КЛЮЧ GEMINI В СТРОКУ НИЖЕ
#  Ключ выдаётся в Google AI Studio: https://aistudio.google.com/apikey
#  Без ключа приложение не запустится — впишите его между кавычками.
#  Если ключ уже задан переменной окружения GEMINI_API_KEY, строку можно
#  оставить пустой — тогда возьмётся переменная окружения.
#  Внимание: не публикуйте файл с вписанным ключом — ключ станет доступен всем.
# ==============================================================================
API_KEY = ""  # <-- ВСТАВЬТЕ API-КЛЮЧ СЮДА, МЕЖДУ КАВЫЧКАМИ
API_KEY = API_KEY.strip() or os.environ.get("GEMINI_API_KEY", "")
MODEL = "gemini-2.5-flash"
PROMPT = (
    "Ты помогаешь с тестом. Дай максимально краткий и точный правильный ответ "
    "на этот вопрос (только сам вариант ответа или суть, без лишней воды): "
)

MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
WM_HOTKEY = 0x0312
HOTKEY_ID = 1

user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = ctypes.c_int

_busy = threading.Lock()


class FloatingWindow(QWidget):
    answer_ready = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._drag_offset = None
        self.initUI()

    def initUI(self):
        # Окно поверх всех, без рамок, не забирает фокус и не висит в панели задач
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.label = QLabel("Выдели вопрос, жми Ctrl+C, затем Ctrl+Shift+Q", self)
        self.label.setStyleSheet(
            "color: #000000; "
            "background-color: rgba(255, 255, 255, 120); "
            "font-size: 13px; "
            "font-weight: bold; "
            "padding: 8px; "
            "border-radius: 6px;"
        )
        self.label.setWordWrap(True)
        self.label.setFixedWidth(360)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)

        self.move(50, 50)
        self.show()

    def update_answer(self, text):
        self.label.setText(text)
        self.adjustSize()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_offset = None


def ask_ai(window):
    if not _busy.acquire(blocking=False):
        return
    try:
        question = pyperclip.paste()
        if not question or not question.strip():
            window.answer_ready.emit("Буфер обмена пуст — сначала скопируй вопрос через Ctrl+C")
            return

        window.answer_ready.emit("Думаю…")
        response = client.models.generate_content(
            model=MODEL,
            contents=PROMPT + question.strip(),
        )
        text = (response.text or "").strip()
        window.answer_ready.emit(text or "Модель вернула пустой ответ")
    except Exception as e:
        text = str(e)
        if "location is not supported" in text:
            text = "Gemini не отвечает: запросы из РФ не поддерживаются (ошибка региона, не ключа)"
        window.answer_ready.emit(f"Ошибка: {text}")
    finally:
        _busy.release()


def hotkey_loop(window):
    vk_q = ord("Q")
    if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_SHIFT, vk_q):
        code = ctypes.get_last_error()
        window.answer_ready.emit(f"Не удалось занять Ctrl+Shift+Q (код {code}): сочетание занято другой программой")
        return

    try:
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                threading.Thread(target=ask_ai, args=(window,), daemon=True).start()
    finally:
        user32.UnregisterHotKey(None, HOTKEY_ID)


def _utf8_console():
    """Чтобы русский текст в консоли не превращался в кракозябры."""
    try:
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except Exception:
        pass
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main():
    _utf8_console()

    if not API_KEY:
        print("ОБЯЗАТЕЛЬНО ВСТАВЬТЕ API-КЛЮЧ GEMINI:")
        print('  откройте helper.py и впишите ключ в строку  API_KEY = ""  ')
        print("  либо задайте переменную окружения:")
        print('  setx GEMINI_API_KEY "ваш_ключ"   (Windows, затем новый терминал)')
        print("  Ключ выдаётся в Google AI Studio: https://aistudio.google.com/apikey")
        sys.exit(1)

    global client
    client = genai.Client(api_key=API_KEY)

    app = QApplication(sys.argv)
    window = FloatingWindow()
    window.answer_ready.connect(window.update_answer)

    threading.Thread(target=hotkey_loop, args=(window,), daemon=True).start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
