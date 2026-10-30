import base64
import ctypes
import os
import sys
import threading
import time
import uuid
from ctypes import wintypes

import pyperclip
import requests
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

# Вариант 1 (проще): Cloud.ru Foundation Models — OpenAI-совместимый API, нужен только API-ключ.
#   setx CLOUDRU_API_KEY "ваш_api_ключ"
#   Ключ: консоль cloud.ru -> Пользователи -> Сервисные аккаунты -> аккаунт ->
#   Учетные данные доступа -> Создать API-ключ (Сервисы: Foundation Models) -> Key Secret.
CLOUDRU_API_KEY = os.environ.get("CLOUDRU_API_KEY", "") or os.environ.get("GIGACHAT_API_KEY", "")
CLOUDRU_BASE_URL = os.environ.get("CLOUDRU_BASE_URL", "https://foundation-models.api.cloud.ru/v1")
CLOUDRU_MODEL = os.environ.get("CLOUDRU_MODEL", "ai-sage/GigaChat3-10B-A1.8B")

# Вариант 2: напрямую Сбер — https://developers.sber.ru/portal/products/gigachat-api
#   setx GIGACHAT_CLIENT_ID "ваш_client_id"
#   setx GIGACHAT_CLIENT_SECRET "ваш_client_secret"
GIGACHAT_CLIENT_ID = os.environ.get("GIGACHAT_CLIENT_ID", "")
GIGACHAT_CLIENT_SECRET = os.environ.get("GIGACHAT_CLIENT_SECRET", "")
# Готовый «ключ авторизации» из кабинета Сбера (уже base64 от client_id:client_secret).
GIGACHAT_AUTH_KEY = os.environ.get("GIGACHAT_AUTH_KEY") or "GIGACHAT_AUTH_KEY_GIGACHAT"
GIGACHAT_SCOPE = os.environ.get("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
GIGACHAT_MODEL = os.environ.get("GIGACHAT_MODEL", "GigaChat")
OAUTH_URL = os.environ.get("GIGACHAT_OAUTH_URL", "https://ngw.devices.sberbank.ru:9443/api/v2/oauth")
CHAT_URL = os.environ.get(
    "GIGACHAT_CHAT_URL", "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
)
PROMPT = (
    "Ты помогаешь с тестом. Дай максимально краткий и точный правильный ответ "
    "на этот вопрос (только сам вариант ответа или суть, без лишней воды): "
)

MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
WM_HOTKEY = 0x0312
HOTKEY_ID = 1
HIDE_HOTKEY_ID = 2
VK_NUMPAD3 = 0x63

user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = ctypes.c_int

_busy = threading.Lock()

_token = {"value": None, "expires_at": 0.0}
_token_lock = threading.Lock()
# У Сбера свой корневой сертификат: сначала проверяем как обычно, при ошибке цепочки — без проверки.
_verify = {"ssl": True}


def _request(method, url, **kwargs):
    if _verify["ssl"]:
        try:
            return requests.request(method, url, verify=True, timeout=60, **kwargs)
        except requests.exceptions.SSLError:
            _verify["ssl"] = False
            requests.packages.urllib3.disable_warnings(
                requests.packages.urllib3.exceptions.InsecureRequestWarning
            )
    return requests.request(method, url, verify=False, timeout=60, **kwargs)


def _basic_auth():
    if GIGACHAT_AUTH_KEY:
        return GIGACHAT_AUTH_KEY.strip()
    if not (GIGACHAT_CLIENT_ID and GIGACHAT_CLIENT_SECRET):
        raise RuntimeError(
            "не заданы GIGACHAT_CLIENT_ID / GIGACHAT_CLIENT_SECRET — см. строки 25-29 в helper.py"
        )
    if GIGACHAT_CLIENT_SECRET.upper().startswith("GIGACHAT_"):
        raise RuntimeError(
            f"в GIGACHAT_CLIENT_SECRET лежит scope «{GIGACHAT_CLIENT_SECRET}», а нужен Client Secret из проекта"
        )
    return base64.b64encode(
        f"{GIGACHAT_CLIENT_ID}:{GIGACHAT_CLIENT_SECRET}".encode()
    ).decode()


def _access_token():
    with _token_lock:
        now = time.time()
        if _token["value"] and now < _token["expires_at"] - 60:
            return _token["value"]
        resp = _request(
            "POST",
            OAUTH_URL,
            headers={
                "Authorization": f"Basic {_basic_auth()}",
                "RqUID": str(uuid.uuid4()),
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            data={"scope": GIGACHAT_SCOPE},
        )
        resp.raise_for_status()
        data = resp.json()
        _token["value"] = data["access_token"]
        expires_at = data.get("expires_at")
        _token["expires_at"] = expires_at / 1000 if expires_at else now + 1500
        return _token["value"]


def ask_gigachat(question):
    resp = _request(
        "POST",
        CHAT_URL,
        headers={
            "Authorization": f"Bearer {_access_token()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "model": GIGACHAT_MODEL,
            "temperature": 0.2,
            "max_tokens": 512,
            "messages": [{"role": "user", "content": PROMPT + question}],
        },
    )
    if resp.status_code == 401:
        _token["value"] = None
    resp.raise_for_status()
    return (resp.json()["choices"][0]["message"]["content"] or "").strip()


def _ask_cloudru(question):
    resp = requests.post(
        f"{CLOUDRU_BASE_URL.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {CLOUDRU_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "model": CLOUDRU_MODEL,
            "temperature": 0.2,
            "max_tokens": 512,
            "messages": [{"role": "user", "content": PROMPT + question}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    return (resp.json()["choices"][0]["message"]["content"] or "").strip()


def ask_model(question):
    if CLOUDRU_API_KEY:
        return _ask_cloudru(question)
    return ask_gigachat(question)


def _human_error(e):
    if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
        hints = {
            400: "неверный запрос — чаще всего кривые ключи (см. текст ответа)",
            401: "ключи не приняты: проверь API-ключ либо client_id/client_secret",
            403: "нет доступа к модели — проверь scope (GIGACHAT_API_PERS)",
            429: "исчерпан лимит запросов, попробуй позже",
            503: "сервис перегружен, попробуй ещё раз",
        }
        code = e.response.status_code
        return f"API {code}: {hints.get(code, e.response.text[:200])}"
    if isinstance(e, requests.exceptions.RequestException):
        return f"сеть недоступна: {e}"
    return str(e)


class FloatingWindow(QWidget):
    answer_ready = pyqtSignal(str)
    toggle_requested = pyqtSignal()

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

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()

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
        text = ask_model(question.strip())
        window.answer_ready.emit(text or "Модель вернула пустой ответ")
    except Exception as e:
        window.answer_ready.emit(f"Ошибка: {_human_error(e)}")
    finally:
        _busy.release()


def hotkey_loop(window):
    vk_q = ord("Q")
    if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_SHIFT, vk_q):
        code = ctypes.get_last_error()
        window.answer_ready.emit(f"Не удалось занять Ctrl+Shift+Q (код {code}): сочетание занято другой программой")
        return

    user32.RegisterHotKey(None, HIDE_HOTKEY_ID, 0, VK_NUMPAD3)

    try:
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                threading.Thread(target=ask_ai, args=(window,), daemon=True).start()
            elif msg.message == WM_HOTKEY and msg.wParam == HIDE_HOTKEY_ID:
                window.toggle_requested.emit()
    finally:
        user32.UnregisterHotKey(None, HIDE_HOTKEY_ID)
        user32.UnregisterHotKey(None, HOTKEY_ID)


def main():
    app = QApplication(sys.argv)
    window = FloatingWindow()
    window.answer_ready.connect(window.update_answer)
    window.toggle_requested.connect(window.toggle_visibility)

    threading.Thread(target=hotkey_loop, args=(window,), daemon=True).start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
