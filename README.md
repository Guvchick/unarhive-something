# UnArchive Bot

Telegram бот для разархивации файлов и конвертации изображений/видео.

## Возможности

| Тип | Форматы |
|-----|---------|
| 📦 Архивы | ZIP · RAR · 7Z · TAR · GZ · BZ2 · XZ · TAR.GZ · TAR.BZ2 · TAR.XZ |
| 🖼 Изображения | JPG · PNG · WEBP · BMP · GIF · TIFF · ICO |
| 🎬 Видео | MP4 · AVI · MKV · MOV · WEBM · FLV |

## Быстрый старт (Docker)

```bash
# 1. Клонируй репозиторий
git clone <repo-url>
cd unarhive-something-1

# 2. Создай .env
cp .env.example .env
# Вставь BOT_TOKEN и (опционально) ADMIN_ID

# 3. Запусти
docker compose up -d

# Логи
docker compose logs -f
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и список возможностей |
| `/help` | Поддерживаемые форматы |
| `/stats` | Статистика обработанных файлов |
| `/status` | Аптайм и статус зависимостей |

## Настройка (.env)

```env
BOT_TOKEN=1234567890:AAxxxx...   # обязательно
ADMIN_ID=123456789               # опционально — получать уведомления о старте/стопе
LOG_LEVEL=INFO                   # DEBUG | INFO | WARNING | ERROR
```

## Запуск без Docker

```bash
# Установить зависимости
pip install -r requirements.txt

# Установить ffmpeg (для видео)
brew install ffmpeg          # macOS
apt install ffmpeg           # Ubuntu/Debian

# Запустить
python bot.py
```

## Структура проекта

```
├── bot.py                  # Точка входа, startup/shutdown хуки
├── config.py               # Настройки из .env
├── Dockerfile
├── docker-compose.yml
├── handlers/
│   ├── start.py            # /start /help /stats /status
│   ├── document_router.py  # Роутер F.document по расширению
│   ├── archive_handler.py  # Разархивация
│   ├── image_handler.py    # Конвертация изображений
│   └── video_handler.py    # Конвертация видео
└── utils/
    ├── logger.py           # Цветной консольный + ротируемый файловый лог
    ├── stats.py            # Постоянная статистика (JSON)
    ├── archive_utils.py    # zip/tar/7z/rar/gz/bz2/xz
    ├── image_utils.py      # Pillow
    ├── video_utils.py      # ffmpeg
    └── file_utils.py       # Temp-файлы, размеры
```

## Логи

Консольный вывод цветной. Файловые логи с ротацией (10 МБ × 5 файлов):
```
logs/bot.log
logs/bot.log.1
...
```

Пример:
```
2024-01-01 12:00:00  INFO      bot                    Bot is ready. Polling started.
2024-01-01 12:00:05  INFO      handler.archive        [123456 @user] Received archive: data.zip (4.2 МБ)
2024-01-01 12:00:08  INFO      handler.archive        [123456 @user] Done: extracted 5 file(s) in 2.8s
```
