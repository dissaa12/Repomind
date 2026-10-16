"""
backend/ingestion/git_cloner.py - GitHub Repository Cloner & Cache Manager
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Tuple
from config import get_settings


def parse_github_url(url_or_slug: str) -> Tuple[str, str]:
    """
    Parses a GitHub URL or 'owner/repo' slug into (owner, repo_name).
    """
    clean = url_or_slug.strip().rstrip("/")
    if clean.endswith(".git"):
        clean = clean[:-4]

    # Match https://github.com/owner/repo or git@github.com:owner/repo
    match = re.search(r"github\.com[/:]([\w.-]+)/([\w.-]+)", clean)
    if match:
        return match.group(1), match.group(2)

    # Match slug 'owner/repo'
    parts = clean.split("/")
    if len(parts) == 2 and not clean.startswith("http"):
        return parts[0], parts[1]

    raise ValueError(f"Invalid GitHub repository URL or slug: '{url_or_slug}'")


def clone_or_update_repo(url_or_slug: str) -> Dict[str, str]:
    """
    Clones a remote GitHub repository into the local cache directory using shallow clone.
    """
    settings = get_settings()
    settings.repos_cache_dir.mkdir(parents=True, exist_ok=True)

    owner, repo_name = parse_github_url(url_or_slug)
    folder_name = f"{owner}_{repo_name}"
    target_dir = settings.repos_cache_dir / folder_name

    # Build clone URL (inject token if provided in settings)
    if settings.github_token:
        clone_url = f"https://x-access-token:{settings.github_token}@github.com/{owner}/{repo_name}.git"
    else:
        clone_url = f"https://github.com/{owner}/{repo_name}.git"

    if target_dir.exists() and (target_dir / ".git").exists():
        # Already cloned - perform quick pull
        try:
            subprocess.run(
                ["git", "pull", "--ff-only"],
                cwd=str(target_dir),
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )
        except Exception:
            pass  # Fallback to existing clone
    else:
        # Clone fresh with shallow depth
        cmd = ["git", "clone", "--depth", "1", clone_url, str(target_dir)]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode != 0:
            err = res.stderr or res.stdout
            # Redact token from error message if present
            if settings.github_token:
                err = err.replace(settings.github_token, "REDACTED_TOKEN")
            raise RuntimeError(f"Git clone failed: {err}")

    return {
        "repo_id": folder_name.lower(),
        "name": f"{owner}/{repo_name}",
        "local_path": str(target_dir),
        "source_type": "github",
        "url": f"https://github.com/{owner}/{repo_name}",
    }
