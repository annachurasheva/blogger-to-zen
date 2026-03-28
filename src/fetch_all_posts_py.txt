#!/usr/bin/env python3
"""
Test Script: Fetch all posts without label filtering
Algorithm:
1. Check if site is accessible and get post count
2. Show count to user
3. Ask user to continue and enter output folder
4. Save posts to folder (md + json)
5. Repeat/Close option
"""

import os
import json
import logging
from datetime import datetime
from urllib.parse import urlparse
from rss_fetcher import BloggerRSSFetcher

# Configure logging
LOG_FILE = os.path.join(os.path.dirname(__file__), "fetch_all_posts.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FetchAllPosts:
    def __init__(self):
        self.site_address = None
        self.fetcher = None
        
    def validate_site_address(self, site):
        """Validate site address format"""
        if not site:
            return False, "Site address cannot be empty"
        parsed = urlparse(site)
        if not parsed.scheme or not parsed.netloc:
            return False, "Invalid URL format. Please use http:// or https://"
        return True, ""
    
    def check_site_accessibility(self, site):
        """Check if site is accessible and get post count"""
        try:
            self.fetcher = BloggerRSSFetcher(site)
            # Try to fetch a small number first to check accessibility
            posts = self.fetcher.fetch_posts(label=None, max_results=10)
            if posts:
                logger.info(f"Site is accessible. Sample fetch returned {len(posts)} posts")
                return True, len(posts)
            else:
                logger.warning("Site returned no posts in sample fetch")
                return True, 0
        except Exception as e:
            logger.error(f"Error checking site accessibility: {e}")
            return False, 0
    
    def get_output_folder(self):
        """Ask user for output folder"""
        print("\nEnter output folder path (relative or absolute):")
        folder = input("Folder: ").strip()
        if not folder:
            print("ERROR: Folder cannot be empty")
            return None
        return folder
    
    def create_output_folders(self, base_folder, site):
        """Create output folders with underscores for spaces in site name"""
        site_folder = site.replace(" ", "_").replace("/", "_").replace(":", "")
        full_path = os.path.join(base_folder, site_folder)
        os.makedirs(full_path, exist_ok=True)
        logger.info(f"Created output directory: {full_path}")
        return full_path
    
    def generate_md_file(self, posts, output_path):
        """Generate .md file from posts"""
        md_path = os.path.join(output_path, "all_posts.md")
        try:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# All Posts from {self.site_address}\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
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
        json_path = os.path.join(output_path, "all_posts.json")
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(posts, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Generated JSON file: {json_path}")
            return json_path
        except Exception as e:
            logger.error(f"Error generating JSON file: {e}")
            return None
    
    def fetch_all_posts(self, max_results=500):
        """Fetch all posts from the site"""
        try:
            logger.info(f"Fetching all posts from {self.site_address}")
            posts = self.fetcher.fetch_posts(label=None, max_results=max_results)
            logger.info(f"Fetched {len(posts)} posts")
            return posts
        except Exception as e:
            logger.error(f"Error fetching all posts: {e}")
            return []
    
    def run(self):
        """Main run loop"""
        print("=== Fetch All Posts Test Script ===\n")
        logger.info("Fetch All Posts script started")
        
        while True:
            try:
                print("\n" + "="*50)
                print("1. Enter site address")
                print("2. Check site accessibility")
                print("3. Exit")
                choice = input("\nSelect option (1-3): ").strip()
                
                if choice == '1':
                    site = input("Enter site address: ").strip()
                    valid, msg = self.validate_site_address(site)
                    if not valid:
                        print(f"ERROR: {msg}")
                        continue
                    self.site_address = site
                    print(f"Site address set: {self.site_address}")
                
                elif choice == '2':
                    if not self.site_address:
                        print("ERROR: Please enter site address first")
                        continue
                    
                    print(f"Checking accessibility of {self.site_address}...")
                    accessible, sample_count = self.check_site_accessibility(self.site_address)
                    
                    if accessible:
                        print(f"\nSUCCESS: Site is accessible!")
                        print(f"   Sample fetch (10 posts) returned: {sample_count} posts")
                        
                        # Ask if user wants to continue
                        continue_choice = input("\nDo you want to fetch ALL posts? (y/n): ").strip().lower()
                        if continue_choice == 'y':
                            # Get output folder
                            output_folder = self.get_output_folder()
                            if not output_folder:
                                continue
                            
                            # Create site-specific subfolder
                            site_folder = self.create_output_folders(output_folder, self.site_address)
                            
                            # Fetch all posts
                            print("\nFetching all posts...")
                            all_posts = self.fetch_all_posts(max_results=500)
                            
                            if all_posts:
                                # Generate files
                                md_file = self.generate_md_file(all_posts, site_folder)
                                json_file = self.generate_json_file(all_posts, site_folder)
                                
                                if md_file and json_file:
                                    print(f"\nSUCCESS: Saved {len(all_posts)} posts")
                                    print(f"Folder: {site_folder}")
                                    print(f"MD file: {md_file}")
                                    print(f"JSON file: {json_file}")
                                else:
                                    print("ERROR: Failed to generate output files")
                            else:
                                print("ERROR: No posts fetched")
                        else:
                            print("Operation cancelled")
                    else:
                        print("ERROR: Site is not accessible or returned no posts")
                
                elif choice == '3':
                    print("Exiting program...")
                    logger.info("User exited the program")
                    break
                
                else:
                    print("Invalid choice")
                    
            except KeyboardInterrupt:
                print("\n\nProgram interrupted by user")
                logger.info("Program interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                print(f"Error: {e}")
        
        print("Program finished")
        logger.info("Fetch All Posts script finished")

def main():
    """Main entry point"""
    app = FetchAllPosts()
    app.run()

if __name__ == "__main__":
    main()