#!/usr/bin/env python3
"""
delta_classifier.py — Classify changes for TUV certification routing.

Analyzes the Git diff between two versions and categorizes changes
by component and impact level. Recommends "delta certification" 
vs "full certification."

Usage:
    python scripts/delta_classifier.py /path/to/repo --from v1.0.0 --to v1.1.0

This feeds into the certification team's workflow:
- Full certification: new target architecture, major optimization rewrite
- Delta certification: bug fixes, minor features, device support additions

The classification rules would be defined by the safety team.
This script automates the analysis; humans make the final call.
"""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from git import Repo


@dataclass
class FileChange:
    """One changed file with its classification."""
    path: str
    change_type: str      # added, modified, deleted, renamed
    lines_added: int
    lines_deleted: int
    component: str         # classified component
    impact_level: str      # low, medium, high, critical


# Component classification rules
# In production at IAR, these would map to actual product components:
# compiler backend, optimizer, code generator, debugger, linker, etc.
COMPONENT_RULES = [
    (r'^src/.*\.cpp$', 'core-library', 'Product source code'),
    (r'^include/.*\.h$', 'public-api', 'Public interface'),
    (r'^tests/.*', 'test-suite', 'Test code'),
    (r'^CMakeLists\.txt$', 'build-system', 'Build configuration'),
    (r'^Dockerfile$', 'infrastructure', 'Build environment'),
    (r'^Jenkinsfile$', 'infrastructure', 'CI/CD pipeline'),
    (r'^docs?/.*', 'documentation', 'Documentation'),
    (r'.*\.md$', 'documentation', 'Documentation'),
    (r'.*', 'other', 'Other'),
]

# Impact classification rules
IMPACT_RULES = {
    'public-api': 'critical',      # API changes affect all users
    'core-library': 'high',        # Core logic changes need regression testing
    'build-system': 'medium',      # Build changes could affect output
    'test-suite': 'low',           # Test changes don't affect the product
    'infrastructure': 'low',       # CI changes don't affect the product
    'documentation': 'low',        # Docs don't affect the product
    'other': 'medium',             # Unknown = caution
}


def classify_file(path: str) -> tuple[str, str]:
    """Classify a file path into component and impact level."""
    for pattern, component, _ in COMPONENT_RULES:
        if re.match(pattern, path):
            impact = IMPACT_RULES.get(component, 'medium')
            return component, impact
    return 'other', 'medium'


def analyze_diff(repo_path: str, from_ref: str, to_ref: str) -> list[FileChange]:
    """Analyze the diff between two Git refs."""
    repo = Repo(repo_path)
    
    # Get the diff between two refs
    from_commit = repo.commit(from_ref)
    to_commit = repo.commit(to_ref)
    diff = from_commit.diff(to_commit)
    
    changes = []
    for d in diff:
        # Determine change type
        if d.new_file:
            change_type = 'added'
            path = d.b_path
        elif d.deleted_file:
            change_type = 'deleted'
            path = d.a_path
        elif d.renamed_file:
            change_type = 'renamed'
            path = d.b_path
        else:
            change_type = 'modified'
            path = d.b_path or d.a_path
        
        # Count lines changed (simplified)
        try:
            diff_text = d.diff.decode('utf-8', errors='replace') if d.diff else ''
            lines_added = diff_text.count('\n+') - diff_text.count('\n+++')
            lines_deleted = diff_text.count('\n-') - diff_text.count('\n---')
        except Exception:
            lines_added = 0
            lines_deleted = 0
        
        component, impact = classify_file(path)
        
        changes.append(FileChange(
            path=path,
            change_type=change_type,
            lines_added=max(0, lines_added),
            lines_deleted=max(0, lines_deleted),
            component=component,
            impact_level=impact,
        ))
    
    return changes


def recommend_certification(changes: list[FileChange]) -> dict:
    """Recommend certification approach based on change analysis."""
    
    # Count changes by impact level
    impact_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    component_changes = {}
    total_lines = 0
    
    for c in changes:
        impact_counts[c.impact_level] = impact_counts.get(c.impact_level, 0) + 1
        total_lines += c.lines_added + c.lines_deleted
        
        if c.component not in component_changes:
            component_changes[c.component] = 0
        component_changes[c.component] += 1
    
    # Decision logic
    # Thresholds would be defined by the safety team
    if impact_counts['critical'] > 0:
        recommendation = 'FULL CERTIFICATION'
        reason = f"{impact_counts['critical']} critical-impact changes detected (public API modified)"
    elif impact_counts['high'] > 5 or total_lines > 1000:
        recommendation = 'FULL CERTIFICATION'
        reason = f"Significant changes: {impact_counts['high']} high-impact files, {total_lines} lines changed"
    elif impact_counts['high'] > 0:
        recommendation = 'DELTA CERTIFICATION'
        reason = f"{impact_counts['high']} high-impact changes — delta analysis required"
    else:
        recommendation = 'DELTA CERTIFICATION'
        reason = "Only low/medium-impact changes — streamlined delta process"
    
    return {
        'recommendation': recommendation,
        'reason': reason,
        'impact_counts': impact_counts,
        'component_changes': component_changes,
        'total_files': len(changes),
        'total_lines': total_lines,
    }


def main():
    parser = argparse.ArgumentParser(
        description='Classify changes for TUV certification routing'
    )
    parser.add_argument('repo', help='Path to Git repository')
    parser.add_argument('--from', dest='from_ref', required=True,
                       help='Previous certified version (e.g., v1.0.0)')
    parser.add_argument('--to', dest='to_ref', default='HEAD',
                       help='Current version (default: HEAD)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  TUV CERTIFICATION DELTA ANALYSIS")
    print("=" * 60)
    print(f"  From: {args.from_ref}")
    print(f"  To:   {args.to_ref}")
    print("=" * 60)
    print()
    
    changes = analyze_diff(args.repo, args.from_ref, args.to_ref)
    
    if not changes:
        print("  No changes detected between versions.")
        sys.exit(0)
    
    # Print change details
    print(f"  Changed files ({len(changes)}):")
    print()
    for c in sorted(changes, key=lambda x: x.impact_level):
        icon = {
            'critical': 'X', 'high': '!',
            'medium': '~', 'low': '.'
        }.get(c.impact_level, '?')
        print(f"    [{icon}] {c.path}")
        print(f"        {c.change_type} | +{c.lines_added}/-{c.lines_deleted} "
              f"| {c.component} | impact: {c.impact_level}")
    
    print()
    
    # Print recommendation
    result = recommend_certification(changes)
    
    print("  Component summary:")
    for comp, count in sorted(result['component_changes'].items()):
        print(f"    {comp:20s}: {count} files changed")
    print()
    
    print("  Impact summary:")
    for level, count in result['impact_counts'].items():
        if count > 0:
            print(f"    {level:10s}: {count} files")
    print()
    
    print("=" * 60)
    print(f"  RECOMMENDATION: {result['recommendation']}")
    print(f"  Reason: {result['reason']}")
    print()
    print("  Note: This is an automated recommendation.")
    print("  The safety team makes the final certification decision.")
    print("=" * 60)


if __name__ == '__main__':
    main()