<div align="center">

# Smart Helper

**Скопировал вопрос → нажал Ctrl+Shift+Q → прочитал ответ**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15-41CD52?logo=qt&logoColor=white)](https://pypi.org/project/PyQt5/)
[![GigaChat](https://img.shields.io/badge/GigaChat-Sber-2767e9?logo=sberbank&logoColor=white)](https://developers.sber.ru/portal/products/gigachat-api)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows&logoColor=white)](#требования)

Мини-утилита для рабочего стола: один хоткей — и краткий ответ на скопированный вопрос появляется поверх всех окон, в левом верхнем углу экрана. Запросы обрабатывает **GigaChat**.

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
| **Быстрое скрытие** | `Num 3` прячет/показывает окно — удобно, когда помощник не должен мешать |
| **Нет лишних кликов** | Один хоткей вместо «открыть браузер → вставить → отправить → найти ответ» |
| **Скорость** | 3–5 секунд при нормальном соединении: короткий запрос к модели GigaChat |
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
                                       │ POST /chat/completions → GigaChat│
                                       │ (запрос уходит в сеть)           │
                                       └──────────────┬───────────────────┘
                                                      │  ответ модели
                                                      ▼
                                       ┌──────────────────────────────────┐
                                       │ Плавающее окно PyQt5 в левом     │
                                       │ верхнем углу: только ответ       │
                                       └──────────────────────────────────┘
```

Хоткей регистрируется через Win32 `RegisterHotKey` в отдельном потоке, запрос к модели уходит в фоне — интерфейс не подвисает, а повторное нажатие во время запроса игнорируется (`threading.Lock`). Отдельный хоткей `Num 3` скрывает и снова показывает окно.

## Требования

- **Windows 10/11** — используется Win32 API (`user32.dll`), на других ОС не заработает без переписывания;
- **Python 3.10+**;
- **доступ к GigaChat API** — ключ через Сбер или Cloud.ru Foundation Models (см. ниже).

## Получение и настройка API-ключа

Поддерживаются два варианта подключения к GigaChat. Задаётся всё через переменные окружения, ключи в код вписывать не нужно.

### Вариант 1 (проще): Cloud.ru Foundation Models

OpenAI-совместимый API, нужен только один API-ключ (HTTP bearer-токен).

1. Консоль Cloud.ru → **Пользователи → Сервисные аккаунты → аккаунт**.
2. **Учётные данные доступа → Создать API-ключ** (сервисы: Foundation Models) → скопировать **Key Secret**.
3. Задать переменную окружения:

```bash
setx CLOUDRU_API_KEY "ваш_api_ключ"
# откройте новый терминал, чтобы переменная подхватилась
python helper.py
```

### Вариант 2: напрямую через Сбер

Документация: <https://developers.sber.ru/portal/products/gigachat-api>

Нужны `client_id` и `client_secret` из личного кабинета разработчика Сбера:

```bash
setx GIGACHAT_CLIENT_ID "ваш_client_id"
setx GIGACHAT_CLIENT_SECRET "ваш_client_secret"
```

Либо, если у вас уже есть готовый «ключ авторизации» (base64 от `client_id:client_secret`):

```bash
setx GIGACHAT_AUTH_KEY "ваш_key_авторизации"
```

Если задан `CLOUDRU_API_KEY`, используется Вариант 1; иначе — GigaChat через Сбер. Приложение само запрашивает OAuth-токен и продлевает его, пока работает.

```bash
git clone https://github.com/vlad200zel/smart-helper.git
cd smart-helper
pip install -r requirements.txt
python helper.py
```

**Проверка:** скопируйте любой текст (`Ctrl+C`) и нажмите `Ctrl+Shift+Q` — окно в левом верхнем углу покажет «Думаю…», затем ответ.

## Как пользоваться

1. `python helper.py` — окно с подсказкой висит в углу.
2. В любом приложении выделите вопрос и нажмите `Ctrl+C`.
3. Нажмите **`Ctrl+Shift+Q`** и подождите 3–5 секунд.
4. Прочитайте ответ. Текст в окне можно выделить и скопировать (например, чтобы вставить в бланк).
5. Окно перетаскивается мышью за любое место; закрывается через `Alt+F4` после клика по нему или остановкой скрипта. Клавиша **`Num 3`** скрывает и снова показывает окно.

Подробнее, с разбором ошибок — в [docs/USAGE.md](docs/USAGE.md).

## Настройка

| Что | Где | По умолчанию |
|---|---|---|
| Модель | `CLOUDRU_MODEL` / `GIGACHAT_MODEL` в `helper.py` | `ai-sage/GigaChat3-10B-A1.8B` / `GigaChat` |
| Текст запроса | `PROMPT` в `helper.py` | краткий ответ, без рассуждений |
| Хоткей ответа | `vk_q` и модификаторы в `hotkey_loop` | `Ctrl+Shift+Q` |
| Хоткей скрытия | `VK_NUMPAD3` в `hotkey_loop` | `Num 3` |
| Размер и позиция окна | `setFixedWidth(360)`, `move(50, 50)` | 360 px, левый верхний угол |

## Приватность

Скопированный текст **уходит в сеть** как запрос к API GigaChat: это сетевой сервис, локальной модели здесь нет. Не копируйте под хоткей пароли, персональные данные и рабочую документацию под NDA. Ключи хранятся в переменных окружения, а не в коде — так их можно отозвать в любой момент, не пересобирая проект.

## Ограничения

- Только Windows (завязка на `RegisterHotKey`);
- Один хоткей — одна модель, без истории диалога: каждый запрос независим;
- Ответ зависит от качества распознавания текста в буфере: картинки и PDF-сканы не поддерживаются, нужен выделяемый текст;
- Нет автозапуска при старте системы — запуск вручную или через ярлык в автозагрузке.

---

## English

**Smart Helper** is a small Windows desktop utility: press `Ctrl+Shift+Q` after copying a question and a compact always-on-top window in the top-left corner shows a short, direct answer from **GigaChat** (via Sber or Cloud.ru Foundation Models) — no browser, no chat, no filler.

- Global hotkey registered through Win32 `RegisterHotKey`, so it works from any application.
- Clipboard-based input: copy with a normal `Ctrl+C`, no pasting.
- Frameless, transparent, always-on-top window that never steals focus and can be dragged anywhere.
- `Num 3` toggles the window visibility.
- Answers are requested with a prompt that asks for the point only.
- Graceful handling of an empty clipboard, a busy hotkey and network/API errors.

```bash
git clone https://github.com/vlad200zel/smart-helper.git
cd smart-helper
pip install -r requirements.txt
```

**Set an API key via environment variable.** Two ways:

```bash
# Cloud.ru Foundation Models (simpler, single bearer key)
setx CLOUDRU_API_KEY "your_api_key"

# or Sber GigaChat directly (client_id / client_secret from the Sber dev console)
setx GIGACHAT_CLIENT_ID "your_client_id"
setx GIGACHAT_CLIENT_SECRET "your_client_secret"
```

Then open a new terminal and run:

```powershell
python helper.py
```

Never commit keys into the repository — they are read from environment variables, so they can be revoked at any time without rebuilding the project.

Requires Windows 10/11 and Python 3.10+. Copied text is sent to the GigaChat API over the network — do not use it on secrets or confidential documents. Details and troubleshooting: [docs/USAGE.md](docs/USAGE.md).

---

<div align="center">

**Автор · Author:** Владислав Зеленков · [@vlad200zel](https://github.com/vlad200zel)

Python · PyQt5 · GigaChat

</div>