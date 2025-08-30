#!/usr/bin/env python3
"""
RSS Feed Importer for Quartz
Imports blog posts from RSS feed and converts them to markdown files
"""

import requests
import xml.etree.ElementTree as ET
import os
import re
import html
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, unquote
import hashlib

class RSSImporter:
    def __init__(self, rss_url, content_dir):
        self.rss_url = rss_url
        self.content_dir = Path(content_dir)
        self.posts_dir = self.content_dir / "Posts"
        self.posts_dir.mkdir(exist_ok=True)
        
    def fetch_rss(self):
        """Fetch and parse the RSS feed"""
        try:
            response = requests.get(self.rss_url, timeout=30)
            response.raise_for_status()
            return ET.fromstring(response.text)
        except Exception as e:
            print(f"Error fetching RSS feed: {e}")
            return None
    
    def extract_slug_from_url(self, url):
        """Extract slug from blog post URL"""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        # Get the last part of the path (the slug)
        slug = path.split('/')[-1]
        
        # Clean the slug
        slug = re.sub(r'[^\w\-]', '', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        
        return slug if slug else 'untitled'
    
    def html_to_markdown(self, html_content):
        """Convert HTML content to markdown (basic conversion)"""
        if not html_content:
            return ""
        
        # Decode HTML entities
        content = html.unescape(html_content)
        
        # Remove script and style tags
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Convert common HTML tags to markdown
        conversions = [
            (r'<h1[^>]*>(.*?)</h1>', r'# \1'),
            (r'<h2[^>]*>(.*?)</h2>', r'## \1'),
            (r'<h3[^>]*>(.*?)</h3>', r'### \1'),
            (r'<h4[^>]*>(.*?)</h4>', r'#### \1'),
            (r'<h5[^>]*>(.*?)</h5>', r'##### \1'),
            (r'<h6[^>]*>(.*?)</h6>', r'###### \1'),
            (r'<strong[^>]*>(.*?)</strong>', r'**\1**'),
            (r'<b[^>]*>(.*?)</b>', r'**\1**'),
            (r'<em[^>]*>(.*?)</em>', r'*\1*'),
            (r'<i[^>]*>(.*?)</i>', r'*\1*'),
            (r'<code[^>]*>(.*?)</code>', r'`\1`'),
            (r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'[\2](\1)'),
            (r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>', r'![\2](\1)'),
            (r'<img[^>]*src=["\']([^"\']*)["\'][^>]*/?>', r'![](\1)'),
            (r'<br[^>]*/?>', r'\n'),
            (r'<hr[^>]*/?>', r'\n---\n'),
            (r'<blockquote[^>]*>(.*?)</blockquote>', r'> \1'),
            (r'<ul[^>]*>(.*?)</ul>', r'\1'),
            (r'<ol[^>]*>(.*?)</ol>', r'\1'),
            (r'<li[^>]*>(.*?)</li>', r'- \1\n'),
            (r'<p[^>]*>(.*?)</p>', r'\1\n\n'),
            (r'<div[^>]*>(.*?)</div>', r'\1\n'),
        ]
        
        for pattern, replacement in conversions:
            content = re.sub(pattern, replacement, content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove remaining HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Clean up whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = content.strip()
        
        return content
    
    def create_frontmatter(self, item):
        """Create frontmatter for the markdown file"""
        title = item.find('title')
        title = title.text if title is not None else 'Untitled'
        
        description = item.find('description')
        description = description.text if description is not None else ''
        description = html.unescape(description)
        # Truncate description if too long
        if len(description) > 200:
            description = description[:200] + '...'
        
        pub_date = item.find('pubDate')
        date_str = ''
        if pub_date is not None:
            try:
                # Parse RFC 2822 date format
                date_obj = datetime.strptime(pub_date.text, '%a, %d %b %Y %H:%M:%S %Z')
                date_str = date_obj.strftime('%Y-%m-%d')
            except:
                try:
                    # Try alternative format
                    date_obj = datetime.strptime(pub_date.text[:25], '%a, %d %b %Y %H:%M:%S')
                    date_str = date_obj.strftime('%Y-%m-%d')
                except:
                    date_str = datetime.now().strftime('%Y-%m-%d')
        
        author = item.find('author')
        author = author.text if author is not None else 'Aryan Techie'
        if '(' in author and ')' in author:
            # Extract name from "email (Name)" format
            author = re.search(r'\((.*?)\)', author)
            author = author.group(1) if author else 'Aryan Techie'
        
        link = item.find('link')
        original_url = link.text if link is not None else ''
        
        categories = []
        for category in item.findall('category'):
            if category.text and category.text.lower() != 'blog':
                categories.append(category.text)
        
        frontmatter = f"""---
title: "{title}"
description: "{description}"
date: {date_str}
author: {author}
tags: {categories}
original_url: {original_url}
imported: true
---

"""
        return frontmatter
    
    def process_item(self, item):
        """Process a single RSS item"""
        link = item.find('link')
        if link is None:
            print("Skipping item without link")
            return False
        
        url = link.text
        slug = self.extract_slug_from_url(url)
        filename = f"{slug}.md"
        filepath = self.posts_dir / filename
        
        # Check if file exists and get its hash to detect changes
        file_exists = filepath.exists()
        existing_hash = None
        
        if file_exists:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                    # Extract the content part (after frontmatter)
                    if '---\n' in existing_content:
                        parts = existing_content.split('---\n', 2)
                        if len(parts) >= 3:
                            existing_content_only = parts[2]
                            existing_hash = hashlib.md5(existing_content_only.encode()).hexdigest()
            except Exception as e:
                print(f"Error reading existing file {filepath}: {e}")
        
        # Get content
        content_element = item.find('{http://purl.org/rss/1.0/modules/content/}encoded')
        if content_element is not None and content_element.text:
            content = self.html_to_markdown(content_element.text)
        else:
            description = item.find('description')
            content = self.html_to_markdown(description.text if description is not None else '')
        
        # Calculate new content hash
        new_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Skip if content hasn't changed
        if file_exists and existing_hash == new_hash:
            print(f"No changes detected for: {filename}")
            return True
        
        # Create frontmatter
        frontmatter = self.create_frontmatter(item)
        
        # Combine frontmatter and content
        full_content = frontmatter + content
        
        # Write file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            action = "Updated" if file_exists else "Created"
            print(f"{action}: {filename}")
            return True
            
        except Exception as e:
            print(f"Error writing file {filepath}: {e}")
            return False
    
    def import_posts(self):
        """Import all posts from the RSS feed"""
        print(f"Fetching RSS feed from: {self.rss_url}")
        root = self.fetch_rss()
        
        if root is None:
            return False
        
        items = root.findall('.//item')
        print(f"Found {len(items)} items in RSS feed")
        
        success_count = 0
        for item in items:
            if self.process_item(item):
                success_count += 1
        
        print(f"\nImport complete: {success_count}/{len(items)} posts processed successfully")
        return True

def main():
    """Main function to run the importer"""
    # Configuration
    RSS_URL = "https://aryantechie.com/api/rss"
    CONTENT_DIR = "content"  # Relative to script location
    
    # Get the directory of this script
    script_dir = Path(__file__).parent
    content_path = script_dir.parent / CONTENT_DIR
    
    print("RSS Feed Importer for Quartz")
    print("=" * 40)
    
    importer = RSSImporter(RSS_URL, content_path)
    success = importer.import_posts()
    
    if success:
        print("\n✅ Import completed successfully!")
        print(f"Posts saved to: {importer.posts_dir}")
    else:
        print("\n❌ Import failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())