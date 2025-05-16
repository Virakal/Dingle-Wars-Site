#!/usr/bin/env python3

import os
import re
from urllib.parse import quote, unquote
from itertools import repeat
from glob import iglob

CONTENT_FOLDER = "content"
IMAGE_FOLDER = "static/ob/Images"
IMAGE_URL = "/ob/Images"
LINK_REGEX = re.compile(r"(?P<bang>!)?\[(?P<text>.+?)\]\((?P<url>.+?)\)")
SITE_TITLE = "Dingle Wars Notes"
YAML_DELIMITER = "---"

CONTENT_PATH = os.path.join(os.getcwd(), CONTENT_FOLDER)
IMAGE_PATH = os.path.join(os.getcwd(), IMAGE_FOLDER)


def get_url(file: str) -> str:
    return file.removeprefix(CONTENT_PATH).removesuffix(".md").replace("\\", "/")


def parsed_image_url(url: str) -> str:
    parts = url.split("|")
    path = parts[0]
    width = None

    if len(parts) > 1:
        width = parts[1]

    if os.path.exists(os.path.join(IMAGE_PATH, path)):
        path = f"{IMAGE_URL}/{path}"

    quoted = quote(path)
    width_html = ""

    if width:
        width_html = f' width="{width}px"'

    return f'<img src="{quoted}"{width_html}>'


def parse_link(match: re.Match[str], file: str) -> str:
    text = match.group("text")
    url = match.group("url")
    bang = match.group("bang")
    directory = os.path.dirname(file)
    clean_url = unquote(url)

    if bang:
        # Turn ![image.png|200] into HTML equivalent because it confuses Hugo
        clean = parsed_image_url(clean_url)

        if clean:
            return clean
    elif url.endswith(".png"):
        return f"![{text}]({url})"

    # Don't mess with absolute URLs
    if url.startswith("http"):
        return match.string.strip()

    if url.startswith("/"):
        # Check if this is actually an absolute link
        relative_file_path = os.path.join(directory, clean_url.removeprefix("/"))

        if os.path.exists(relative_file_path):
            url = "../" + url.removeprefix("/")

    url = url.removesuffix(".md")

    return f"[{text}]({url})"


def strip_link_suffix(line: str, file: str) -> str:
    return re.sub(LINK_REGEX, lambda x: parse_link(x, file), line)


def add_urls():
    weight = 0

    for file in iglob(CONTENT_PATH + "/**/*.md", recursive=True):
        print(f"Updating {file}...")
        weight += 1000

        with open(file, "r+") as f:
            lines = f.readlines()
            lines = list(map(strip_link_suffix, lines, list(repeat(file, len(lines)))))
            i = -1
            yaml_lines = []
            found_start = False

            for line in lines:
                i += 1

                if line.strip() == YAML_DELIMITER:
                    if found_start:
                        break

                    found_start = True
                    continue

                if found_start:
                    yaml_lines.append(line)

            if not list(filter(lambda x: x.startswith("url:"), yaml_lines)):
                url = get_url(file)
                lines.insert(i, f"url: {url}\n")

            if not list(filter(lambda x: x.startswith("weight:"), yaml_lines)):
                lines.insert(i, f"weight: {weight}\n")

            f.truncate(0)
            f.seek(0)
            f.writelines(lines)


def get_index_page(path: str, folders: list[str], files: list[str], weight: int = 1) -> str:
    folder_name = os.path.basename(path)
    url = path.replace(CONTENT_PATH, "").replace("\\", "/")

    if folder_name == os.path.basename(CONTENT_FOLDER):
        # We're on the root
        folder_name = SITE_TITLE

    lines = [
        "---",
        f"title: {folder_name}",
        f"url: {url}",
        f"weight: {weight}",
        "---",
        "",
    ]

    for folder in folders:
        folder_url = quote(f"./{folder}/")
        lines.append(f"- 📁 [{folder}]({folder_url})")

    for file in files:
        file_name = file.removesuffix(".md")
        file_url = quote(f"./{file_name}")
        lines.append(f"- 📄 [{file_name}]({file_url})")

    return "\n".join(lines) + "\n"


def create_indexes():
    weight = 0
    for path, folders, files in os.walk(CONTENT_PATH):
        weight += 10

        if "index.md" in files or "_index.md" in files:
            continue

        index_path = os.path.join(path, "_index.md")

        with open(index_path, "w") as f:
            f.write(get_index_page(path, folders, files, weight))

        print("Indexed path", index_path)


def main():
    add_urls()
    create_indexes()


if __name__ == "__main__":
    main()
