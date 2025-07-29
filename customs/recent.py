from pathlib import Path
import re
from datetime import datetime
import sys
from urllib.parse import quote  # Add this import at the top

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "content" / "Posts"
INDEX_PATH = ROOT / "content" / "index.md"

# Slugify helper
def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_]+", "-", text).strip("-")

# Get latest Posts (title from line 1 or filename fallback)
def get_latest_Posts(limit=5):
    Posts = []
    for post_file in POSTS_DIR.rglob("*.md"):
        try:
            content = post_file.read_text(encoding="utf-8")
            lines = content.splitlines()
            title = post_file.stem  # fallback
            in_frontmatter = False
            for line in lines:
                if line.strip() == "---":
                    in_frontmatter = not in_frontmatter
                    continue
                if in_frontmatter and line.strip().lower().startswith("title:"):
                    title = line.split(":", 1)[1].strip()
                    break
            date = post_file.stat().st_mtime  # Use last modified time
            # Store the original stem (without lowercasing)
            Posts.append((date, post_file.stem, title))  # Changed from post_file.name to post_file.stem
        except Exception as e:
            print(f"⚠️ Error reading {post_file.name}: {e}")
    Posts.sort(reverse=True)
    return Posts[:limit] if limit else Posts

# Inject recent Posts into index.md using markers
def update_index_md(limit=5):
    Posts = get_latest_Posts(limit)
    recent_md = "\n".join([
    "> [!recent] Recent Posts"
] + [
    # Use URL encoding to handle spaces and special characters
    f" > - [{title}](/Posts/{quote(file)})"  
    for _, file, title in Posts
])

    block = f"<!-- start:recent -->\n{recent_md}\n<!-- end:recent -->"

    if not INDEX_PATH.exists():
        print("❌ index.md not found.")
        return

    content = INDEX_PATH.read_text(encoding="utf-8")

    pattern = re.compile(r"<!-- start:recent -->(.*?)<!-- end:recent -->", re.DOTALL)
    if pattern.search(content):
        content = pattern.sub(block, content)
    else:
        # Append to the end if section doesn't exist
        content += f"\n\n{block}"

    INDEX_PATH.write_text(content.strip() + "\n", encoding="utf-8")
    print("✅ index.md updated with latest Posts.")

# Run
import sys

if __name__ == "__main__":
    try:
        limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    except ValueError:
        print("⚠️ Invalid limit argument. Using default of 5.")
        limit = 5

    update_index_md(limit=limit)
