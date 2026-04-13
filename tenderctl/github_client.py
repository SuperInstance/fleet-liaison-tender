"""GitHub API client for fleet vessel repos."""

import os
import base64
from typing import Dict, List, Optional
import requests


class GitHubClient:
    """Client for interacting with GitHub vessel repos."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable required")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        })
        self.api_base = "https://api.github.com"

    def get_repo_contents(self, owner: str, repo: str, path: str) -> List[Dict]:
        """Get contents of a directory in a repo."""
        url = f"{self.api_base}/repos/{owner}/{repo}/contents/{path}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_file_content(self, owner: str, repo: str, path: str) -> str:
        """Get decoded file content from a repo."""
        url = f"{self.api_base}/repos/{owner}/{repo}/contents/{path}"
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get("encoding") == "base64":
            return base64.b64decode(data["content"]).decode("utf-8")
        return data["content"]

    def create_file(self, owner: str, repo: str, path: str, content: str, message: str):
        """Create or update a file in a repo."""
        url = f"{self.api_base}/repos/{owner}/{repo}/contents/{path}"
        data = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        }
        response = self.session.put(url, json=data)
        response.raise_for_status()
        return response.json()

    def list_vessels(self, org: str = "SuperInstance") -> List[str]:
        """List all fleet vessel repos."""
        url = f"{self.api_base}/orgs/{org}/repos"
        response = self.session.get(url, params={"type": "sources", "per_page": 100})
        response.raise_for_status()
        repos = response.json()
        return [r["name"] for r in repos if "vessel" in r.get("name", "").lower() or r.get("name") in ["oracle1", "jetsonclaw1"]]

    def scan_bottles(self, owner: str, repo: str, paths: List[str] = None) -> List[Dict]:
        """Scan repo for bottle files in specified paths."""
        if paths is None:
            paths = ["for-oracle1", "for-fleet"]
        bottles = []
        for path in paths:
            try:
                contents = self.get_repo_contents(owner, repo, path)
                if isinstance(contents, list):
                    for item in contents:
                        if item["type"] == "file" and item["name"].endswith(".json"):
                            bottles.append({
                                "repo": repo,
                                "path": f"{path}/{item['name']}",
                                "name": item["name"],
                                "sha": item["sha"],
                            })
            except requests.exceptions.HTTPError as e:
                if e.response.status_code != 404:
                    raise
        return bottles
