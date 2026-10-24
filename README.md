<div align="center">

# Gemini Helper

**Скопировал вопрос → нажал Ctrl+Shift+Q → прочитал ответ**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15-41CD52?logo=qt&logoColor=white)](https://pypi.org/project/PyQt5/)
[![Gemini API](https://img.shields.io/badge/Gemini%202.5%20Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows&logoColor=white)](#требования)

Мини-утилита для рабочего стола: один хоткей — и краткий ответ на скопированный вопрос появляется поверх всех окон, в левом верхнем углу экрана.

</div>

---

## Что это

Desktop-приложение на Python, которое убирает всю возню с чатами: не нужно открывать браузер, вставлять текст и ждать, пока модель «порассуждает».

1. Копируете вопрос — обычным `Ctrl+C` в любом приложении: браузер, Word, тест, PDF.
2. Нажимаете **`Ctrl+Shift+Q`**.
3. В левом верхнем углу появляется окно с **готовым ответом** — без вступлений, объяснений и воды.

## Возможности

| | |
|---|---|
| **Глобальный хоткей** | `Ctrl+Shift+Q` работает в любом приложении, даже когда окно утилиты неактивно |
| **Ответ без воды** | Промпт требует только суть: вариант ответа или точную формулировку, без рассуждений |
| **Окно поверх всех** | Всегда на виду, без рамки и заголовка, не перехватывает фокус и не мешает печатать |
| **Перетаскивание** | Окно двигается мышью в любое место экрана |
| **Нет лишних кликов** | Один хоткей вместо «открыть браузер → вставить → отправить → найти ответ» |
| **Скорость** | 3–5 секунд при нормальном соединении: короткий запрос к `gemini-2.5-flash` |
| **Защита от дурака** | Пустой буфер, занятый хоткей и ошибки сети показываются человеческим текстом |

## Как это работает

```
 ┌──────────────────────┐   Ctrl+Shift+Q    ┌────────────────────────────┐
 │ Вопрос в буфере      │ ────────────────► │ RegisterHotKey (Win32 API) │
 │ (скопирован Ctrl+C)  │                   └─────────────┬──────────────┘
 └──────────────────────┘                                 │
                                                          ▼
                                       ┌──────────────────────────────────┐
                                       │ pyperclip → текст вопроса        │
                                       │ PROMPT + вопрос → Gemini 2.5     │
                                       │ (google-genai, звонок в сети)    │
                                       └──────────────┬───────────────────┘
                                                      │  ответ модели
                                                      ▼
                                       ┌──────────────────────────────────┐
                                       │ Плавающее окно PyQt5 в левом     │
                                       │ верхнем углу: только ответ       │
                                       └──────────────────────────────────┘
```

Хоткей регистрируется через Win32 `RegisterHotKey` в отдельном потоке, запрос к модели уходит в фоне — интерфейс не подвисает, а повторное нажатие во время запроса игнорируется (`threading.Lock`).

## Требования

- **Windows 10/11** — используется Win32 API (`user32.dll`), на других ОС не заработает без переписывания;
- **Python 3.10+**;
- **ключ Google Gemini API** — обязателен, вписывается в код или в переменную окружения;
- доступ к сервису Gemini из вашей сети: если Google не обслуживает запросы из вашего региона, приложение покажет это отдельной ошибкой, а не «неверным ключом».

## Быстрый старт

> ### ⚠️ ОБЯЗАТЕЛЬНО: вставьте API-ключ в код
>
> Откройте `helper.py` и в начале файла найдите строку:
>
> ```python
> API_KEY = ""  # <-- ВСТАВЬТЕ API-КЛЮЧ СЮДА, МЕЖДУ КАВЫЧКАМИ
> ```
>
> Впишите свой ключ между кавычками: `API_KEY = "ваш_ключ"`. **Без этого приложение не запустится** — оно остановится и прямо скажет, что ключ нужно вставить. Ключ выдаётся бесплатно в [Google AI Studio](https://aistudio.google.com/apikey).
>
> Альтернатива: оставьте строку пустой и задайте переменную окружения `GEMINI_API_KEY` (см. ниже).
>
> 🔒 **Не публикуйте файл с вписанным ключом.** Если закоммитить ключ в открытый репозиторий, он станет доступен всем, и Google его отзовёт. Вписывайте ключ только локально.

```bash
git clone https://github.com/vlad200zel/gemini-helper.git
cd gemini-helper
pip install -r requirements.txt
```

Затем вставьте ключ в `helper.py` (обязательно) или задайте переменную окружения:

```bash
# Windows, cmd/PowerShell — ключ сохраняется в профиле пользователя
setx GEMINI_API_KEY "ваш_ключ"
# откройте новый терминал, чтобы переменная подхватилась
python helper.py
```

Ключ также можно передать на один запуск:

```powershell
$env:GEMINI_API_KEY = "ваш_ключ"; python helper.py
```

**Проверка:** скопируйте любой текст (`Ctrl+C`) и нажмите `Ctrl+Shift+Q` — окно в левом верхнем углу покажет «Думаю…», затем ответ.

## Как пользоваться

1. `python helper.py` — окно с подсказкой висит в углу.
2. В любом приложении выделите вопрос и нажмите `Ctrl+C`.
3. Нажмите **`Ctrl+Shift+Q`** и подождите 3–5 секунд.
4. Прочитайте ответ. Текст в окне можно выделить и скопировать (например, чтобы вставить в бланк).
5. Окно перетаскивается мышью за любое место; закрывается через `Alt+F4` после клика по нему или остановкой скрипта.

Подробнее, с разбором ошибок — в [docs/USAGE.md](docs/USAGE.md).

## Настройка

| Что | Где | По умолчанию |
|---|---|---|
| Модель | `MODEL` в `helper.py` | `gemini-2.5-flash` |
| Текст запроса | `PROMPT` в `helper.py` | краткий ответ, без рассуждений |
| Хоткей | `vk_q` и модификаторы в `hotkey_loop` | `Ctrl+Shift+Q` |
| Размер и позиция окна | `setFixedWidth(360)`, `move(50, 50)` | 360 px, левый верхний угол |

## Приватность

Скопированный текст **уходит в Google** как запрос к Gemini API: это сетевой сервис, локальной модели здесь нет. Не копируйте под хоткей пароли, персональные данные и рабочую документацию под NDA. Ключ хранится в переменной окружения, а не в коде — так его можно отозвать в любой момент, не пересобирая проект.

## Ограничения

- Только Windows (завязка на `RegisterHotKey`);
- Один хоткей — одна модель, без истории диалога: каждый запрос независим;
- Ответ зависит от качества распознавания текста в буфере: картинки и PDF-сканы не поддерживаются, нужен выделяемый текст;
- Нет автозапуска при старте системы — запуск вручную или через ярлык в автозагрузке.

---

## English

**Gemini Helper** is a small Windows desktop utility: press `Ctrl+Shift+Q` after copying a question and a compact always-on-top window in the top-left corner shows a short, direct answer from Google Gemini — no browser, no chat, no filler.

- Global hotkey registered through Win32 `RegisterHotKey`, so it works from any application.
- Clipboard-based input: copy with a normal `Ctrl+C`, no pasting.
- Frameless, transparent, always-on-top window that never steals focus and can be dragged anywhere.
- Answers are requested with a prompt that asks for the point only, using `gemini-2.5-flash`.
- Graceful handling of an empty clipboard, a busy hotkey and network/region errors.

```bash
git clone https://github.com/vlad200zel/gemini-helper.git
cd gemini-helper
pip install -r requirements.txt
```

**Required: paste your API key into the code.** Open `helper.py`, find the line `API_KEY = ""` at the top and put your key between the quotes — the app refuses to start without it. Alternatively, leave the line empty and set the `GEMINI_API_KEY` environment variable:

```bash
setx GEMINI_API_KEY "your_key"    # then open a new terminal
python helper.py
```

Never commit the file with the key filled in: a key pushed to a public repository is public, and Google revokes it.

Requires Windows 10/11, Python 3.10+ and a Gemini API key. Copied text is sent to Google — do not use it on secrets or confidential documents. Details and troubleshooting: [docs/USAGE.md](docs/USAGE.md).

---

<div align="center">

**Автор · Author:** Владислав Зеленков · [@vlad200zel](https://github.com/vlad200zel)

Python · PyQt5 · Gemini API

</div>
