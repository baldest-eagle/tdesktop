#!/usr/bin/env python3
"""
Unified Test Runner for Telegram Desktop Fork E2E Test Suite.
Discovers and executes Tier 1, Tier 2, Tier 3, and Tier 4 tests.
"""

import argparse
import io
import json
import os
import sys
import time
import unittest
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

# Ensure repository root is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


CATEGORY_MAP = {
    "Privacy & Ghost Mode (E3)": ["f01", "f02", "f1", "f2"],
    "Network & Download (B1)": ["f03", "f3"],
    "Call UI & Controls": ["f04", "f05", "f06", "f07", "f08", "f09", "f10", "f4", "f5", "f6", "f7", "f8", "f9", "f10"],
    "Multi-Display & Routing": ["f11", "f12", "f13", "f14", "f15"],
    "Grid Layout & Pin System": ["f16", "f17", "f18", "f19", "f20", "f21", "f22", "f23", "f24"],
    "Floating Overlay": ["f25", "f26", "f27", "f28"],
    "Embedded Chat & Search": ["f29", "f30"],
    "Participant Sidebar & Search": ["f31", "f32", "f33", "f34"],
    "Audio / Microphone": ["f35", "f36", "f37"],
    "Main Menu & Navigation": ["f38", "f39"],
    "UI Tweaks & Polish": ["f40", "f41", "f42", "f43", "f44"],
    "Context Menus & Cross-UI": ["f45", "f46", "f47", "f48"],
    "Backend / Engine": ["f49", "f50", "f51", "f52", "f53", "f54"],
    "Build & Toolchain": ["f55", "f56", "f57"],
}


class CustomTestResult(unittest.TestResult):
    def __init__(self, verbose: bool = False):
        super().__init__()
        self.verbose = verbose
        self.records: List[Dict[str, Any]] = []
        self.start_times: Dict[str, float] = {}

    def startTest(self, test: unittest.TestCase):
        super().startTest(test)
        self.start_times[test.id()] = time.time()
        if self.verbose:
            sys.stdout.write(f"  RUNNING: {test.id()} ... ")
            sys.stdout.flush()

    def addSuccess(self, test: unittest.TestCase):
        super().addSuccess(test)
        elapsed = time.time() - self.start_times.get(test.id(), time.time())
        self.records.append(
            {
                "id": test.id(),
                "name": test._testMethodName,
                "class": test.__class__.__name__,
                "module": test.__class__.__module__,
                "status": "PASS",
                "duration": elapsed,
                "error": None,
            }
        )
        if self.verbose:
            sys.stdout.write(f"PASS ({elapsed:.4f}s)\n")

    def addFailure(self, test: unittest.TestCase, err):
        super().addFailure(test, err)
        elapsed = time.time() - self.start_times.get(test.id(), time.time())
        err_msg = self._exc_info_to_string(err, test)
        self.records.append(
            {
                "id": test.id(),
                "name": test._testMethodName,
                "class": test.__class__.__name__,
                "module": test.__class__.__module__,
                "status": "FAIL",
                "duration": elapsed,
                "error": err_msg,
            }
        )
        if self.verbose:
            sys.stdout.write(f"FAIL ({elapsed:.4f}s)\n")

    def addError(self, test: unittest.TestCase, err):
        super().addError(test, err)
        elapsed = time.time() - self.start_times.get(test.id(), time.time())
        err_msg = self._exc_info_to_string(err, test)
        self.records.append(
            {
                "id": test.id(),
                "name": test._testMethodName,
                "class": test.__class__.__name__,
                "module": test.__class__.__module__,
                "status": "ERROR",
                "duration": elapsed,
                "error": err_msg,
            }
        )
        if self.verbose:
            sys.stdout.write(f"ERROR ({elapsed:.4f}s)\n")


def discover_suite(
    tier: str = "all",
    feature_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
) -> unittest.TestSuite:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    tier_dirs = []
    if tier in ("1", "all"):
        tier_dirs.append(os.path.join(SCRIPT_DIR, "tier1_features"))
    if tier in ("2", "all"):
        tier_dirs.append(os.path.join(SCRIPT_DIR, "tier2_boundaries"))
    if tier in ("3", "all"):
        tier_dirs.append(os.path.join(SCRIPT_DIR, "tier3_combinations"))
    if tier in ("4", "all"):
        tier_dirs.append(os.path.join(SCRIPT_DIR, "tier4_scenarios"))

    all_tests: List[unittest.TestCase] = []
    for t_dir in tier_dirs:
        if os.path.exists(t_dir):
            discovered = loader.discover(start_dir=t_dir, pattern="test_*.py", top_level_dir=REPO_ROOT)
            _extract_tests(discovered, all_tests)

    # Filtering
    for test in all_tests:
        test_id = test.id().lower()
        method_name = test._testMethodName.lower()

        # Feature filter
        if feature_filter:
            ff = feature_filter.lower().replace("-", "_")
            if ff not in method_name and ff not in test_id:
                continue

        # Category filter
        if category_filter:
            cf = category_filter.lower()
            # Match against category map
            matched = False
            for cat_name, feat_ids in CATEGORY_MAP.items():
                if cf in cat_name.lower():
                    if any(f"_{fid}_" in method_name or f"_{fid}" in method_name for fid in feat_ids):
                        matched = True
                        break
            if not matched and cf not in test_id and cf not in method_name:
                continue

        suite.addTest(test)

    return suite


def _extract_tests(suite_or_test, test_list: List[unittest.TestCase]):
    if isinstance(suite_or_test, unittest.TestCase):
        test_list.append(suite_or_test)
    elif isinstance(suite_or_test, unittest.TestSuite):
        for sub in suite_or_test:
            _extract_tests(sub, test_list)


def export_json(records: List[Dict[str, Any]], filepath: str, total_time: float):
    summary = {
        "total_tests": len(records),
        "passed": sum(1 for r in records if r["status"] == "PASS"),
        "failed": sum(1 for r in records if r["status"] == "FAIL"),
        "errors": sum(1 for r in records if r["status"] == "ERROR"),
        "total_duration_seconds": round(total_time, 4),
        "results": records,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def export_junit(records: List[Dict[str, Any]], filepath: str, total_time: float):
    root = ET.Element(
        "testsuite",
        name="TelegramDesktopE2E",
        tests=str(len(records)),
        failures=str(sum(1 for r in records if r["status"] == "FAIL")),
        errors=str(sum(1 for r in records if r["status"] == "ERROR")),
        time=f"{total_time:.4f}",
    )
    for r in records:
        tc = ET.SubElement(
            root,
            "testcase",
            name=r["name"],
            classname=r["class"],
            time=f"{r['duration']:.4f}",
        )
        if r["status"] == "FAIL":
            fail = ET.SubElement(tc, "failure", message="Assertion Failed")
            fail.text = r["error"] or ""
        elif r["status"] == "ERROR":
            err = ET.SubElement(tc, "error", message="Test Error")
            err.text = r["error"] or ""

    tree = ET.ElementTree(root)
    tree.write(filepath, encoding="utf-8", xml_declaration=True)


def print_summary_table(records: List[Dict[str, Any]], total_time: float):
    tier_counts = {"Tier 1 (Features)": 0, "Tier 2 (Boundaries)": 0, "Tier 3 (Combinations)": 0, "Tier 4 (Scenarios)": 0}
    tier_pass = {"Tier 1 (Features)": 0, "Tier 2 (Boundaries)": 0, "Tier 3 (Combinations)": 0, "Tier 4 (Scenarios)": 0}

    for r in records:
        mod = r["module"]
        if "tier1" in mod:
            t = "Tier 1 (Features)"
        elif "tier2" in mod:
            t = "Tier 2 (Boundaries)"
        elif "tier3" in mod:
            t = "Tier 3 (Combinations)"
        elif "tier4" in mod:
            t = "Tier 4 (Scenarios)"
        else:
            t = "Other"

        if t in tier_counts:
            tier_counts[t] += 1
            if r["status"] == "PASS":
                tier_pass[t] += 1

    total = len(records)
    passed = sum(1 for r in records if r["status"] == "PASS")
    failed = sum(1 for r in records if r["status"] == "FAIL")
    errors = sum(1 for r in records if r["status"] == "ERROR")

    print("\n" + "=" * 80)
    print("                      E2E TEST EXECUTION SUMMARY TABLE")
    print("=" * 80)
    print(f" {'Test Tier':<28} | {'Total':<8} | {'Passed':<8} | {'Failed':<8} | {'Pass Rate':<10}")
    print("-" * 80)
    for t, cnt in tier_counts.items():
        p = tier_pass[t]
        rate = f"{(p / cnt * 100):.1f}%" if cnt > 0 else "N/A"
        print(f" {t:<28} | {cnt:<8} | {p:<8} | {cnt - p:<8} | {rate:<10}")
    print("-" * 80)
    total_rate = f"{(passed / total * 100):.1f}%" if total > 0 else "0.0%"
    print(f" {'TOTAL (All Tiers)':<28} | {total:<8} | {passed:<8} | {failed + errors:<8} | {total_rate:<10}")
    print("=" * 80)
    print(f" Execution Status : {'ALL PASSED' if failed == 0 and errors == 0 else 'FAILED'}")
    print(f" Elapsed Time     : {total_time:.3f} seconds")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Telegram Desktop Fork E2E Test Runner")
    parser.add_argument("--tier", choices=["1", "2", "3", "4", "all"], default="all", help="Target test tier to run")
    parser.add_argument("--feature", type=str, default=None, help="Filter tests by feature ID or name")
    parser.add_argument("--category", type=str, default=None, help="Filter tests by category name")
    parser.add_argument("--json", type=str, default=None, help="Path to export JSON results file")
    parser.add_argument("--junit", type=str, default=None, help="Path to export JUnit XML results file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose per-test progress logging")

    args = parser.parse_args()

    print(f"=== Telegram Desktop Fork E2E Test Suite ===")
    print(f"Tier Selection: {args.tier.upper()} | Feature Filter: {args.feature or 'None'} | Category Filter: {args.category or 'None'}")
    print("Discovering and loading test suites...")

    suite = discover_suite(tier=args.tier, feature_filter=args.feature, category_filter=args.category)
    test_count = suite.countTestCases()
    print(f"Discovered {test_count} tests across specified target scope.")

    result = CustomTestResult(verbose=args.verbose)
    start_time = time.time()
    suite.run(result)
    total_time = time.time() - start_time

    print_summary_table(result.records, total_time)

    # Failures / Errors summary
    failures = [r for r in result.records if r["status"] in ("FAIL", "ERROR")]
    if failures:
        print("FAILURES & ERRORS DETAIL:")
        for idx, f in enumerate(failures, 1):
            print(f"\n[{idx}] {f['status']}: {f['id']}")
            print("-" * 60)
            print(f["error"])
        print("\n")

    if args.json:
        export_json(result.records, args.json, total_time)
        print(f"Exported JSON report to: {args.json}")

    if args.junit:
        export_junit(result.records, args.junit, total_time)
        print(f"Exported JUnit XML report to: {args.junit}")

    sys.exit(0 if len(failures) == 0 else 1)


if __name__ == "__main__":
    main()
