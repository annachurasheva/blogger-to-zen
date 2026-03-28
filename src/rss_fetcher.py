import feedparser
import logging
from urllib.parse import quote, unquote, urlparse

logger = logging.getLogger(__name__)

class BloggerRSSFetcher:
    def __init__(self, base_url: str):
        logger.info(f"BloggerRSSFetcher init: base_url='{base_url}'")
        # Ensure we have the proper Blogger RSS feed URL
        # If user provides blog URL like https://blog.example.com,
        # convert it to https://blog.example.com/feeds/posts/default
        parsed = urlparse(base_url)
        if not parsed.path.endswith('/feeds/posts/default'):
            # Add the feeds path if not present
            self.base_url = base_url.rstrip('/') + '/feeds/posts/default'
        else:
            self.base_url = base_url.rstrip('/')
        logger.info(f"Using RSS feed base URL: {self.base_url}")

    def fetch_posts(self, label: str = None, max_results: int = 10):
        """Получает посты из Blogger с поддержкой меток"""
        try:
            if label:
                # Decode URL-encoded label if needed, then re-encode properly
                decoded_label = unquote(label)
                encoded_label = quote(decoded_label, safe='')
                url = f"{self.base_url}?alt=rss&max-results={max_results}&q=label:{encoded_label}"
            else:
                url = f"{self.base_url}?alt=rss&max-results={max_results}"

            logger.info(f"Fetching RSS URL: {url}")
            feed = feedparser.parse(url)

            if feed.bozo:
                logger.warning(f"RSS parsing error: {feed.bozo_exception}")
                return []

            # Check if we got any entries
            if not feed.entries:
                logger.warning("No entries in RSS feed")
                return []

            posts = []
            for entry in feed.entries:
                post = {
                    'id': entry.get('id', ''),
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'content': self._extract_content(entry),
                    'summary': entry.get('summary', ''),
                    'published': entry.get('published', ''),
                    'author': entry.get('author', ''),
                    'labels': [tag.term for tag in entry.get('tags', [])]
                }
                posts.append(post)

            logger.info(f"Получено {len(posts)} постов" + (f" с меткой '{label}'" if label else ""))
            return posts
        except Exception as e:
            logger.error(f"Error fetching posts: {e}")
            return []

    def _extract_content(self, entry):
        """Извлекает основной контент из поста"""
        if 'content' in entry and entry.content:
            for content in entry.content:
                if content.value:
                    return content.value
        return entry.get('summary', '')