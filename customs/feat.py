import frontmatter
from pathlib import Path
from datetime import datetime
from urllib.parse import quote
import re

ROOT = Path(__file__).resolve().parents[1]
POSTS_FOLDER = ROOT / "content" / "posts"
INDEX_PATH = ROOT / "content" / "index.md"

def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_]+", "-", text).strip("-")

def find_featured_post():
    posts = []
    for file in POSTS_FOLDER.rglob("*.md"):
        try:
            post = frontmatter.load(file)
            title = post.get("title", file.stem.replace("-", " ").title())
            date_str = post.get("date")
            date = datetime.fromisoformat(str(date_str)) if date_str else datetime.fromtimestamp(file.stat().st_mtime)
            is_featured = post.get("featured", False)

            # Get relative path from posts folder
            rel_path = file.relative_to(POSTS_FOLDER).parent
            if rel_path == Path('.'):  # If file is directly in posts folder
                slug_path = file.stem
            else:
                slug_path = f"{rel_path}/{file.stem}"
                
            posts.append((is_featured, date, title, slug_path))
        except Exception as e:
            print(f"⚠️ Skipped {file.name}: {e}")
            continue

    # Priority 1: First featured post
    for post in sorted(posts, key=lambda x: x[1], reverse=True):
        if post[0]:  # is_featured
            return post[2], post[3]  # title, slug

    # Fallback: Most recent post
    if posts:
        most_recent = max(posts, key=lambda x: x[1])
        return most_recent[2], most_recent[3]

    return None, None

def inject_featured_post():
    if not INDEX_PATH.exists():
        print("❌ index.md not found.")
        return

    content = INDEX_PATH.read_text(encoding="utf-8")
    lines = content.splitlines()  # ← Add this line to define 'lines'
    title, slug = find_featured_post()

    if not title:
        featured_md = "_No featured post available yet._"
    else:

        # Load the actual post content to extract the first paragraph
        post_path = next((p for p in POSTS_FOLDER.rglob("*.md") if p.stem == slug), None)
        excerpt = ""

        if post_path and post_path.exists():
            with open(post_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        # Find the first non-empty line after frontmatter
        in_frontmatter = False
        callout_prefixes = tuple(["> [!", ">[!"])  # Obsidian-style callouts
        for line in lines:
            if line.strip() == "---":
                in_frontmatter = not in_frontmatter
                continue
            if not in_frontmatter:
                clean = line.strip()
                if clean and not clean.startswith(callout_prefixes):
                    # Remove '>' if it's a simple blockquote
                    excerpt = clean.lstrip("> ").strip()
                    break


        excerpt = excerpt or "_No excerpt available._"

        featured_md = f"""> [!feat] Featured Post
> ## [{title}](/posts/{quote(slug)})
> {excerpt}
> 
> [Read more →](/posts/{quote(slug)})"""
    pattern = re.compile(r"<!-- start:featured -->(.*?)<!-- end:featured -->", re.DOTALL)
    new_block = f"<!-- start:featured -->\n{featured_md}\n<!-- end:featured -->"
    if pattern.search(content):
        content = pattern.sub(new_block, content)
    else:
        # Append if not present
        content = content + "\n\n" + new_block

    INDEX_PATH.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"✅ Featured section updated with: {title or 'None'}")


if __name__ == "__main__":
    inject_featured_post()
