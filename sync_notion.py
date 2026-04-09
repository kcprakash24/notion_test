import os
import re
import requests
from notion_client import Client

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
OUTPUT_DIR = "blogs"

notion = Client(auth=NOTION_TOKEN)

def download_image(url: str, assets_dir: str) -> str:
    os.makedirs(assets_dir, exist_ok=True)
    filename = url.split("/")[-1].split("?")[0]
    if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        filename += ".png"
    filepath = os.path.join(assets_dir, filename)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    with open(filepath, "wb") as f:
        f.write(response.content)
    return f"./assets/{filename}"

def slugify(title: str) -> str:
    title = title.lower().strip()
    title = re.sub(r"[^\w\s-]", "", title)
    title = re.sub(r"[\s_-]+", "-", title)
    return title


def get_live_pages() -> list:
    pages = []
    cursor = None

    while True:
        kwargs = {
            "database_id": NOTION_DATABASE_ID,
            "filter": {"property": "Status", "status": {"equals": "Live"}},
        }
        if cursor:
            kwargs["start_cursor"] = cursor

        response = notion.databases.query(**kwargs)
        pages.extend(response["results"])

        if response["has_more"]:
            cursor = response["next_cursor"]
        else:
            break

    return pages


def get_title(page: dict) -> str:
    for prop in page["properties"].values():
        if prop["type"] == "title":
            parts = prop["title"]
            if parts:
                return parts[0]["plain_text"]
    return page["id"]


def get_slug(page: dict) -> str:
    slug_prop = page["properties"].get("Slug", {})
    rich = slug_prop.get("rich_text", [])
    if rich:
        return rich[0]["plain_text"].strip()
    return slugify(get_title(page))


def block_to_md(block: dict, assets_dir: str = None) -> str:

    t = block["type"]
    b = block[t]

    def rich_text(rt_list):
        result = ""
        for rt in rt_list:
            text = rt["plain_text"]
            ann = rt.get("annotations", {})
            if ann.get("code"):
                text = f"`{text}`"
            if ann.get("bold"):
                text = f"**{text}**"
            if ann.get("italic"):
                text = f"*{text}*"
            if ann.get("strikethrough"):
                text = f"~~{text}~~"
            href = rt.get("href")
            if href:
                text = f"[{text}]({href})"
            result += text
        return result

    if t == "paragraph":
        return rich_text(b["rich_text"]) + "\n"
    elif t == "heading_1":
        return f"# {rich_text(b['rich_text'])}\n"
    elif t == "heading_2":
        return f"## {rich_text(b['rich_text'])}\n"
    elif t == "heading_3":
        return f"### {rich_text(b['rich_text'])}\n"
    elif t == "bulleted_list_item":
        return f"- {rich_text(b['rich_text'])}\n"
    elif t == "numbered_list_item":
        return f"1. {rich_text(b['rich_text'])}\n"
    elif t == "to_do":
        check = "x" if b.get("checked") else " "
        return f"- [{check}] {rich_text(b['rich_text'])}\n"
    elif t == "quote":
        return f"> {rich_text(b['rich_text'])}\n"
    elif t == "code":
        lang = b.get("language", "")
        code = rich_text(b["rich_text"])
        return f"```{lang}\n{code}\n```\n"
    elif t == "divider":
        return "---\n"
    elif t == "image":
        src = b.get("file", {}).get("url") or b.get("external", {}).get("url", "")
        caption = rich_text(b.get("caption", []))
        alt = caption or "image"
        if src and assets_dir:
            try:
                src = download_image(src, assets_dir)
            except Exception as e:
                print(f"    Warning: could not download image: {e}")
        return f"![{alt}]({src})\n"
    elif t == "callout":
        icon = b.get("icon", {}).get("emoji", "")
        return f"> {icon} {rich_text(b['rich_text'])}\n"
    elif t == "toggle":
        return rich_text(b["rich_text"]) + "\n"
    else:
        return ""


def get_page_markdown(page_id: str, assets_dir: str = None) -> str:
    lines = []
    cursor = None

    while True:
        kwargs = {"block_id": page_id}
        if cursor:
            kwargs["start_cursor"] = cursor

        response = notion.blocks.children.list(**kwargs)

        for block in response["results"]:
            md = block_to_md(block, assets_dir)
            if md:
                lines.append(md)

        if response["has_more"]:
            cursor = response["next_cursor"]
        else:
            break

    return "\n".join(lines)


def sync():
    if os.path.exists(OUTPUT_DIR):
        for root, dirs, files in os.walk(OUTPUT_DIR, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
        os.rmdir(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    pages = get_live_pages()
    print(f"Found {len(pages)} live pages")

    for page in pages:
        title = get_title(page)
        slug = get_slug(page)
        folder = os.path.join(OUTPUT_DIR, slug)
        os.makedirs(folder, exist_ok=True)

        assets_dir = os.path.join(folder, "assets")
        md = get_page_markdown(page["id"], assets_dir)
        full_md = f"# {title}\n\n{md}"

        with open(os.path.join(folder, "index.md"), "w", encoding="utf-8") as f:
            f.write(full_md)

        print(f"  ✓ {title}")

    print("Sync complete.")


if __name__ == "__main__":
    sync()
