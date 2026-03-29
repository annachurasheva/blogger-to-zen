#!/usr/bin/env python3
"""
Полный экспорт ВСЕХ постов Blogger с использованием пагинации.
Решает проблему получения только части постов (125 вместо 188).
"""

import os
import json
import logging
from datetime import datetime
from markdownify import markdownify as md
from src.rss_fetcher import BloggerRSSFetcher
import feedparser
from urllib.parse import quote

# --- КОНСТАНТЫ ---
BLOG_URL = "https://blog.roses-crimea.ru"
OUTPUT_DIR = "hugo_posts_complete"
MAX_PER_PAGE = 100  # Максимум постов за запрос (Blogger лимит)

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("hugo_export_complete.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def sanitize_filename(text):
    """Очищает строку для использования в имени файла"""
    import re
    text = re.sub(r'[\\/*?:"<>|]', "", text)
    text = text.replace(" ", "_")
    return text[:100]


def create_hugo_frontmatter(post):
    """Создает YAML frontmatter в формате HUGO"""
    title = post.get('title', 'Без названия')
    published = post.get('published', '')
    author = post.get('author', '')
    link = post.get('link', '')
    post_id = post.get('id', '')
    labels = post.get('labels', [])

    date = published if published else datetime.now().isoformat()

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
    return md(
        html_content,
        heading_style="ATX",
        bullets="-",
        strong_em_symbol="*"
    )


def save_post_as_markdown(post, output_dir):
    """Сохраняет один пост в MD файл с YAML frontmatter"""
    try:
        title = post.get('title', 'Без названия')
        published = post.get('published', '')

        date_str = published[:10] if published else datetime.now().strftime("%Y-%m-%d")
        title_clean = sanitize_filename(title)

        filename = f"{date_str}-{title_clean}.md"
        filepath = os.path.join(output_dir, filename)

        frontmatter = create_hugo_frontmatter(post)

        content_html = post.get('content', '')
        if not content_html:
            content_html = post.get('summary', '')

        content_md = convert_html_to_markdown(content_html)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(frontmatter)
            f.write(content_md)

        logger.debug(f"Сохранен: {filename}")
        return True

    except Exception as e:
        logger.error(f"Ошибка при сохранении поста: {e}")
        return False


def fetch_all_posts_with_pagination(fetcher):
    """Получает ВСЕ посты с использованием пагинации"""
    all_posts = []
    start_index = 1
    page_num = 1

    logger.info("Начинаем постраничную загрузку всех постов...")

    while True:
        logger.info(f"Загружаем страницу {page_num} (start-index={start_index}, max-results={MAX_PER_PAGE})")

        # Формируем URL с пагинацией
        url = f"{fetcher.base_url}?alt=rss&start-index={start_index}&max-results={MAX_PER_PAGE}"

        try:
            feed = feedparser.parse(url)

            if feed.bozo:
                logger.warning(f"RSS parsing error on page {page_num}: {feed.bozo_exception}")
                break

            entries = feed.entries

            if not entries:
                logger.info(f"На странице {page_num} нет постов. Завершаем.")
                break

            # Преобразуем entries в наш формат
            page_posts = []
            for entry in entries:
                post = {
                    'id': entry.get('id', ''),
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'content': fetcher._extract_content(entry),
                    'summary': entry.get('summary', ''),
                    'published': entry.get('published', ''),
                    'author': entry.get('author', ''),
                    'labels': [tag.term for tag in entry.get('tags', [])]
                }
                page_posts.append(post)

            all_posts.extend(page_posts)
            logger.info(f"Страница {page_num}: получено {len(page_posts)} постов. Всего: {len(all_posts)}")

            # Если получили меньше, чем максимум - это последняя страница
            if len(entries) < MAX_PER_PAGE:
                logger.info("Последняя страница достигнута.")
                break

            start_index += MAX_PER_PAGE
            page_num += 1

        except Exception as e:
            logger.error(f"Ошибка при загрузке страницы {page_num}: {e}")
            break

    return all_posts


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
    logger.info("ПОЛНЫЙ ЭКСПОРТ ВСЕХ ПОСТОВ BLOGGER → HUGO (С ПАГИНАЦИЕЙ)")
    logger.info(f"Источник: {BLOG_URL}")
    logger.info(f"Выходная папка: {OUTPUT_DIR}")
    logger.info(f"Постов за запрос: {MAX_PER_PAGE}")
    logger.info("=" * 70)

    # 1. Создаем папку для результатов
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. Инициализируем fetcher
    fetcher = BloggerRSSFetcher(BLOG_URL)

    # 3. Получаем ВСЕ посты с пагинацией
    all_posts = fetch_all_posts_with_pagination(fetcher)

    if not all_posts:
        logger.error("Не удалось получить посты!")
        return

    logger.info(f"Итого получено {len(all_posts)} постов")

    # 4. Сохраняем каждый пост как MD файл
    saved_count = 0
    for post in all_posts:
        if save_post_as_markdown(post, OUTPUT_DIR):
            saved_count += 1

    # 5. Сохраняем общую метаинформацию
    save_metadata_json(all_posts, OUTPUT_DIR)

    # 6. Итоговый отчет
    logger.info("\n" + "=" * 70)
    logger.info("✅ ПОЛНЫЙ ЭКСПОРТ ЗАВЕРШЕН")
    logger.info("=" * 70)
    logger.info(f"Папка: {os.path.abspath(OUTPUT_DIR)}")
    logger.info(f"Сохранено MD-файлов: {saved_count}/{len(all_posts)}")
    logger.info(f"Метаданные: metadata.json")
    logger.info("\nСтруктура папки готова для импорта в HUGO!")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()