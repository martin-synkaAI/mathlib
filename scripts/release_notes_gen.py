#!/usr/bin/env python3
"""
release_notes_gen.py — Generate release notes from Git commit history.

Usage:
    python scripts/release_notes_gen.py /path/to/repo [--since v1.0.0] [--until v1.1.0]

Run as part of the release pipeline:
    stage('Release Notes') {
        steps {
            sh 'python3 scripts/release_notes_gen.py . --since ${PREV_TAG} --until ${VERSION}'
        }
    }

The script categorizes commits by their conventional commit prefix:
    feat:     → New Features
    fix:      → Bug Fixes
    refactor: → Improvements
    docs:     → Documentation
    test:     → Test Changes
    chore:    → Maintenance
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

# GitPython wraps the git CLI — like subprocess but with a nice API.
# In Python terms: it's the "requests" library but for Git instead of HTTP.
from git import Repo
from jinja2 import Template


# --- Data classes (like Python dataclasses — structured data containers) ---

@dataclass
class CommitInfo:
    """Represents one parsed Git commit."""
    sha: str            # The commit hash (e.g., "a1b2c3d")
    short_sha: str      # First 7 characters
    message: str        # Full commit message
    author: str         # Who wrote it
    date: str           # When
    category: str       # Parsed category (feat, fix, etc.)
    description: str    # Message without the category prefix


@dataclass
class ReleaseNotes:
    """The structured release notes document."""
    version: str
    date: str
    previous_version: str
    total_commits: int
    categories: dict = field(default_factory=dict)  # category -> [CommitInfo]
    contributors: list = field(default_factory=list)


# --- Commit parsing ---

# This regex matches conventional commit format: "type: description"
# or "type(scope): description"
COMMIT_PATTERN = re.compile(
    r'^(?P<type>feat|fix|refactor|docs|test|chore|perf|style|build|ci)'
    r'(?:\((?P<scope>[^)]+)\))?'
    r':\s*(?P<description>.+)$',
    re.IGNORECASE
)

# Human-readable category names for the release notes
CATEGORY_NAMES = {
    'feat': 'New Features',
    'fix': 'Bug Fixes',
    'refactor': 'Improvements',
    'perf': 'Performance',
    'docs': 'Documentation',
    'test': 'Test Changes',
    'chore': 'Maintenance',
    'build': 'Build System',
    'ci': 'CI/CD',
    'style': 'Code Style',
    'other': 'Other Changes',
}


def parse_commit(commit) -> CommitInfo:
    """Parse a git commit into a structured CommitInfo object.
    
    This is where conventional commit messages become powerful.
    If teams use "feat:", "fix:", etc. prefixes, we can auto-categorize.
    If they don't, everything goes into "Other Changes."
    
    Enforce this convention via a commit-msg hook
    or a PR check.
    """
    message = commit.message.strip().split('\n')[0]  # First line only
    match = COMMIT_PATTERN.match(message)
    
    if match:
        category = match.group('type').lower()
        description = match.group('description')
    else:
        category = 'other'
        description = message
    
    return CommitInfo(
        sha=commit.hexsha,
        short_sha=commit.hexsha[:7],
        message=message,
        author=commit.author.name,
        date=datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d'),
        category=category,
        description=description,
    )


def get_commits_between_tags(
    repo_path: str,
    since_tag: Optional[str] = None,
    until_tag: Optional[str] = None,
) -> list[CommitInfo]:
    """Get all commits between two Git tags.
    
    If since_tag is None, gets all commits up to until_tag.
    If until_tag is None, gets all commits since since_tag to HEAD.
    
    "Give me all commits between v10.1.0 and v10.2.0"
    """
    repo = Repo(repo_path)
    
    # Build the revision range string
    # Git revision ranges: "v1.0.0..v1.1.0" means "commits in v1.1.0 not in v1.0.0"
    if since_tag and until_tag:
        rev_range = f"{since_tag}..{until_tag}"
    elif since_tag:
        rev_range = f"{since_tag}..HEAD"
    else:
        rev_range = None  # All commits
    
    # Get commits using GitPython
    if rev_range:
        commits = list(repo.iter_commits(rev_range))
    else:
        commits = list(repo.iter_commits('HEAD', max_count=50))
    
    return [parse_commit(c) for c in commits]


def generate_release_notes(
    repo_path: str,
    version: str,
    since_tag: Optional[str] = None,
) -> ReleaseNotes:
    """Generate structured release notes from Git history.
    
    This is the main function. It:
    1. Gets commits since the last release
    2. Categorizes them
    3. Extracts contributor list
    4. Returns a structured ReleaseNotes object
    """
    commits = get_commits_between_tags(repo_path, since_tag=since_tag)
    
    # Group commits by category
    categories = {}
    contributors = set()
    
    for commit in commits:
        cat_name = CATEGORY_NAMES.get(commit.category, 'Other Changes')
        if cat_name not in categories:
            categories[cat_name] = []
        categories[cat_name].append(commit)
        contributors.add(commit.author)
    
    return ReleaseNotes(
        version=version,
        date=datetime.now().strftime('%Y-%m-%d'),
        previous_version=since_tag or 'initial',
        total_commits=len(commits),
        categories=categories,
        contributors=sorted(contributors),
    )


def render_markdown(notes: ReleaseNotes) -> str:
    """Render release notes as Markdown.
    
    Uses Jinja2 templating — same as you'd use for HTML templates
    in Flask/Django. The template is inline here but at IAR you'd
    put it in templates/release_notes.md.j2
    """
    template_str = """# Release Notes — {{ version }}

**Release date:** {{ date }}
**Previous version:** {{ previous_version }}
**Total commits:** {{ total_commits }}

---

{% for category, commits in categories.items() %}
## {{ category }}

{% for c in commits %}
- {{ c.description }} (`{{ c.short_sha }}` — {{ c.author }}, {{ c.date }})
{% endfor %}

{% endfor %}
---

### Contributors

{% for name in contributors %}
- {{ name }}
{% endfor %}
"""
    template = Template(template_str)
    return template.render(
        version=notes.version,
        date=notes.date,
        previous_version=notes.previous_version,
        total_commits=notes.total_commits,
        categories=notes.categories,
        contributors=notes.contributors,
    )


def render_json(notes: ReleaseNotes) -> str:
    """Render release notes as JSON.
    
    Useful for programmatic consumption — a dashboard or web UI
    that displays release history. At IAR, this might feed into
    the customer-facing release page.
    """
    data = {
        'version': notes.version,
        'date': notes.date,
        'previous_version': notes.previous_version,
        'total_commits': notes.total_commits,
        'categories': {
            cat: [asdict(c) for c in commits]
            for cat, commits in notes.categories.items()
        },
        'contributors': notes.contributors,
    }
    return json.dumps(data, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description='Generate release notes from Git history'
    )
    parser.add_argument('repo', help='Path to the Git repository')
    parser.add_argument('--version', default='NEXT', help='Version being released')
    parser.add_argument('--since', help='Previous version tag (e.g., v1.0.0)')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown')
    parser.add_argument('--output', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    print(f"Generating release notes for {args.version}...", file=sys.stderr)
    notes = generate_release_notes(args.repo, args.version, args.since)
    
    if args.format == 'json':
        output = render_json(notes)
    else:
        output = render_markdown(notes)
    
    if args.output:
        Path(args.output).write_text(output)
        print(f"Release notes written to {args.output}", file=sys.stderr)
    else:
        print(output)
    
    print(f"Done: {notes.total_commits} commits across "
          f"{len(notes.categories)} categories", file=sys.stderr)


if __name__ == '__main__':
    main()