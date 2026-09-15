import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "projects.json"
OWNER = "Triyan31"
ALLOWED_TOPICS = {"portfolio", "research", "teaching"}


def github_json(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Triyan31-portfolio-sync"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def main():
    registry = json.loads(DATA.read_text(encoding="utf-8"))
    projects = registry.get("projects", [])
    by_repo = {p.get("repo"): p for p in projects if p.get("source") == "github" and p.get("repo")}

    # Public endpoint only: private repositories are intentionally excluded.
    repos = github_json(f"https://api.github.com/users/{OWNER}/repos?type=owner&per_page=100&sort=updated")
    seen = set()

    for repo in repos:
        if repo.get("private") or repo.get("fork") or repo.get("archived"):
            continue
        full_name = repo["full_name"]
        existing = by_repo.get(full_name)
        topics = set(repo.get("topics") or [])
        eligible = bool(topics & ALLOWED_TOPICS) or bool(existing and existing.get("tracked"))
        if not eligible:
            continue

        seen.add(full_name)
        if existing is None:
            status = "research" if "research" in topics else "open-work"
            existing = {
                "id": repo["name"], "source": "github", "tracked": True,
                "visibility": "public", "status": status,
                "label": "PUBLIC · RESEARCH" if status == "research" else "PUBLIC · PROJECT",
                "symbol": repo["name"][:2].upper(), "title": repo["name"].replace("-", " ").title(),
                "description": repo.get("description") or "Public GitHub project.",
                "url": repo["html_url"], "repo": full_name, "tags": []
            }
            projects.append(existing)

        # Update safe public metadata only. Curated title/description/tags stay editorially controlled.
        existing["github"] = {
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "language": repo.get("language"),
            "topics": sorted(topics),
            "updated_at": repo.get("updated_at")
        }
        existing["available"] = True

    for full_name, project in by_repo.items():
        if project.get("tracked") and full_name not in seen:
            project["available"] = False

    registry["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    DATA.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
