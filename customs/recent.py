from pathlib import Path
import re
from datetime import datetime
import sys

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "content" / "posts"
INDEX_PATH = ROOT / "content" / "index.md"

# Slugify helper
def slugify(name: str) -> str:
    return name.lower().replace(" ", "-")

# Get latest posts (title from line 1 or filename fallback)
def get_latest_posts(limit=5):
    posts = []
    for post_file in POSTS_DIR.glob("*.md"):
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
            posts.append((date, post_file.name, title))
        except Exception as e:
            print(f"⚠️ Error reading {post_file.name}: {e}")
    posts.sort(reverse=True)
    return posts[:limit] if limit else posts


# Inject recent posts into index.md using markers
def update_index_md(limit=5):
    posts = get_latest_posts(limit)
    recent_md = "\n".join([
    "> [!abstract] Recent Posts"
] + [
    f" > - [{title}](/posts/{slugify(Path(file).stem)})"
    for _, file, title in posts
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
    print("✅ index.md updated with latest posts.")

# Run
import sys

if __name__ == "__main__":
    try:
        limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    except ValueError:
        print("⚠️ Invalid limit argument. Using default of 5.")
        limit = 5

    update_index_md(limit=limit)
