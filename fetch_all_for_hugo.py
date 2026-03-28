#!/usr/bin/env python3
"""
Полный экспорт всех постов Blogger в формат HUGO (Markdown + YAML frontmatter).
Собирает ВСЕ посты с указанного блога и сохраняет их в структуре, готовой для импорта в HUGO.
"""

import os
import json
import logging
from datetime import datetime
from markdownify import markdownify as md
from src.rss_fetcher import BloggerRSSFetcher

# --- КОНСТАНТЫ ---
BLOG_URL = "https://blog.roses-crimea.ru"
OUTPUT_DIR = "hugo_posts_import"
MAX_RESULTS = 500  # Максимум постов за один запрос

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("hugo_export.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def sanitize_filename(text):
    """Очищает строку для использования в имени файла"""
    # Удаляем запрещенные символы
    import re
    text = re.sub(r'[\\/*?:"<>|]', "", text)
    # Заменяем пробелы на подчеркивания
    text = text.replace(" ", "_")
    # Ограничиваем длину
    return text[:100]


def create_hugo_frontmatter(post):
    """Создает YAML frontmatter в формате HUGO"""
    title = post.get('title', 'Без названия')
    published = post.get('published', '')
    author = post.get('author', '')
    link = post.get('link', '')
    post_id = post.get('id', '')
    labels = post.get('labels', [])

    # Извлекаем дату для frontmatter
    date = published if published else datetime.now().isoformat()

    # Формируем frontmatter
    frontmatter = f"""---
title: "{title}"
date: {date}
author: "{author}"
original_link: "{link}"
blogger_id: "{post_id}"
tags: {json.dumps(labels, ensure_ascii=False)}
draft: false
---

"""
    return frontmatter


def convert_html_to_markdown(html_content):
    """Конвертирует HTML в Markdown с помощью markdownify"""
    if not html_content:
        return ""
    # Настройки markdownify для лучшей совместимости с HUGO
    return md(
        html_content,
        heading_style="ATX",  # # Заголовок вместо подчеркивания
        bullets="-",          # Маркированные списки с -
        strong_em_symbol="*"  # Использовать * для жирного/курсива
    )


def save_post_as_markdown(post, output_dir):
    """Сохраняет один пост в MD файл с YAML frontmatter"""
    try:
        # Извлекаем данные
        title = post.get('title', 'Без названия')
        published = post.get('published', '')

        # Создаем имя файла: YYYY-MM-DD-заголовок.md
        date_str = published[:10] if published else datetime.now().strftime("%Y-%m-%d")
        title_clean = sanitize_filename(title)

        filename = f"{date_str}-{title_clean}.md"
        filepath = os.path.join(output_dir, filename)

        # Создаем frontmatter
        frontmatter = create_hugo_frontmatter(post)

        # Конвертируем контент
        content_html = post.get('content', '')
        if not content_html:
            content_html = post.get('summary', '')

        content_md = convert_html_to_markdown(content_html)

        # Сохраняем файл
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(frontmatter)
            f.write(content_md)

        logger.debug(f"Сохранен: {filename}")
        return True

    except Exception as e:
        logger.error(f"Ошибка при сохранении поста: {e}")
        return False


def save_metadata_json(all_posts, output_dir):
    """Сохраняет метаданные всех постов в JSON для справки"""
    metadata = {
        "export_date": datetime.now().isoformat(),
        "source": BLOG_URL,
        "total_posts": len(all_posts),
        "posts": []
    }

    for post in all_posts:
        metadata["posts"].append({
            "title": post.get('title', ''),
            "published": post.get('published', ''),
            "author": post.get('author', ''),
            "link": post.get('link', ''),
            "id": post.get('id', ''),
            "labels": post.get('labels', [])
        })

    metadata_file = os.path.join(output_dir, "metadata.json")
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    logger.info(f"Метаданные сохранены: {metadata_file}")


def main():
    """Основная функция"""
    logger.info("=" * 70)
    logger.info("ЭКСПОРТ ВСЕХ ПОСТОВ BLOGGER → HUGO")
    logger.info(f"Источник: {BLOG_URL}")
    logger.info(f"Выходная папка: {OUTPUT_DIR}")
    logger.info("=" * 70)

    # 1. Создаем папку для результатов
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. Инициализируем fetcher
    fetcher = BloggerRSSFetcher(BLOG_URL)

    # 3. Получаем ВСЕ посты (без фильтра по метке)
    logger.info(f"Запрашиваем до {MAX_RESULTS} постов...")
    posts = fetcher.fetch_posts(label=None, max_results=MAX_RESULTS)

    if not posts:
        logger.error("Не удалось получить посты!")
        return

    logger.info(f"Получено {len(posts)} постов")

    # 4. Сохраняем каждый пост как MD файл
    saved_count = 0
    for post in posts:
        if save_post_as_markdown(post, OUTPUT_DIR):
            saved_count += 1

    # 5. Сохраняем общую метаинформацию
    save_metadata_json(posts, OUTPUT_DIR)

    # 6. Итоговый отчет
    logger.info("\n" + "=" * 70)
    logger.info("✅ ЭКСПОРТ ЗАВЕРШЕН")
    logger.info("=" * 70)
    logger.info(f"Папка: {os.path.abspath(OUTPUT_DIR)}")
    logger.info(f"Сохранено MD-файлов: {saved_count}/{len(posts)}")
    logger.info(f"Метаданные: metadata.json")
    logger.info("\nСтруктура папки готова для импорта в HUGO!")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()