import re
from pathlib import Path
from typing import Iterable
import argparse


def replace_relative_links(
    files_names: Iterable[str | Path],
    file_base_url: str,
    image_base_url: str,
    project_root: str | Path | None = None,
):
    """
    Simple script to replace relative links in a markdown document, e.g. [my local file](/route/to/local/file.md).
    Pro:
    - The script differs between links relative to the project root ('/folder/file.md') or relative to the current file ('folder/file.md').
    - The script differs between links to images ('![image.png](folder/image.png)') and other files and uses different base urls.
    Cons:
    - The script will break if a link contains a ')'
    - The script does not respect code blocks and will replace markdown links in code blocks.
    - Link replacement is limited files in the same repository and branch.
    """
    base_dir = Path(project_root).resolve() if project_root else Path.cwd()
    link_pattern = re.compile(
        r"(!?)\[([^]]+)\]\(([^)]+)\)"
    )  # Pattern is flawed (but good enough for me...)
    http_pattern = re.compile(r"^http(s)?:\/\/")

    for file in (Path(f).resolve() for f in files_names):
        # Don't ask...
        if not file.is_relative_to(Path.cwd()):
            raise ValueError(
                f"Invalid file path: file '{file}' is not relative to project root '{base_dir}'"
            )

        text = file.read_text()

        offset = 0
        replaced_links: list[tuple[str, str]] = []
        for match in re.finditer(link_pattern, text):
            link = match.group(3).strip()  # 3rd group is the link itself
            # Skip if link is not relative
            if re.match(http_pattern, link):
                continue

            if link.startswith("/"):
                linked_file = base_dir / link[1:]  # Relative to project root
            else:
                linked_file = file.parent / link  # Relative to current file
            linked_file = linked_file.resolve()

            if not linked_file.is_relative_to(base_dir):
                raise ValueError(
                    f"Link '{link}' in file '{file}' is not relative to project root '{base_dir}'"
                )
            if not linked_file.exists():
                raise FileNotFoundError(f"File or directory {linked_file}.")

            base_url = image_base_url if match.group(1) else file_base_url
            replacement_link = (
                f"{base_url.rstrip("/")}/{linked_file.relative_to(base_dir)}"
            )
            text = (
                text[: match.start(3) + offset]
                + replacement_link
                + text[match.end(3) + offset :]
            )
            offset += len(replacement_link) - len(match.group(3))
            replaced_links.append((link, replacement_link))

        file.write_text(text)
        print(
            f"Replaced {len(replaced_links)} link(s) in file {file.relative_to(base_dir)}:"
        )
        for original, replacement in replaced_links:
            print(f"  {original} --> {replacement}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Markdown Link Replacer",
        description="Replaces relative links in a markdown file with web links.",
    )
    parser.add_argument(
        "--file-url",
        type=str,
        help="Base url for files. Will be added to relative file links. Can be omitted if '--github-repo' is set.",
    )
    parser.add_argument(
        "--image-url",
        type=str,
        help="Base url for images. Will be added to relative image links. Defaults to 'file-url' or raw github link",
    )
    parser.add_argument(
        "--github-repo",
        type=str,
        help="A github user and repository name (e.g. 'octocat/Hello-World'). Auto creates file and image links to branch 'main'. Will be overridden by '--file_url' and '--image-url'.",
    )
    parser.add_argument(
        "--project_root",
        type=str,
        help="Set a directory to the project root. Defaults to current working directory.",
    )
    parser.add_argument("files", type=str, nargs="+", help="One or more markdown files")

    args = parser.parse_args()
    print(args)
    if not args.file_url and not args.github_repo:
        parser.error("Either '--file-url' or '--github-repo' must be set.")

    file_url = args.file_url or f"https://github.com/{args.github_repo}/blob/main"
    image_url = (
        args.image_url
        or args.file_url
        or f"https://raw.githubusercontent.com/{args.github_repo}/main/"
    )
    replace_relative_links(
        files_names=args.files,
        file_base_url=file_url,
        image_base_url=image_url,
        project_root=args.project_root,
    )
