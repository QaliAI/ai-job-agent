#!/usr/bin/env python3
"""Per-person profile configuration for the personal job agent.

A profile is a directory. Real clients live in profiles/<name>/, which is
gitignored. Committed samples live in examples/<name>/.

Every field is optional. Missing fields stay unset. The directory name is the
only identifier required to address a profile.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional


PROFILE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")

OPTIONAL_FIELDS = (
    "name",
    "source_resume",
    "target_titles",
    "acceptable_titles",
    "excluded_titles",
    "seniority",
    "locations",
    "work_mode",
    "salary",
    "industries",
    "preferred_companies",
    "excluded_companies",
    "skills",
    "work_authorization",
    "travel",
    "notification",
    "jobs_per_digest",
    "portals",
    "search",
    "priorities",
    "sample",
    "label",
)

WEIGHT_KEYS = (
    "title_and_role_relevance",
    "core_required_skills",
    "experience_seniority",
    "domain_industry_fit",
    "location_and_work_mode",
    "preferred_qualifications",
)


def repo_root_from_here() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def validate_profile_name(name: str) -> str:
    """Reject path separators and traversal. A profile name is one segment."""
    cleaned = (name or "").strip()
    if not PROFILE_NAME_RE.match(cleaned):
        raise ValueError(
            f"Profile name '{name}' is not allowed. Use letters, numbers, hyphens, "
            "and underscores only, with no slashes."
        )
    return cleaned


def _is_within(path: str, parent: str) -> bool:
    path = os.path.abspath(path)
    parent = os.path.abspath(parent)
    try:
        return os.path.commonpath([path, parent]) == parent
    except ValueError:
        return False


def resolve_profile_dir(name: str, repo_root: Optional[str] = None) -> str:
    """Resolve a profile name to its directory without crossing user roots.

    Search order: profiles/<name>, then examples/<name>.
    """
    root = os.path.abspath(repo_root or repo_root_from_here())
    cleaned = validate_profile_name(name)
    candidates = [
        os.path.join(root, "profiles", cleaned),
        os.path.join(root, "examples", cleaned),
    ]
    for path in candidates:
        if not _is_within(path, root):
            raise ValueError(f"Profile path escapes the repository: {path}")
        if os.path.isdir(path) and (
            os.path.exists(os.path.join(path, "profile.json"))
            or os.path.exists(os.path.join(path, "MASTER_PROFILE.md"))
        ):
            return path
    # Prefer the profiles/ location for a name that is not created yet.
    return candidates[0]


def empty_profile(name: str) -> Dict[str, Any]:
    """A usable profile with nothing filled in. Callers must not require more."""
    return {"name": name}


def load_user_profile(profile_dir: str) -> Dict[str, Any]:
    """Load profile.json. Missing file yields a name taken from the directory."""
    path = os.path.join(profile_dir, "profile.json")
    if not os.path.exists(path):
        return empty_profile(os.path.basename(profile_dir))
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a JSON object")
    if not data.get("name"):
        data["name"] = os.path.basename(profile_dir)
    return data


def save_user_profile(profile_dir: str, profile: Dict[str, Any]) -> str:
    os.makedirs(profile_dir, exist_ok=True)
    path = os.path.join(profile_dir, "profile.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(profile, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return path


def normalize_work_mode(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    text = str(value).strip().lower().replace("_", "-")
    if "remote" in text and "hybrid" not in text and "on-site" not in text and "onsite" not in text:
        return "remote"
    if "hybrid" in text:
        return "hybrid"
    if "on-site" in text or "onsite" in text or "office" in text:
        return "onsite"
    if text in ("any", "flexible", "either"):
        return "any"
    return text


def portals_enabled(profile: Dict[str, Any]) -> bool:
    """Live portal search is opt-in when a profile configures portals.

    No portals key means the legacy pipeline may still search. An explicit
    enabled flag, or a set of portal flags that are all false, turns search off.
    """
    portals = profile.get("portals")
    if portals is None:
        return True
    if isinstance(portals, bool):
        return portals
    if not isinstance(portals, dict):
        return True
    if "enabled" in portals:
        return bool(portals.get("enabled"))
    flags = [value for key, value in portals.items() if isinstance(value, bool)]
    if not flags:
        return True
    return any(flags)


def jobs_per_digest(profile: Dict[str, Any], default: int = 10) -> int:
    raw = profile.get("jobs_per_digest")
    if raw in (None, ""):
        return default
    try:
        count = int(raw)
    except (TypeError, ValueError):
        return default
    return max(1, min(count, 50))


def fixture_path(profile: Dict[str, Any], profile_dir: str, repo_root: str) -> Optional[str]:
    search = profile.get("search") or {}
    raw = search.get("fixture") if isinstance(search, dict) else None
    if not raw:
        return None
    if os.path.isabs(raw) and os.path.exists(raw):
        return raw
    for base in (profile_dir, repo_root):
        candidate = os.path.abspath(os.path.join(base, raw))
        if os.path.exists(candidate) and (_is_within(candidate, repo_root) or _is_within(candidate, profile_dir)):
            return candidate
    return os.path.abspath(os.path.join(repo_root, raw))


def offline_search(profile: Dict[str, Any]) -> bool:
    search = profile.get("search") or {}
    return bool(isinstance(search, dict) and search.get("offline"))


def scoring_overlay(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Map configured fields onto the scorer profile. Unset fields are omitted."""
    overlay: Dict[str, Any] = {}
    if profile.get("name"):
        overlay["name"] = profile["name"]
    if profile.get("target_titles"):
        overlay["target_titles"] = list(profile["target_titles"])
    if profile.get("acceptable_titles"):
        overlay["acceptable_titles"] = list(profile["acceptable_titles"])
    if profile.get("excluded_titles"):
        overlay["excluded_titles"] = list(profile["excluded_titles"])
    if profile.get("seniority"):
        overlay["seniority"] = profile["seniority"]
    if profile.get("locations"):
        overlay["locations"] = list(profile["locations"])
        overlay["location"] = ", ".join(profile["locations"])
    mode = normalize_work_mode(profile.get("work_mode"))
    if mode:
        overlay["work_mode_pref"] = mode
    if profile.get("skills"):
        overlay["proven_skills"] = list(profile["skills"])
    if profile.get("industries"):
        overlay["domain_expertise"] = list(profile["industries"])
    if profile.get("preferred_companies"):
        overlay["preferred_companies"] = list(profile["preferred_companies"])
    salary = profile.get("salary")
    if isinstance(salary, dict) and any(salary.get(key) not in (None, "") for key in ("min", "max", "currency")):
        overlay["salary_expectation"] = salary
    return overlay


def apply_scoring_overlay(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if value in (None, "", [], {}):
            continue
        if key == "proven_skills":
            existing = list(merged.get("proven_skills") or [])
            seen = {item.lower() for item in existing}
            for skill in value:
                if skill.lower() not in seen:
                    existing.append(skill)
                    seen.add(skill.lower())
            merged["proven_skills"] = existing
        elif key == "domain_expertise":
            existing = list(merged.get("domain_expertise") or [])
            seen = {item.lower() for item in existing}
            for item in value:
                if item.lower() not in seen:
                    existing.append(item)
                    seen.add(item.lower())
            merged["domain_expertise"] = existing
        elif key == "target_titles":
            merged["target_titles"] = list(value)
        else:
            merged[key] = value
    return merged


def prefs_from_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    prefs: Dict[str, Any] = {}
    if profile.get("excluded_companies"):
        prefs["excluded_companies"] = [item.lower() for item in profile["excluded_companies"]]
    if profile.get("excluded_titles"):
        prefs["excluded_title_keywords"] = [item.lower() for item in profile["excluded_titles"]]
    salary = profile.get("salary") or {}
    if isinstance(salary, dict) and salary.get("min") not in (None, ""):
        prefs["min_salary"] = float(salary["min"])
    mode = normalize_work_mode(profile.get("work_mode"))
    if mode:
        prefs["work_mode"] = mode
    if profile.get("locations"):
        prefs["allowed_locations"] = list(profile["locations"])
    if profile.get("target_titles"):
        prefs["target_titles"] = list(profile["target_titles"])
    return prefs


def weights_from_priorities(profile: Dict[str, Any]) -> Optional[Dict[str, float]]:
    priorities = profile.get("priorities")
    if not isinstance(priorities, dict) or not priorities:
        return None
    weights = {}
    for key in WEIGHT_KEYS:
        if key not in priorities:
            continue
        try:
            weights[key] = float(priorities[key])
        except (TypeError, ValueError):
            continue
    if not weights:
        return None
    # Fill any omitted dimension with 0 so a user can emphasize one factor.
    for key in WEIGHT_KEYS:
        weights.setdefault(key, 0.0)
    total = sum(weights.values())
    if total <= 0:
        return None
    return {key: value / total for key, value in weights.items()}


def profile_dirs(profile_dir: str) -> Dict[str, str]:
    jobs_dir = os.path.join(profile_dir, "jobs")
    output_dir = os.path.join(profile_dir, "output")
    return {
        "profile": os.path.abspath(profile_dir),
        "jobs": os.path.abspath(jobs_dir),
        "output": os.path.abspath(output_dir),
        "history": os.path.abspath(os.path.join(jobs_dir, "history.json")),
    }


def assert_isolated_write(path: str, profile_dir: str) -> None:
    """Refuse to write a profile artifact outside that profile directory."""
    if not _is_within(path, profile_dir):
        raise ValueError(f"Refusing to write outside profile directory: {path}")


def notification_preferences(profile: Dict[str, Any]) -> Dict[str, Any]:
    raw = profile.get("notification") or {}
    if isinstance(raw, str):
        raw = {"channel": raw}
    if not isinstance(raw, dict):
        raw = {}
    channel = (raw.get("channel") or "file").strip().lower()
    return {"channel": channel, "to": raw.get("to") or None}


def preflight(profile_dir: str, repo_root: Optional[str] = None) -> Dict[str, Any]:
    """Report blockers and warnings. Warnings do not fail setup."""
    root = os.path.abspath(repo_root or repo_root_from_here())
    blockers: List[str] = []
    warnings: List[str] = []
    checks: List[str] = []

    if not os.path.isdir(profile_dir):
        blockers.append(f"Profile directory does not exist: {profile_dir}")
        return {"ok": False, "blockers": blockers, "warnings": warnings, "checks": checks, "profile_dir": profile_dir}

    if not _is_within(profile_dir, root):
        blockers.append("Profile directory is outside the repository. Refusing to use it.")

    profile_path = os.path.join(profile_dir, "profile.json")
    profile: Dict[str, Any] = {}
    if os.path.exists(profile_path):
        try:
            profile = load_user_profile(profile_dir)
            checks.append("profile.json parses")
        except Exception as exc:
            blockers.append(f"profile.json is invalid: {exc}")
    else:
        warnings.append("profile.json is missing. Markdown profile files will be used if present.")

    master = os.path.join(profile_dir, "MASTER_PROFILE.md")
    source = None
    if profile.get("source_resume"):
        source = profile["source_resume"]
        if not os.path.isabs(source):
            source = os.path.join(profile_dir, source)
    has_master = os.path.exists(master)
    has_source = bool(source and os.path.exists(source))
    if has_master:
        checks.append("MASTER_PROFILE.md is present")
    if has_source:
        checks.append(f"source resume is present ({os.path.basename(source)})")
    if not has_master and not has_source:
        blockers.append(
            "No career source. Add a resume file or MASTER_PROFILE.md. "
            "No other field is required before that."
        )

    if profile and not profile.get("target_titles"):
        warnings.append("target_titles is empty. Search will use the current title in the profile, if one is written there.")
    if profile and not profile.get("salary"):
        warnings.append("salary is not set. Posted pay will still be shown. Jobs will not be filtered by pay.")
    if profile and not profile.get("work_authorization"):
        warnings.append("work_authorization is not set. It will be left blank rather than guessed.")

    if profile:
        if portals_enabled(profile):
            warnings.append("Job portals are enabled. A run will query live employer boards.")
        else:
            fixture = fixture_path(profile, profile_dir, root) if profile.get("search") else None
            if fixture and os.path.exists(fixture):
                checks.append(f"portals disabled; fixture search will be used ({os.path.basename(fixture)})")
            else:
                warnings.append(
                    "Job portals are disabled and no fixture is configured. "
                    "A run will not search the network. The digest will say that search was skipped."
                )

        note = notification_preferences(profile)
        if note["channel"] == "email":
            if not note["to"] and not os.environ.get("JOB_AGENT_EMAIL_TO") and not os.environ.get("SMTP_TO"):
                warnings.append("Email notification is selected, but no recipient is configured. The digest will be saved to disk.")
            has_transport = bool(os.environ.get("RESEND_API_KEY") or os.environ.get("SMTP_HOST"))
            if not has_transport:
                warnings.append("Email credentials are absent. The digest will be saved instead of failing the search.")
        else:
            checks.append(f"notification channel is '{note['channel']}' (digest is saved with the profile)")

    gitignore = os.path.join(root, ".gitignore")
    if os.path.exists(gitignore):
        with open(gitignore, "r", encoding="utf-8") as handle:
            ignored = handle.read()
        if "profiles" not in ignored:
            warnings.append(".gitignore does not mention profiles/. Real client directories can be committed by mistake.")
        else:
            checks.append("profiles/ is gitignored")
    else:
        blockers.append(".gitignore is missing")

    return {
        "ok": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "checks": checks,
        "profile_dir": os.path.abspath(profile_dir),
        "profile": profile,
    }


def format_preflight(report: Dict[str, Any]) -> str:
    lines = ["Profile preflight", f"Directory: {report.get('profile_dir', '')}", ""]
    if report.get("checks"):
        lines.append("Ready:")
        for item in report["checks"]:
            lines.append(f"  + {item}")
        lines.append("")
    if report.get("warnings"):
        lines.append("Warnings (setup can continue):")
        for item in report["warnings"]:
            lines.append(f"  ! {item}")
        lines.append("")
    if report.get("blockers"):
        lines.append("Missing requirements:")
        for item in report["blockers"]:
            lines.append(f"  x {item}")
        lines.append("")
    lines.append("Result: READY" if report.get("ok") else "Result: NOT READY")
    return "\n".join(lines)


def init_profile(name: str, repo_root: str, source_dir: Optional[str] = None) -> str:
    """Create profiles/<name> from a template or copy an example directory."""
    cleaned = validate_profile_name(name)
    dest = os.path.join(repo_root, "profiles", cleaned)
    if not _is_within(dest, os.path.join(repo_root, "profiles")):
        raise ValueError("Refusing to initialize a profile outside profiles/")
    os.makedirs(dest, exist_ok=True)
    os.makedirs(os.path.join(dest, "jobs"), exist_ok=True)
    os.makedirs(os.path.join(dest, "output"), exist_ok=True)

    if source_dir:
        source_dir = os.path.abspath(source_dir)
        if not os.path.isdir(source_dir):
            raise FileNotFoundError(source_dir)
        for filename in (
            "profile.json",
            "resume.md",
            "MASTER_PROFILE.md",
            "SEARCH_PREFERENCES.md",
            "VERIFIED_ACHIEVEMENTS.md",
            "CAREER_STORIES.md",
            "skills.json",
        ):
            src = os.path.join(source_dir, filename)
            if os.path.exists(src):
                with open(src, "r", encoding="utf-8") as handle:
                    text = handle.read()
                target = os.path.join(dest, filename)
                assert_isolated_write(target, dest)
                with open(target, "w", encoding="utf-8") as handle:
                    handle.write(text)
        fixture_src = os.path.join(source_dir, "fixtures")
        if os.path.isdir(fixture_src):
            fixture_dest = os.path.join(dest, "fixtures")
            os.makedirs(fixture_dest, exist_ok=True)
            for filename in os.listdir(fixture_src):
                src = os.path.join(fixture_src, filename)
                if not os.path.isfile(src):
                    continue
                with open(src, "r", encoding="utf-8") as handle:
                    text = handle.read()
                target = os.path.join(fixture_dest, filename)
                assert_isolated_write(target, dest)
                with open(target, "w", encoding="utf-8") as handle:
                    handle.write(text)
    if not os.path.exists(os.path.join(dest, "profile.json")):
        template = os.path.join(repo_root, "templates", "profile.template.json")
        if os.path.exists(template):
            with open(template, "r", encoding="utf-8") as handle:
                profile = json.load(handle)
        else:
            profile = empty_profile(cleaned)
        profile["name"] = profile.get("name") or cleaned
        save_user_profile(dest, profile)
    else:
        profile = load_user_profile(dest)
        if not profile.get("name"):
            profile["name"] = cleaned
            save_user_profile(dest, profile)
    return dest
