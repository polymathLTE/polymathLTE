"""
Fetches the most recently pushed repositories for polymathLTE and updates
the <!-- CURRENT_PROJECTS:START/END --> block in README.md.
"""
import os
import re
import sys
import requests

USERNAME = "polymathLTE"
TOP_N = 5
README_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")

START_MARKER = "<!-- CURRENT_PROJECTS:START -->"
END_MARKER = "<!-- CURRENT_PROJECTS:END -->"


def fetch_recent_repos(token: str) -> list[dict]:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(
        f"https://api.github.com/users/{USERNAME}/repos",
        params={"sort": "pushed", "direction": "desc", "per_page": 20, "type": "owner"},
        headers=headers,
        timeout=15,
    )
    resp.raise_for_status()
    repos = [r for r in resp.json() if not r["fork"]]
    return repos[:TOP_N]


def build_section(repos: list[dict]) -> str:
    lines = []
    for repo in repos:
        name = repo["name"]
        url = repo["html_url"]
        desc = (repo.get("description") or "").strip()
        desc_part = f" -- {desc}" if desc else ""
        lines.append(f"- [**{name}**]({url}){desc_part}")
    return "\n".join(lines) + "\n"


def update_readme(new_block: str) -> None:
    with open(README_PATH, "r", encoding="utf-8") as fh:
        readme = fh.read()

    pattern = re.compile(
        rf"({re.escape(START_MARKER)}).*?({re.escape(END_MARKER)})",
        re.DOTALL,
    )
    if not pattern.search(readme):
        print("ERROR: markers not found in README.md", file=sys.stderr)
        sys.exit(1)

    new_readme = pattern.sub(rf"\1\n{new_block}\2", readme)

    with open(README_PATH, "w", encoding="utf-8") as fh:
        fh.write(new_readme)


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("WARNING: GITHUB_TOKEN is not set. Proceeding unauthenticated (rate limits apply).", file=sys.stderr)
    repos = fetch_recent_repos(token)
    block = build_section(repos)
    update_readme(block)
    print(f"README updated with {len(repos)} recent project(s).")


if __name__ == "__main__":
    main()
