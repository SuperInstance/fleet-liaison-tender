"""GitHub API client for tenderctl — fleet bottle scanner."""
import os
import base64
import requests
from typing import Dict, List, Optional

class GitHubClient:
    def __init__(self, token: str = None):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.api_base = "https://api.github.com"
        self.session = requests.Session()
        if self.token:
            self.session.headers["Authorization"] = f"token {self.token}"

    def list_vessels(self, org: str = "SuperInstance") -> List[str]:
        """List all fleet vessel repos with pagination."""
        known_vessels = {
            "oracle1-vessel", "JetsonClaw1-vessel", "navigator-vessel", "nautilus",
            "super-z-quartermaster", "pelagic-twin", "quill-isa-architect",
            "babel-vessel", "claude-code-vessel", "datum", "superz-parallel-fleet-executor",
        }
        all_repos = []
        for page in range(1, 15):
            url = f"{self.api_base}/users/{org}/repos"
            resp = self.session.get(url, params={"per_page": 100, "page": page})
            if resp.status_code != 200:
                break
            data = resp.json()
            if not data:
                break
            all_repos.extend(data)
        return [r["name"] for r in all_repos
                if "vessel" in r.get("name", "").lower()
                or r.get("name") in known_vessels]

    def scan_bottles(self, owner: str, repo: str, paths: List[str] = None) -> List[Dict]:
        """Scan repo for bottle files in specified paths."""
        if not paths:
            paths = ["for-oracle1", "for-fleet"]
        bottles = []
        for path in paths:
            url = f"{self.api_base}/repos/{owner}/{repo}/contents/{path}"
            resp = self.session.get(url)
            if resp.status_code != 200:
                continue
            for item in resp.json():
                if item.get("type") == "file" and item["name"].endswith(".md"):
                    bottles.append({
                        "vessel": repo,
                        "path": f"{path}/{item['name']}",
                        "name": item["name"],
                        "sha": item.get("sha", ""),
                        "url": item.get("html_url", ""),
                    })
        return bottles

    def read_file(self, owner: str, repo: str, path: str) -> Optional[str]:
        """Read file content from GitHub."""
        url = f"{self.api_base}/repos/{owner}/{repo}/contents/{path}"
        resp = self.session.get(url)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if "content" in data:
            return base64.b64decode(data["content"]).decode("utf-8")
        return None
