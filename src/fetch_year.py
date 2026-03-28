#!/usr/bin/env python3
"""
Скрипт для сбора всех постов блога Blogger за определенный год.
Сохраняет каждый пост в отдельный файл:
  - .md (Markdown с YAML-frontmatter)
  - .json (исходные данные)
"""

import os
import re
import json
import logging
from datetime import datetime
from urllib.parse import urlparse
from rss_fetcher import BloggerRSSFetcher # Предполагается, что этот класс у вас уже есть

# --- БЛОК 2: Новый импорт и настройка (ВСТАВИТЬ СЮДА) ---
import html2text

# Создаем объект конвертера (это "контейнер" с настройками)
h = html2text.HTML2Text()

# Настраиваем его для сохранения структуры Markdown
h.ignore_links = False  # Сохраняем ссылки [текст](url)
h.ignore_images = False # Сохраняем изображения ![alt](url)
h.body_width = 0        # Не переносим строки по ширине (оставляем как есть)
h.unicode_snob = True   # Корректно сохраняем русские символы и кавычки


# --- НАЧАЛО БЛОКА КОНСТАНТ (МЕНЯЙТЕ ЗДЕСЬ) ---
# 1. URL вашего блога
BLOG_URL = "https://crimeanblog.blogspot.com"

# 2. Год, за который нужно собрать посты
TARGET_YEAR = 2009

# 3. Папка, куда сохранять результат (создастся автоматически)
OUTPUT_FOLDER = f"posts_{TARGET_YEAR}"

# 4. Лимит постов за один запрос к RSS (можно не менять)
POSTS_PER_PAGE = 50

# 5. Файл для логирования ошибок
LOG_FILE = "blogger_fetcher.log"
# --- КОНЕЦ БЛОКА КОНСТАНТ ---


# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def validate_blog_url(url):
    """Проверяет, что URL блога указан верно."""
    parsed = urlparse(url)
    if not parsed.netloc or "blogger.com" not in parsed.netloc:
        logger.error(f"Ошибка: '{url}' не выглядит как адрес блога на Blogger.")
        return False
    return True


def fetch_posts_for_year(fetcher, year, posts_per_page):
    """
    Основная функция сбора.
    Использует пагинацию RSS-ленты, чтобы забрать все посты за год.
    """
    all_posts = []
    start_index = 1
    year_str = str(year)

    logger.info(f"Начинаем сбор постов за {year} год...")

    while True:
        # Формируем URL с фильтром по дате и пагинацией
        rss_url = (
            f"{fetcher.base_url}/feeds/posts/default?"
            f"published-min={year_str}-01-01T00:00:00&"
            f"published-max={year_str}-12-31T23:59:59&"
            f"start-index={start_index}&"
            f"max-results={posts_per_page}"
        )

        feed = fetcher.parse_feed(rss_url)
        entries = feed.entries

        if not entries:
            # Нет больше постов, выходим из цикла
            break

        logger.debug(f"Получена страница. Постов на странице: {len(entries)}")
        all_posts.extend(entries)

        # Проверяем, есть ли следующая страница
        # Если постов меньше, чем запрошено max-results, это последняя страница
        if len(entries) < posts_per_page:
            logger.info("Достигнут конец списка постов.")
            break

        start_index += posts_per_page

    logger.info(f"Сбор завершен. Найдено постов за {year} год: {len(all_posts)}")
    return all_posts


def save_post_to_md(entry, output_path):
    """
    Сохраняет один пост в файл .md с YAML-frontmatter.
    """
    # Получаем дату для имени файла
    date_str = entry.published[:10] # 'YYYY-MM-DD'
    
    # Чистим заголовок для имени файла (удаляем запрещенные символы)
    title_clean = re.sub(r'[\\/*?:"<>|]', "", entry.title).strip()
    
    filename = f"{date_str}-{title_clean}.md"
    filepath = os.path.join(output_path, filename)

    # Извлекаем контент (полный текст или summary)
    content_html = getattr(entry, "content", [{}])[0].get("value") or entry.summary

    # Извлекаем метки (labels) из тегов <category>
    labels = []
    for cat in entry.get('tags', []):
        if 'blogger.com/atom/ns#' in cat.get('scheme', ''):
            labels.append(cat.term)

    # Формируем YAML Front Matter
    frontmatter = f"""---
title: "{entry.title}"
date: {entry.published}
author: {entry.author}
link: {entry.link}
id: {entry.id}
labels: {labels} # Список меток поста
---
"""

    # Конвертируем HTML контент в простой текст (или используем markdownify для лучшей конвертации)
    # Здесь используем простой парсинг для примера, но лучше установить библиотеку html2text или markdownify
    content_md = h.handle(content_html)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(frontmatter + "\n" + content_text)
        logger.debug(f"Сохранен MD файл: {filename}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении {filename}: {e}")
        return False


def save_post_to_json(entry, output_path):
    """
    Сохраняет данные одного поста в файл .json.
    """
    date_str = entry.published[:10]
    title_clean = re.sub(r'[\\/*?:"<>|]', "", entry.title).strip()
    
    filename = f"{date_str}-{title_clean}.json"
    filepath = os.path.join(output_path, filename)

    # Создаем словарь с данными поста для сохранения в JSON
    post_data = {
        "title": entry.title,
        "published": entry.published,
        "author": entry.author,
        "link": entry.link,
        "id": entry.id,
        "content": getattr(entry, "content", [{}])[0].get("value") or entry.summary,
        "labels": [cat.term for cat in entry.get('tags', []) if 'blogger.com/atom/ns#' in cat.get('scheme', '')]
    }

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(post_data, f, indent=2, ensure_ascii=False)
        logger.debug(f"Сохранен JSON файл: {filename}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении {filename}: {e}")
        return False


def main():
    """Точка входа в программу."""
    
    # 1. Валидация URL
    if not validate_blog_url(BLOG_URL):
        return

    # 2. Создание объекта для работы с RSS
    fetcher = BloggerRSSFetcher(BLOG_URL)

    # 3. Сбор постов за указанный год
    posts = fetch_posts_for_year(fetcher, TARGET_YEAR, POSTS_PER_PAGE)
    
    if not posts:
        logger.warning("Постов для сохранения не найдено.")
        return

    # 4. Создание папки для результатов
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # 5. Сохранение файлов для каждого поста
    md_count = 0
    json_count = 0

    for post in posts:
        if save_post_to_md(post, OUTPUT_FOLDER):
            md_count += 1
        
        if save_post_to_json(post, OUTPUT_FOLDER):
            json_count += 1

    # 6. Итоговый отчет
    logger.info("\n=== ЗАВЕРШЕНИЕ ===")
    logger.info(f"Папка с результатами: {os.path.abspath(OUTPUT_FOLDER)}")
    logger.info(f"Сохранено .md файлов: {md_count}")
    logger.info(f"Сохранено .json файлов: {json_count}")


if __name__ == "__main__":
    main()