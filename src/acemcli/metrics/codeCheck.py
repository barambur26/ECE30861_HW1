from __future__ import annotations
import ast
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class MetricBreakdown:
    maintainer_responsiveness: float
    code_clarity: float
    structure: float
    tests_and_coverage: float
    governance_and_ci: float
    details: Dict[str, object]


@dataclass
class MetricResult:
    name: str
    score: float
    latency_ms: int
    breakdown: MetricBreakdown


def _safe_run_git(repo: Path, args: List[str]) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(
            ["git"] + args,
            cwd=str(repo),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return 1, "", str(e)


def _git_recent_activity_score(repo: Path) -> Tuple[float, Dict[str, object]]:
    """
    Score maintainer responsiveness using git history:
      - commits_last_90d (normalized)
      - unique_authors_180d (normalized)
      - days_since_last_commit (inverted)
    """
    details = {}
    # Default if no git
    if not (repo / ".git").exists():
        return 0.3, {"note": "No git history found (.git missing)"}  # neutral-ish

    # Last commit date (unix)
    rc, out, _ = _safe_run_git(repo, ["log", "-1", "--format=%ct"])
    if rc != 0 or not out.strip():
        return 0.3, {"note": "Unable to read git history"}
    last_commit_ts = int(out.strip())
    days_since_last = (time.time() - last_commit_ts) / 86400.0

    # Commits last 90 days
    since_90 = int(time.time() - 90 * 86400)
    rc, out, _ = _safe_run_git(repo, ["rev-list", "--count", f"--since={since_90}", "HEAD"])
    commits_90 = int(out.strip()) if rc == 0 and out.strip().isdigit() else 0

    # Unique authors last 180 days
    since_180 = int(time.time() - 180 * 86400)
    rc, out, _ = _safe_run_git(
        repo,
        ["log", f"--since={since_180}", "--format=%ae"]
    )
    authors = set()
    if rc == 0 and out:
        for line in out.splitlines():
            line = line.strip().lower()
            if line:
                authors.add(line)

    # Normalize components
    # Heuristics: 0–1 via soft thresholds
    def clamp01(x: float) -> float:
        return max(0.0, min(1.0, x))

    # More recent is better: 0 days -> 1.0, 365+ -> 0.0
    recency = clamp01(1.0 - (days_since_last / 365.0))
    # Commits: 50+ in 90d ~ 1.0
    commit_rate = clamp01(commits_90 / 50.0)
    # Authors: 5+ in 180d ~ 1.0
    diversity = clamp01(len(authors) / 5.0)

    score = 0.45 * recency + 0.35 * commit_rate + 0.20 * diversity
    details.update(
        dict(
            days_since_last_commit=round(days_since_last, 2),
            commits_last_90d=commits_90,
            unique_authors_last_180d=len(authors),
            components=dict(recency=recency, commit_rate=commit_rate, diversity=diversity),
        )
    )
    return score, details


def _iter_python_files(root: Path) -> List[Path]:
    return [p for p in root.rglob("*.py") if p.is_file() and ".venv" not in str(p)]


def _analyze_python_ast(files: List[Path]) -> Dict[str, float]:
    """
    Returns:
      - docstring_coverage: defs/classes with docstrings / total defs/classes
      - type_hint_coverage: fraction of function args+returns annotated
      - comment_ratio: comment lines / code lines
      - avg_line_len, max_line_len
    """
    total_defs = 0
    defs_with_doc = 0
    annotated_slots = 0
    total_slots = 0
    comment_lines = 0
    code_lines = 0
    total_len = 0
    total_lines_counted = 0
    max_len = 0

    for file in files:
        try:
            src = file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # line stats
        for line in src.splitlines():
            s = line.strip()
            if not s:
                continue
            if s.startswith("#"):
                comment_lines += 1
            else:
                code_lines += 1
            ln = len(line)
            total_len += ln
            total_lines_counted += 1
            if ln > max_len:
                max_len = ln

        try:
            tree = ast.parse(src)
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                total_defs += 1
                if ast.get_docstring(node):
                    defs_with_doc += 1

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Return annotation
                total_slots += 1
                if node.returns is not None:
                    annotated_slots += 1
                # Arg annotations
                for arg in list(node.args.args) + list(getattr(node.args, "kwonlyargs", [])):
                    total_slots += 1
                    if arg.annotation is not None:
                        annotated_slots += 1
                if node.args.vararg is not None:
                    total_slots += 1
                    if node.args.vararg.annotation is not None:
                        annotated_slots += 1
                if node.args.kwarg is not None:
                    total_slots += 1
                    if node.args.kwarg.annotation is not None:
                        annotated_slots += 1

    doc_cov = (defs_with_doc / total_defs) if total_defs else 0.0
    type_cov = (annotated_slots / total_slots) if total_slots else 0.0
    comment_ratio = (comment_lines / max(1, (comment_lines + code_lines)))
    avg_len = (total_len / total_lines_counted) if total_lines_counted else 0.0

    return dict(
        docstring_coverage=doc_cov,
        type_hint_coverage=type_cov,
        comment_ratio=comment_ratio,
        avg_line_len=avg_len,
        max_line_len=max_len,
    )


def _readme_quality(repo: Path) -> Tuple[float, Dict[str, object]]:
    """
    Simple README score: presence + key sections.
    """
    candidates = list(repo.glob("README*"))
    if not candidates:
        return 0.0, {"readme": "missing"}

    content = ""
    try:
        content = candidates[0].read_text(encoding="utf-8", errors="ignore")
    except Exception:
        pass

    present = {
        "installation": bool(re.search(r"\binstall(ation)?\b", content, re.IGNORECASE)),
        "usage": bool(re.search(r"\busage|example(s)?\b", content, re.IGNORECASE)),
        "license": bool(re.search(r"\blicense\b", content, re.IGNORECASE)),
        "contributing": bool(re.search(r"\bcontribut(ing|ion)\b", content, re.IGNORECASE)),
        "badges": bool(re.search(r"\bcoverage|build|ci\b", content, re.IGNORECASE)),
    }
    score = sum(present.values()) / 5.0
    return score, {"readme_file": str(candidates[0].name), "sections_found": present}


def _tests_and_coverage(repo: Path) -> Tuple[float, Dict[str, object]]:
    """
    Score:
      - tests directory or test_*.py present
      - README coverage badge
      - presence of pytest/coverage config files
    """
    details = {}
    has_tests_dir = (repo / "tests").exists()
    any_test_file = any(p.name.startswith("test_") or p.name.endswith("_test.py") for p in _iter_python_files(repo))
    tests_present = has_tests_dir or any_test_file

    # coverage badge in README
    coverage_pct = None
    readme_files = list(repo.glob("README*"))
    if readme_files:
        try:
            txt = readme_files[0].read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"(\d{1,3})\s*%\s*coverage", txt, re.IGNORECASE)
            if m:
                coverage_pct = min(100, max(0, int(m.group(1))))
        except Exception:
            pass

    # config presence
    cfg_files = [
        "pyproject.toml",
        "pytest.ini",
        "tox.ini",
        ".coveragerc",
        "setup.cfg",
    ]
    present_cfg = {c: (repo / c).exists() for c in cfg_files}

    # scoring heuristic
    score = 0.0
    score += 0.5 if tests_present else 0.0
    if coverage_pct is not None:
        score += 0.4 * (coverage_pct / 100.0)
    score += 0.1 * (sum(present_cfg.values()) / len(present_cfg))

    details.update(
        dict(
            tests_present=tests_present,
            has_tests_dir=has_tests_dir,
            any_test_file=any_test_file,
            coverage_badge_pct=coverage_pct,
            configs_present=present_cfg,
        )
    )
    return score, details


def _structure_score(repo: Path, py_files: List[Path]) -> Tuple[float, Dict[str, object]]:
    has_pyproject = (repo / "pyproject.toml").exists()
    has_setup_cfg = (repo / "setup.cfg").exists() or (repo / "setup.py").exists()
    has_src_layout = (repo / "src").exists()
    has_package_init = any(p.name == "__init__.py" for p in py_files)
    # simple packaging/structure score
    score = (
        0.35 * (1.0 if has_pyproject else 0.0)
        + 0.15 * (1.0 if has_setup_cfg else 0.0)
        + 0.30 * (1.0 if has_src_layout else 0.0)
        + 0.20 * (1.0 if has_package_init else 0.0)
    )
    return score, dict(
        has_pyproject=has_pyproject,
        has_setup_cfg=has_setup_cfg,
        has_src_layout=has_src_layout,
        has_package_init=has_package_init,
    )


def _governance_ci_score(repo: Path) -> Tuple[float, Dict[str, object]]:
    has_license = any((repo / name).exists() for name in ["LICENSE", "LICENSE.md", "LICENSE.txt"])
    has_ci = (repo / ".github" / "workflows").exists()
    has_gitignore = (repo / ".gitignore").exists()
    # pinned deps (==) in requirements*.txt
    req_files = list(repo.glob("requirements*.txt"))
    pinned_count = 0
    total_deps = 0
    for f in req_files:
        try:
            for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                total_deps += 1
                if "==" in s:
                    pinned_count += 1
        except Exception:
            pass
    pinned_ratio = (pinned_count / total_deps) if total_deps else 0.0

    score = (
        0.40 * (1.0 if has_license else 0.0)
        + 0.30 * (1.0 if has_ci else 0.0)
        + 0.15 * (1.0 if has_gitignore else 0.0)
        + 0.15 * pinned_ratio
    )
    return score, dict(
        has_license=has_license,
        has_ci_workflows=has_ci,
        has_gitignore=has_gitignore,
        requirements_files=[str(p.name) for p in req_files],
        pinned_ratio=round(pinned_ratio, 2),
    )


def _code_clarity_score(repo: Path, py_files: List[Path]) -> Tuple[float, Dict[str, object]]:
    ast_stats = _analyze_python_ast(py_files)
    readme_score, readme_det = _readme_quality(repo)

    # penalize extremely long lines (over 120 avg -> bad)
    line_length_penalty = 0.0
    if ast_stats["avg_line_len"] > 120:
        line_length_penalty = min(0.4, (ast_stats["avg_line_len"] - 120) / 200.0)

    # heuristic weighting
    score = (
        0.40 * ast_stats["docstring_coverage"]
        + 0.30 * ast_stats["type_hint_coverage"]
        + 0.15 * ast_stats["comment_ratio"]
        + 0.15 * readme_score
    )
    score = max(0.0, score - line_length_penalty)

    details = dict(ast_stats=ast_stats, readme=readme_det, line_length_penalty=line_length_penalty)
    return score, details


def score_code_quality(repo_path: str | Path) -> MetricResult:
    """
    Compute a 0–1 score with breakdown:
      - maintainer_responsiveness (git recency, commits, authors)
      - code_clarity (docstrings, type hints, comments, README)
      - structure (packaging/layout signals)
      - tests_and_coverage (tests present, coverage badge, configs)
      - governance_and_ci (license, CI, gitignore, pinned deps)
    """
    t0 = time.time()
    repo = Path(repo_path).resolve()

    py_files = _iter_python_files(repo)

    maint_score, maint_det = _git_recent_activity_score(repo)
    clarity_score, clarity_det = _code_clarity_score(repo, py_files)
    struct_score, struct_det = _structure_score(repo, py_files)
    tests_score, tests_det = _tests_and_coverage(repo)
    gov_score, gov_det = _governance_ci_score(repo)

    # weights sum to 1.0
    weights = {
        "maintainer_responsiveness": 0.20,
        "code_clarity": 0.20,
        "structure": 0.20,
        "tests_and_coverage": 0.30,
        "governance_and_ci": 0.10,
    }

    final = (
        weights["maintainer_responsiveness"] * maint_score
        + weights["code_clarity"] * clarity_score
        + weights["structure"] * struct_score
        + weights["tests_and_coverage"] * tests_score
        + weights["governance_and_ci"] * gov_score
    )
    latency_ms = int((time.time() - t0) * 1000)

    breakdown = MetricBreakdown(
        maintainer_responsiveness=round(maint_score, 3),
        code_clarity=round(clarity_score, 3),
        structure=round(struct_score, 3),
        tests_and_coverage=round(tests_score, 3),
        governance_and_ci=round(gov_score, 3),
        details={
            "maintainer": maint_det,
            "clarity": clarity_det,
            "structure": struct_det,
            "tests": tests_det,
            "governance": gov_det,
            "weights": weights,
        },
    )
    return MetricResult(
        name="code_quality",
        score=round(max(0.0, min(1.0, final)), 3),
        latency_ms=latency_ms,
        breakdown=breakdown,
    )


# --- Optional: tiny CLI shim for local testing ---
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Score code quality of a local repo.")
    ap.add_argument("repo", help="Path to local repository checkout")
    ap.add_argument("--ndjson", action="store_true", help="Print NDJSON line with score and breakdown")
    args = ap.parse_args()

    result = score_code_quality(args.repo)
    if args.ndjson:
        print(json.dumps({
            "metric": result.name,
            "score": result.score,
            "latency_ms": result.latency_ms,
            "breakdown": asdict(result.breakdown),
        }))
    else:
        print(f"Score: {result.score} (latency {result.latency_ms} ms)")
        print(json.dumps(asdict(result.breakdown), indent=2))
