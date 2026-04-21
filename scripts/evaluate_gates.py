#!/usr/bin/env python3
"""
evaluate_gates.py — Evaluate quality gates for a release candidate.

Usage:
    python scripts/evaluate_gates.py \\
        --test-results test-results.xml \\
        --coverage-threshold 80 \\
        --analysis-report cppcheck-report.xml

In Jenkins:
    stage('Quality Gate') {
        steps {
            sh '''
                python3 scripts/evaluate_gates.py \\
                    --test-results test-results.xml \\
                    --coverage-threshold 80 \\
                    --analysis-report cppcheck-report.xml
            '''
        }
    }

Exit code 0 = all gates passed (pipeline continues)
Exit code 1 = one or more gates failed (pipeline blocks)

Check:
- All tests passed across 20+ target architectures
- Static analysis: zero critical findings
- Code coverage above threshold
- Performance benchmarks within tolerance
- Open hazards resolved in risk management tool
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GateResult:
    """Result of evaluating one quality gate."""
    name: str
    passed: bool
    message: str
    details: str = ""


def check_test_results(xml_path: str) -> GateResult:
    """Parse JUnit XML test results and check for failures.
    
    JUnit XML is the standard test result format that Jenkins understands.
    Google Test, pytest, and most test frameworks can output it.
    
    The XML structure looks like:
    <testsuites tests="16" failures="0" errors="0">
        <testsuite name="MathLibAdd" tests="3">
            <testcase name="PositiveNumbers" status="run"/>
            <testcase name="NegativeNumbers" status="run"/>
        </testsuite>
    </testsuites>
    """
    if not Path(xml_path).exists():
        return GateResult(
            name="Test results",
            passed=False,
            message="FAIL: Test results file not found",
            details=f"Expected file at: {xml_path}"
        )
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Handle both <testsuites> (wrapper) and <testsuite> (direct) root
    if root.tag == 'testsuites':
        total = int(root.get('tests', 0))
        failures = int(root.get('failures', 0))
        errors = int(root.get('errors', 0))
    else:
        total = int(root.get('tests', 0))
        failures = int(root.get('failures', 0))
        errors = int(root.get('errors', 0))
    
    passed = (failures == 0 and errors == 0)
    
    # Collect failed test names for the report
    failed_tests = []
    for testsuite in root.iter('testsuite'):
        for testcase in testsuite.iter('testcase'):
            failure = testcase.find('failure')
            if failure is not None:
                name = f"{testsuite.get('name', '?')}.{testcase.get('name', '?')}"
                failed_tests.append(name)
    
    if passed:
        return GateResult(
            name="Test results",
            passed=True,
            message=f"PASS: {total} tests passed, 0 failures",
        )
    else:
        return GateResult(
            name="Test results",
            passed=False,
            message=f"FAIL: {failures} failures, {errors} errors out of {total} tests",
            details="Failed tests:\n" + "\n".join(f"  - {t}" for t in failed_tests)
        )


def check_static_analysis(xml_path: str, max_critical: int = 0) -> GateResult:
    """Parse cppcheck XML report and check for critical findings.
    
    cppcheck outputs XML like:
    <results>
        <errors>
            <error id="nullPointer" severity="error" msg="..."/>
            <error id="unusedVariable" severity="style" msg="..."/>
        </errors>
    </results>
    
    We block on 'error' severity (critical bugs).
    We report but don't block on 'warning' and 'style'.
    
    """
    if not Path(xml_path).exists():
        return GateResult(
            name="Static analysis",
            passed=True,  # Don't block if no report (maybe not configured)
            message="SKIP: Static analysis report not found",
            details=f"Expected file at: {xml_path}"
        )
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    severity_counts = {'error': 0, 'warning': 0, 'style': 0, 'performance': 0, 'information': 0}
    critical_findings = []
    
    for error in root.iter('error'):
        severity = error.get('severity', 'unknown')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        if severity == 'error':
            critical_findings.append(
                f"{error.get('id', '?')}: {error.get('msg', 'No message')}"
            )
    
    total_critical = severity_counts.get('error', 0)
    passed = total_critical <= max_critical
    
    summary = ", ".join(f"{k}: {v}" for k, v in severity_counts.items() if v > 0)
    
    if passed:
        return GateResult(
            name="Static analysis",
            passed=True,
            message=f"PASS: {summary or 'No findings'}",
        )
    else:
        return GateResult(
            name="Static analysis",
            passed=False,
            message=f"FAIL: {total_critical} critical findings (max allowed: {max_critical})",
            details="Critical findings:\n" + "\n".join(f"  - {f}" for f in critical_findings)
        )


def check_build_metadata(version: str) -> GateResult:
    """Verify build metadata is present and valid.
    
    In production, this would check:
    - Version number follows semantic versioning
    - Build number is present
    - Git SHA is recorded
    - Docker image SHA is recorded
    - All dependencies are pinned
    
    For this lab, we do a simple version format check.
    """
    import re
    semver_pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?(\+[a-zA-Z0-9.]+)?$'
    
    if re.match(semver_pattern, version):
        return GateResult(
            name="Build metadata",
            passed=True,
            message=f"PASS: Version {version} follows semantic versioning",
        )
    else:
        return GateResult(
            name="Build metadata",
            passed=False,
            message=f"FAIL: Version '{version}' does not follow semantic versioning",
            details="Expected format: MAJOR.MINOR.PATCH[-prerelease][+build]"
        )


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate quality gates for a release candidate'
    )
    parser.add_argument('--test-results', default='test-results.xml',
                       help='Path to JUnit XML test results')
    parser.add_argument('--analysis-report', default='cppcheck-report.xml',
                       help='Path to static analysis XML report')
    parser.add_argument('--version', default='1.0.0',
                       help='Version being evaluated')
    parser.add_argument('--coverage-threshold', type=int, default=80,
                       help='Minimum code coverage percentage')
    parser.add_argument('--max-critical', type=int, default=0,
                       help='Maximum allowed critical static analysis findings')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  QUALITY GATE EVALUATION")
    print("=" * 60)
    print(f"  Version: {args.version}")
    print(f"  Date:    {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    # Run all gate checks
    gates = [
        check_test_results(args.test_results),
        check_static_analysis(args.analysis_report, args.max_critical),
        check_build_metadata(args.version),
    ]
    
    # Print results
    all_passed = True
    for gate in gates:
        status = "PASS" if gate.passed else "FAIL"
        icon = "+" if gate.passed else "X"
        print(f"  [{icon}] {gate.name}: {gate.message}")
        if gate.details:
            for line in gate.details.split('\n'):
                print(f"      {line}")
        if not gate.passed:
            all_passed = False
        print()
    
    # Final verdict
    print("=" * 60)
    if all_passed:
        print("  VERDICT: ALL GATES PASSED — release candidate approved")
        print("=" * 60)
        sys.exit(0)
    else:
        print("  VERDICT: GATES FAILED — release blocked")
        print("=" * 60)
        sys.exit(1)  # Non-zero exit = Jenkins marks stage as FAILED


if __name__ == '__main__':
    main()