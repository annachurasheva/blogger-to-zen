#!/usr/bin/env python3
"""
Тестирование меток Blogger
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BLOGGER_RSS_BASE, BLOGS
from src.rss_fetcher import BloggerRSSFetcher

def main():
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ МЕТОК BLOGGER")
    print("=" * 60)
    
    # Инициализация
    fetcher = BloggerRSSFetcher(BLOGGER_RSS_BASE)
    
    # 1. Тест всех постов (без метки)
    print("\n1. Тест: ВСЕ ПОСТЫ (без метки)")
    all_posts = fetcher.fetch_posts(label=None, max_results=3)
    print(f"   Получено: {len(all_posts)} постов")
    for i, post in enumerate(all_posts[:3], 1):
        print(f"   {i}. {post['title'][:60]}...")
    
    # 2. Тест по конфигу
    print("\n2. Тест: ПО КОНФИГУРАЦИИ")
    for blog in BLOGS:
        print(f"\n   Блог: {blog['name']}")
        print(f"   Метка: {blog['label'] or '(все)'}")
        
        posts = fetcher.fetch_posts(label=blog['label'], max_results=2)
        print(f"   Найдено: {len(posts)} постов")
        
        if posts:
            for i, post in enumerate(posts, 1):
                print(f"   {i}. {post['title'][:50]}...")
                print(f"      Метки поста: {', '.join(post['labels'][:3])}")
    
    # 3. Тест доступных меток
    print("\n3. Тест: ПОИСК ДОСТУПНЫХ МЕТОК")
    test_labels = ['zen', 'дзен', 'philosophy', 'философия', 'life', 'искусство']
    
    results = fetcher.test_labels(test_labels)
    
    print("\n   Результаты поиска меток:")
    for label, data in results.items():
        status = "? ДОСТУПНА" if data['available'] else "? НЕДОСТУПНА"
        print(f"    {label:15} {status:20} постов: {data['post_count']}")
        if data['sample_titles']:
            print(f"      Примеры: {', '.join(data['sample_titles'])}")
    
    print("\n" + "=" * 60)
    print("КАК ИСПОЛЬЗОВАТЬ:")
    print("1. Добавьте метки в config.py в список BLOGS")
    print("2. Метка 'zen' будет фильтровать посты с этой меткой")
    print("3. None = все посты блога")
    print("=" * 60)

if __name__ == "__main__":
    main()