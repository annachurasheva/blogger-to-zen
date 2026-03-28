#!/usr/bin/env python3
"""
Scraper Script with Menu System
Based on existing BloggerRSSFetcher for integration
"""

import os
import json
import logging
from datetime import datetime
from urllib.parse import urlparse, unquote
from rss_fetcher import BloggerRSSFetcher

# Configure logging
LOG_FILE = os.path.join(os.path.dirname(__file__), "scraper.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
OUTPUT_DIR = "output_samples/Проект R"
LAST_SITE_FILE = "last_site.txt"

class ScraperMenu:
    def __init__(self):
        self.site_address = None
        self.tag = None
        self.fetcher = None
        
    def load_last_site(self):
        """Load last used site address"""
        if os.path.exists(LAST_SITE_FILE):
            try:
                with open(LAST_SITE_FILE, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                logger.warning(f"Error reading last site file: {e}")
        return None
    
    def save_last_site(self, site):
        """Save site address for repeat use"""
        try:
            with open(LAST_SITE_FILE, 'w', encoding='utf-8') as f:
                f.write(site)
        except Exception as e:
            logger.error(f"Error saving last site: {e}")
    
    def create_output_folders(self, site, tag):
        """Create output folders with underscores for spaces in tag"""
        site_folder = site.replace(" ", "_")
        tag_folder = tag.replace(" ", "_")
        full_path = os.path.join(OUTPUT_DIR, site_folder, tag_folder)
        os.makedirs(full_path, exist_ok=True)
        logger.info(f"Created output directory: {full_path}")
        return full_path
    
    def validate_site_address(self, site):
        """Validate site address format"""
        if not site:
            return False, "Site address cannot be empty"
        
        # Basic URL validation
        parsed = urlparse(site)
        if not parsed.scheme or not parsed.netloc:
            return False, "Invalid URL format. Please use http:// or https://"
        
        return True, ""
    
    def validate_tag(self, tag):
        """Validate tag input"""
        if not tag:
            return False, "Tag cannot be empty"
        
        # Remove leading/trailing whitespace
        tag = tag.strip()
        if not tag:
            return False, "Tag cannot be empty after trimming"
        
        return True, ""
    
    def generate_md_file(self, posts, output_path):
        """Generate .md file from posts"""
        md_path = os.path.join(output_path, "index.md")
        try:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# {self.site_address}\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"Tag: {self.tag}\n\n")
                f.write(f"Total posts: {len(posts)}\n\n")
                
                for i, post in enumerate(posts, 1):
                    f.write(f"## {i}. {post['title']}\n\n")
                    f.write(f"**Published:** {post['published']}\n")
                    f.write(f"**Author:** {post['author']}\n")
                    f.write(f"**Labels:** {', '.join(post['labels'])}\n\n")
                    f.write(f"**Content:**\n{post['content']}\n\n")
                    f.write(f"**Link:** {post['link']}\n\n")
                    f.write("---\n\n")
            
            logger.info(f"Generated MD file: {md_path}")
            return md_path
        except Exception as e:
            logger.error(f"Error generating MD file: {e}")
            return None
    
    def generate_json_file(self, posts, output_path):
        """Generate .json file from posts"""
        json_path = os.path.join(output_path, "data.json")
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(posts, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Generated JSON file: {json_path}")
            return json_path
        except Exception as e:
            logger.error(f"Error generating JSON file: {e}")
            return None
    
    def process_site(self):
        """Process the site and tag to generate output files"""
        if not self.site_address or not self.tag:
            logger.error("Site address and tag must be set")
            return False
        
        # Validate inputs
        site_valid, site_msg = self.validate_site_address(self.site_address)
        if not site_valid:
            logger.error(f"Site validation failed: {site_msg}")
            return False
        
        tag_valid, tag_msg = self.validate_tag(self.tag)
        if not tag_valid:
            logger.error(f"Tag validation failed: {tag_msg}")
            return False
        
        try:
            # Decode tag if it's percent-encoded (e.g., from URL input)
            decoded_tag = unquote(self.tag)
            logger.info(f"Using tag: {self.tag} (decoded: {decoded_tag})")
            
            # Initialize fetcher
            self.fetcher = BloggerRSSFetcher(self.site_address)
            
            # Fetch posts
            logger.info(f"Fetching posts from {self.site_address} with tag '{decoded_tag}'")
            posts = self.fetcher.fetch_posts(label=decoded_tag, max_results=100)
            
            if not posts:
                logger.warning("No posts found with the specified tag")
                print("\n⚠️  No posts found with the specified tag.")
                print("   This could be due to:")
                print("   - The tag doesn't exist on this blog")
                print("   - The blog has no posts with this tag")
                print("   - The RSS feed is malformed or inaccessible")
                print("   - Network connectivity issues")
                print("\n   Check the log file (src/scraper.log) for detailed error information.")
                return False
            
            # Create output folders
            output_path = self.create_output_folders(self.site_address, self.tag)
            
            # Generate output files
            md_file = self.generate_md_file(posts, output_path)
            json_file = self.generate_json_file(posts, output_path)
            
            if md_file and json_file:
                logger.info(f"Successfully processed {len(posts)} posts")
                print(f"\n✅ Successfully processed {len(posts)} posts")
                print(f"📁 Folder: {output_path}")
                print(f"📄 MD file: {md_file}")
                print(f"📄 JSON file: {json_file}")
                return True
            else:
                logger.error("Failed to generate output files")
                return False
                
        except Exception as e:
            logger.error(f"Error processing site: {e}")
            print(f"\n❌ Error: {e}")
            return False
    
    def show_menu(self):
        """Display menu and handle user input"""
        print("\n" + "="*50)
        print("SCRAPER MENU")
        print("="*50)
        
        # Load last site if available
        last_site = self.load_last_site()
        if last_site:
            print(f"Last site: {last_site}")
        
        print("\n1. Enter site address")
        print("2. Enter tag")
        print("3. Process")
        print("4. Exit")
        
        try:
            choice = input("\nSelect option (1-4): ").strip()
            logger.info(f"User selected menu option: {choice}")
        except EOFError:
            logger.error("EOFError: No input available")
            return False
        
        if choice == '1':
            # Enter site address
            if last_site:
                use_last = input(f"Use last site address '{last_site}'? (y/n): ").strip().lower()
                logger.info(f"User decided to {'use' if use_last == 'y' else 'enter new'} site address")
                if use_last == 'y':
                    self.site_address = last_site
                    print(f"Site address: {self.site_address}")
                else:
                    new_site = input("Enter new site address: ").strip()
                    if new_site:
                        self.site_address = new_site
                        print(f"Site address: {self.site_address}")
                    else:
                        print("Site address cannot be empty")
            else:
                new_site = input("Enter site address: ").strip()
                if new_site:
                    self.site_address = new_site
                    print(f"Site address: {self.site_address}")
                else:
                    print("Site address cannot be empty")
        
        elif choice == '2':
            # Enter tag
            tag = input("Enter tag: ").strip()
            logger.info(f"User entered tag: {tag}")
            if tag:
                self.tag = tag
                print(f"Tag: {self.tag}")
            else:
                print("Tag cannot be empty")
        
        elif choice == '3':
            # Process
            if not self.site_address:
                print("Please enter site address first")
                logger.warning("Attempted to process without site address")
            elif not self.tag:
                print("Please enter tag first")
                logger.warning("Attempted to process without tag")
            else:
                success = self.process_site()
                if success:
                    # Save site for repeat
                    self.save_last_site(self.site_address)
                    logger.info("Processing completed successfully")
        
        elif choice == '4':
            # Exit
            print("Exiting program...")
            logger.info("User exited the program")
            return False
        
        else:
            print("Invalid choice")
            logger.warning(f"Invalid menu choice: {choice}")
        
        return True
    
    def run(self):
        """Main run loop"""
        print("Starting Scraper...")
        logger.info("Scraper started")
        
        while True:
            try:
                if not self.show_menu():
                    break
            except KeyboardInterrupt:
                print("\nProgram interrupted by user")
                logger.info("Program interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                print(f"Error: {e}")
        
        print("Program finished")
        logger.info("Scraper finished")

def main():
    """Main entry point"""
    menu = ScraperMenu()
    menu.run()

if __name__ == "__main__":
    main()
