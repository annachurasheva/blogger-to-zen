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
from .rss_fetcher import BloggerRSSFetcher

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


def fetch_posts_for_year(fetcher, year, max_results=50):
    """
    Основная функция сбора.
    Собирает все посты за указанный год с помощью фильтра по дате.
    """
    year_str = str(year)
    
    logger.info(f"Начинаем сбор постов за {year} год...")
    
    # Используем метод fetch_posts с фильтром по дате через параметр q
    # Формируем запрос: published:YYYY или published:YYYY-MM-DD
    # Для RSS Blogger используем published-min и published-max
    posts = fetcher.fetch_posts(
        label=None,
        max_results=max_results
    )
    
    # Фильтруем посты по году
    filtered_posts = []
    for post in posts:
        published = post.get('published', '')
        if published and published.startswith(year_str):
            filtered_posts.append(post)
    
    logger.info(f"Сбор завершен. Найдено постов за {year} год: {len(filtered_posts)}")
    return filtered_posts


def save_post_to_md(entry, output_path):
    """
    Сохраняет один пост в файл .md с YAML-frontmatter.
    """
    # Получаем данные поста
    title = entry.get('title', 'Без названия')
    published = entry.get('published', '')
    author = entry.get('author', '')
    link = entry.get('link', '')
    post_id = entry.get('id', '')
    
    # Получаем дату для имени файла
    date_str = published[:10] if published else 'unknown'
    
    # Чистим заголовок для имени файла (удаляем запрещенные символы)
    title_clean = re.sub(r'[\\/*?:"<>|]', "", title).strip()
    
    filename = f"{date_str}-{title_clean}.md"
    filepath = os.path.join(output_path, filename)

    # Извлекаем контент (полный текст или summary)
    content_html = ''
    if 'content' in entry and entry.content:
        for content in entry.content:
            if content.value:
                content_html = content.value
                break
    if not content_html:
        content_html = entry.get('summary', '')

    # Извлекаем метки (labels) из тегов
    labels = []
    for cat in entry.get('tags', []):
        # Проверяем, что это метка Blogger
        if isinstance(cat, dict) and 'blogger.com/atom/ns#' in cat.get('scheme', ''):
            labels.append(cat.get('term', ''))
        elif hasattr(cat, 'term'):
            labels.append(cat.term)

    # Формируем YAML Front Matter
    frontmatter = f"""---
title: "{title}"
date: {published}
author: {author}
link: {link}
id: {post_id}
labels: {labels}
---
"""

    # Конвертируем HTML контент в Markdown
    content_md = h.handle(content_html) if content_html else ''
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(frontmatter + "\n" + content_md)
        logger.debug(f"Сохранен MD файл: {filename}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении {filename}: {e}")
        return False


def save_post_to_json(entry, output_path):
    """
    Сохраняет данные одного поста в файл .json.
    """
    # Получаем данные поста
    title = entry.get('title', 'Без названия')
    published = entry.get('published', '')
    author = entry.get('author', '')
    link = entry.get('link', '')
    post_id = entry.get('id', '')
    
    date_str = published[:10] if published else 'unknown'
    title_clean = re.sub(r'[\\/*?:"<>|]', "", title).strip()
    
    filename = f"{date_str}-{title_clean}.json"
    filepath = os.path.join(output_path, filename)

    # Извлекаем контент
    content_html = ''
    if 'content' in entry and entry.content:
        for content in entry.content:
            if content.value:
                content_html = content.value
                break
    if not content_html:
        content_html = entry.get('summary', '')

    # Извлекаем метки
    labels = []
    for cat in entry.get('tags', []):
        if isinstance(cat, dict) and 'blogger.com/atom/ns#' in cat.get('scheme', ''):
            labels.append(cat.get('term', ''))
        elif hasattr(cat, 'term'):
            labels.append(cat.term)

    # Создаем словарь с данными поста
    post_data = {
        "title": title,
        "published": published,
        "author": author,
        "link": link,
        "id": post_id,
        "content": content_html,
        "labels": labels
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
    # BloggerRSSFetcher сам преобразует URL в правильный RSS feed URL
    fetcher = BloggerRSSFetcher(BLOG_URL)

    # 3. Сбор постов за указанный год
    # Сначала получаем все посты (или много), затем фильтруем по году
    # Для сбора всех постов используем большой max_results
    all_posts = fetcher.fetch_posts(label=None, max_results=500)
    
    # Фильтруем посты по году
    posts = []
    for post in all_posts:
        published = post.get('published', '')
        if published and published.startswith(str(TARGET_YEAR)):
            posts.append(post)
    
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