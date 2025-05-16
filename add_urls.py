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
YAML_DELIMITER = "---"

CONTENT_PATH = os.path.join(os.getcwd(), CONTENT_FOLDER)
IMAGE_PATH = os.path.join(os.getcwd(), IMAGE_FOLDER)


def get_url(file: str) -> str:
    return file.removeprefix(CONTENT_PATH).removesuffix(".md")


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
            url = url.removeprefix("/")

    url = url.removesuffix(".md")

    return f"[{text}]({url})"


def strip_link_suffix(line: str, file: str) -> str:
    return re.sub(LINK_REGEX, lambda x: parse_link(x, file), line)


def main():
    for file in iglob(CONTENT_PATH + "/**/*.md", recursive=True):
        print(f"Updating {file}...")

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

            f.truncate(0)
            f.seek(0)
            f.writelines(lines)


if __name__ == "__main__":
    main()
