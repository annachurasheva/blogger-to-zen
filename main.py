#!/usr/bin/env python3
"""
ПЕРВЫЙ РАБОЧИЙ ШАГ: Сбор постов о розах как лекарстве
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime

# Добавляем пути
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Импортируем НАШИ модули
try:
    from config import BLOGGER_RSS_BASE, BLOGS, CONTENT
    from src.rss_fetcher import BloggerRSSFetcher
    from src.content_processor import ContentProcessor
    from src.youtube_replacer import YouTubeReplacer
    from src.zen_tagger import ZenTagger
except ImportError as e:
    print(f"❌ ОШИБКА ИМПОРТА: {e}")
    print("Создайте недостающие файлы в папке src/")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FirstStepPipeline:
    """
    ПЕРВЫЙ ШАГ: Собрать посты о лечебных свойствах роз
    для бабушек и их внуков
    """
    def __init__(self):
        self.fetcher = BloggerRSSFetcher(BLOGGER_RSS_BASE)
        self.processor = ContentProcessor()
        self.youtube_replacer = YouTubeReplacer()
        self.zen_tagger = ZenTagger()
        
        # Папки для данных
        self.data_dir = 'data'
        self.archive_dir = os.path.join(self.data_dir, 'archive')
        self.schedule_file = os.path.join(self.data_dir, 'schedule.json')
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        os.makedirs('output_samples', exist_ok=True)
    
    def run_first_step(self):
        """Запуск первого шага: сбор и подготовка"""
        logger.info("=" * 60)
        logger.info("ШАГ 1: СОБИРАЕМ ЗНАНИЯ О ЛЕЧЕБНЫХ РОЗАХ")
        logger.info("=" * 60)
        
        all_medical_posts = []
        
        # Собираем посты по КЛЮЧЕВЫМ меткам для здоровья
        health_labels = ['Centifolia', 'шиповник', 'рецепт', 'масло']
        
        for label in health_labels:
            logger.info(f"🔍 Ищем посты о здоровье: метка '{label}'")
            
            posts = self.fetcher.fetch_posts(label=label, max_results=5)
            
            for post in posts:
                # АКЦЕНТИРУЕМ на лечебных свойствах
                medical_post = self._add_medical_context(post)
                
                # Обрабатываем контент
                processed = self.processor.process(medical_post)
                
                # Заменяем YouTube на Rutube (ВАЖНО для РФ)
                if CONTENT['replace_youtube']:
                    processed['content'] = self.youtube_replacer.replace(
                        processed['content']
                    )
                
                # Добавляем теги для Дзен с акцентом на здоровье
                processed['zen_tags'] = self.zen_tagger.generate_tags(
                    processed.get('labels', []),
                    processed.get('content', '')
                )
                
                # Добавляем ЦЕЛЬ поста (для бабушек и внуков)
                processed['purpose'] = self._define_purpose(processed)
                
                all_medical_posts.append(processed)
                
                logger.info(f"  ✅ {processed['title'][:50]}...")
                logger.info(f"     Цель: {processed['purpose']}")
        
        if not all_medical_posts:
            logger.warning("⚠️  Не найдено постов о лечебных свойствах роз")
            # Пробуем все посты
            logger.info("Пробуем получить все посты...")
            all_posts = self.fetcher.fetch_posts(label=None, max_results=10)
            for post in all_posts:
                processed = self.processor.process(post)
                all_medical_posts.append(processed)
        
        # Сохраняем результат
        self._save_first_step_results(all_medical_posts)
        
        # Создаём план публикаций
        publication_plan = self._create_publication_plan(all_medical_posts)
        
        logger.info("=" * 60)
        logger.info(f"ШАГ 1 ЗАВЕРШЁН!")
        logger.info(f"Найдено постов о лечебных розах: {len(all_medical_posts)}")
        logger.info(f"Запланировано публикаций: {len(publication_plan)}")
        logger.info("=" * 60)
        
        return all_medical_posts, publication_plan
    
    def run_test_step(self, label, max_results=50):
        """Тестовый запуск: сбор постов по одной указанной метке"""
        logger.info("=" * 60)
        logger.info(f"ТЕСТОВЫЙ ЗАПУСК: метка '{label}'")
        logger.info("=" * 60)
        
        all_posts = []
        
        logger.info(f"🔍 Ищем посты с меткой '{label}' (до {max_results} постов)")
        
        posts = self.fetcher.fetch_posts(label=label, max_results=max_results)
        
        for post in posts:
            # Обрабатываем контент
            processed = self.processor.process(post)
            
            # Заменяем YouTube на Rutube (ВАЖНО для РФ)
            if CONTENT['replace_youtube']:
                processed['content'] = self.youtube_replacer.replace(
                    processed['content']
                )
            
            # Добавляем теги для Дзен
            processed['zen_tags'] = self.zen_tagger.generate_tags(
                processed.get('labels', []),
                processed.get('content', '')
            )
            
            # Определяем цель поста
            processed['purpose'] = self._define_purpose(processed)
            
            all_posts.append(processed)
            
            logger.info(f"  ✅ {processed['title'][:50]}...")
            logger.info(f"     Цель: {processed['purpose']}")
        
        # Создаем папку для метки
        label_dir = os.path.join('output_samples', label)
        os.makedirs(label_dir, exist_ok=True)
        
        # Сохраняем результат тестового сбора
        test_file = os.path.join(label_dir, f'posts_{datetime.now().strftime("%Y%m%d_%H%M")}.json')
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(all_posts, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Тестовые посты сохранены: {test_file}")
        
        # Создаём простой HTML для просмотра
        html_content = self._generate_html_preview(all_posts)
        html_file = os.path.join(label_dir, f'preview_{datetime.now().strftime("%Y%m%d_%H%M")}.html')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"👁️  Визуальный просмотр: {html_file}")
        
        logger.info("=" * 60)
        logger.info(f"ТЕСТОВЫЙ ЗАПУСК ЗАВЕРШЁН!")
        logger.info(f"Найдено постов: {len(all_posts)}")
        logger.info("=" * 60)
        
        return all_posts
    
    def _add_medical_context(self, post):
        """Добавляем медицинский контекст к посту"""
        post = post.copy()
        
        # Добавляем ключевые фразы для бабушек
        medical_keywords = [
            "здоровье внуков",
            "гормоны счастья", 
            "регенерация сосудов",
            "ароматерапия для детей",
            "лекарственное растение"
        ]
        
        # Добавляем в контент если нет
        content_lower = post.get('content', '').lower() + post.get('title', '').lower()
        
        for keyword in medical_keywords:
            if keyword not in content_lower:
                if 'content' in post:
                    post['content'] = f"<p><strong>Для здоровья ваших внуков:</strong> {keyword}.</p>\n" + post['content']
        
        return post
    
    def _define_purpose(self, post):
        """Определяет цель поста в нашей миссии"""
        title_lower = post.get('title', '').lower()
        content_lower = post.get('content', '').lower()
        
        if any(word in title_lower for word in ['масло', 'шиповник']):
            return "Уход за кожей для бабушек и молодость внуков"
        elif any(word in content_lower for word in ['чай', 'напиток', 'шарбат']):
            return "Напиток счастья для семейного здоровья"
        elif 'centifolia' in title_lower.lower():
            return "Лекарственная роза для регенерации сосудов"
        elif 'рецепт' in title_lower:
            return "Кулинария здоровья для поколений"
        else:
            return "Знания о розах для семейного благополучия"
    
    def _save_first_step_results(self, posts):
        """Сохраняет результаты первого шага"""
        # 1. JSON со всеми постами
        posts_file = os.path.join('output_samples', f'medical_posts_{datetime.now().strftime("%Y%m%d_%H%M")}.json')
        
        with open(posts_file, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Посты сохранены: {posts_file}")
        
        # 2. HTML для визуальной проверки
        html_file = os.path.join('output_samples', f'preview_{datetime.now().strftime("%Y%m%d_%H%M")}.html')
        
        html_content = self._generate_html_preview(posts)
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"👁️  Визуальный просмотр: {html_file}")
        
        # 3. Короткий отчет
        report_file = os.path.join('output_samples', 'first_step_report.txt')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("ОТЧЁТ: ПЕРВЫЙ ШАГ - СБОР ЗНАНИЙ О ЛЕЧЕБНЫХ РОЗАХ\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Найдено постов: {len(posts)}\n\n")
            
            f.write("ТЕМАТИКИ ПОСТОВ:\n")
            purposes = {}
            for post in posts:
                purpose = post.get('purpose', 'без категории')
                purposes[purpose] = purposes.get(purpose, 0) + 1
            
            for purpose, count in purposes.items():
                f.write(f"  • {purpose}: {count} постов\n")
            
            f.write("\nСЛЕДУЮЩИЕ ШАГИ:\n")
            f.write("1. Проверить output_samples/*.html\n")
            f.write("2. Настроить Telegram бота\n")
            f.write("3. Запустить публикации\n")
        
        logger.info(f"📊 Отчёт сохранён: {report_file}")
    
    def _generate_html_preview(self, posts):
        """Генерирует HTML для визуального просмотра"""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ПРЕДПРОСМОТР: Лечебные розы для бабушек и внуков</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .post { border: 1px solid #e0e0e0; padding: 20px; margin: 20px 0; border-radius: 10px; }
        .title { color: #c2185b; font-size: 24px; margin-bottom: 10px; }
        .purpose { background: #f3e5f5; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .tags { color: #666; font-size: 14px; }
        .content { margin: 15px 0; line-height: 1.6; }
        .meta { color: #999; font-size: 12px; }
    </style>
</head>
<body>
    <h1>🌹 ПОСТЫ О ЛЕЧЕБНЫХ РОЗАХ</h1>
    <p>Цель: дать бабушкам знания для здоровья внуков</p>
    <hr>
"""
        
        for i, post in enumerate(posts, 1):
            html += f"""
    <div class="post">
        <div class="title">{i}. {post.get('title', 'Без названия')}</div>
        <div class="purpose"><strong>Цель:</strong> {post.get('purpose', '')}</div>
        <div class="tags"><strong>Теги Дзен:</strong> {', '.join(post.get('zen_tags', [])[:8])}</div>
        <div class="content">{post.get('content', '')[:500]}...</div>
        <div class="meta">
            <strong>Источник:</strong> {post.get('link', '')} |
            <strong>Метки:</strong> {', '.join(post.get('labels', [])[:5])}
        </div>
    </div>
"""
        
        html += """
</body>
</html>"""
        
        return html
    
    def _create_publication_plan(self, posts):
        """Создаёт план публикаций с учётом шортов"""
        # Читаем шорты из файла
        shorts = []
        if os.path.exists('shorts_list.txt'):
            with open('shorts_list.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        shorts.append(line)
        
        logger.info(f"📹 Найдено шортов: {len(shorts)}")
        
        # Чередуем посты и шорты
        plan = []
        post_index = 0
        short_index = 0
        
        # Первые 7 дней (по 2 публикации в день)
        for day in range(7):
            # Утро: пост о лечебных свойствах
            if post_index < len(posts):
                post = posts[post_index]
                plan.append({
                    'type': 'post',
                    'data': post,
                    'time': f"10:00",
                    'day': day + 1,
                    'purpose': post.get('purpose', '')
                })
                post_index += 1
            
            # Вечер: шорт
            if short_index < len(shorts):
                plan.append({
                    'type': 'short',
                    'data': shorts[short_index],
                    'time': f"18:00",
                    'day': day + 1,
                    'purpose': "Кратковременная мотивация о пользе роз"
                })
                short_index += 1
        
        # Сохраняем план
        plan_file = os.path.join(self.data_dir, 'publication_plan.json')
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📅 План публикаций сохранён: {plan_file}")
        
        return plan

def main():
    """Запуск первого шага"""
    import sys
    # Настройка кодировки вывода для Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    parser = argparse.ArgumentParser(description='Сбор постов с Blogger')
    parser.add_argument('--label', '-l', help='Метка для тестового сбора (например, "Проект R")')
    args = parser.parse_args()
    
    print("=" * 60)
    print("ПЕРВЫЙ ШАГ: СОЗДАНИЕ БАЗЫ ЗНАНИЙ")
    print("О лечебных розах для бабушек и их внуков")
    print("=" * 60)
    
    try:
        pipeline = FirstStepPipeline()
        if args.label:
            # Тестовый режим: собираем только по одной указанной метке
            posts = pipeline.run_test_step(label=args.label, max_results=2)
            plan = []
        else:
            posts, plan = pipeline.run_first_step()
        
        print("\n✅ ЧТО СДЕЛАНО:")
        print(f"1. Найдено {len(posts)} постов о лечебных свойствах роз")
        print(f"2. Создан план на {len(plan)} публикаций")
        print(f"3. Файлы сохранены в папке output_samples/")
        
        print("\n📁 ПРОВЕРЬТЕ ФАЙЛЫ:")
        print("• output_samples/*.html - визуальный просмотр постов")
        print("• output_samples/*.json - данные постов")
        print("• output_samples/first_step_report.txt - отчёт")
        print("• data/publication_plan.json - план публикаций")
        
        print("\n🎯 СЛЕДУЮЩИЙ ШАГ:")
        print("1. Проверить HTML-просмотр постов")
        print("2. Настроить Telegram бота (завтра)")
        print("3. Начать публикации по плану")
        
    except Exception as e:
        logger.error(f"❌ ОШИБКА: {e}", exc_info=True)
        print(f"\n❌ Ошибка: {e}")
        print("Проверьте наличие всех файлов в src/")

if __name__ == "__main__":
    main()