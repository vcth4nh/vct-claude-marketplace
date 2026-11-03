#!/usr/bin/env python3
"""Run pinned writing cases through Claude Code or Codex in isolated workspaces.

Input is an array of cases (or an object with a ``cases`` array). Required
fields: id, source, mode. Optional: audience, request, questions, target,
companions, setup_files. Companion and setup entries have source and optional
target fields. Setup files (such as private glossaries) are installed in the
workspace but are not named as public companions in the prompt. Sources
are absolute or relative to the case manifest; targets are workspace-relative.
Only these raw inputs enter prompts. Assessment keys belong in separate files.

Example:
  python3 run_native.py cases.json --output /tmp/writing-eval-001 --jobs 2
  python3 run_native.py cases.json --output /tmp/writing-plan --dry-run

This records behavior, not pass/fail judgments. Inspect the reports, edits,
and reviewer handoffs before assessing quality or sequential isolation.
"""

import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time


REPO = Path(__file__).resolve().parents[3]
MODES = {
    "ordinary": ("public-hygiene", "cold-read", ""),
    "comprehension": ("public-hygiene", "cold-read", "comprehension"),
    "sequential": ("public-hygiene", "cold-read", "sequential"),
    "sequential-comprehension": ("public-hygiene", "cold-read", "sequential comprehension"),
    "deslop": ("anti-slop", "deslop", ""),
    "academic": ("anti-slop", "academic-voice", ""),
    "leak": ("public-hygiene", "leak-check", ""),
}
STYLE_MODES = {"deslop", "academic"}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(directory):
    return {str(p.relative_to(directory)): sha256(p)
            for p in sorted(directory.rglob("*")) if p.is_file()}


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def target_path(value):
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"Target must be a nonempty workspace-relative file: {value!r}")
    return path


def read_cases(path, selected, baseline):
    value = json.loads(path.read_text(encoding="utf-8"))
    cases = value["cases"] if isinstance(value, dict) else value
    if not isinstance(cases, list) or not cases:
        raise ValueError("The manifest must contain a nonempty array of cases")
    seen = set()
    prepared = []
    for case in cases:
        name = case["id"]
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name):
            raise ValueError(f"Invalid case id: {name!r}")
        if name in seen:
            raise ValueError(f"Duplicate case id: {name}")
        seen.add(name)
        if selected and name not in selected:
            continue
        if case["mode"] not in MODES:
            raise ValueError(f"Unknown mode in {name}: {case['mode']}")
        if baseline and case["mode"] not in STYLE_MODES:
            raise ValueError("--baseline currently supports only deslop and academic cases")
        files = []
        targets = set()
        for item in [case, *case.get("companions", []), *case.get("setup_files", [])]:
            source = (path.parent / item["source"]).resolve()
            if not source.is_file():
                raise ValueError(f"Missing source for {name}: {source}")
            target = target_path(item.get("target", source.name))
            if str(target) in targets:
                raise ValueError(f"Repeated target in {name}: {target}")
            targets.add(str(target))
            files.append({"source": str(source), "target": str(target),
                          "sha256": sha256(source)})
        for field in ("audience", "request"):
            if field in case and not isinstance(case[field], str):
                raise ValueError(f"{field} must be a string in {name}")
        if not isinstance(case.get("questions", []), list) or any(
                not isinstance(q, str) for q in case.get("questions", [])):
            raise ValueError(f"questions must be an array of strings in {name}")
        prepared.append({"raw": case, "files": files})
    missing = set(selected) - seen
    if missing:
        raise ValueError("Unknown selected case(s): " + ", ".join(sorted(missing)))
    return prepared


def make_prompt(case, files, scratch, args):
    plugin, skill, mode = MODES[case["mode"]]
    target = files[0]["target"]
    companions = [f["target"] for f in files[1:1 + len(case.get("companions", []))]]
    lines = []
    if args.baseline:
        lines.append("Use general writing judgment for this baseline. Do not load or apply any skills.")
    elif args.backend == "codex":
        skill_path = args.output / "plugins" / plugin / "skills" / skill / "SKILL.md"
        lines.append(f"Use the {plugin}:{skill} skill at {skill_path} and its bundled references.")
        lines.append("Use that exact snapshot, not a cached or installed version of the skill.")
        lines.append("Invocation: " + skill + " " + (mode + " " if mode else "")
                     + " ".join([target, *companions]))
    else:
        lines.append("/" + plugin + ":" + skill + " " + (mode + " " if mode else "")
                     + " ".join([target, *companions]))
    if case["mode"] in STYLE_MODES:
        lines.append(f"Edit {target} in place to improve its writing for the audience below.")
        lines.append("Keep its meaning and factual claims intact. Give a brief summary of changes.")
        lines.append(f"Only {target} may be changed. Companion files are read-only.")
    else:
        lines.append(f"Review {target}. Keep all source and companion files unchanged.")
        if case["mode"].startswith("sequential"):
            lines.append(f"Temporary preparation files may be written only under {scratch}/.")
    if case.get("audience"):
        lines.append("Audience: " + case["audience"])
    if companions:
        lines.append("Public companions: " + ", ".join(companions))
    if case.get("request"):
        lines.append(case["request"])
    if case.get("questions"):
        lines.append("Questions to test:\n" + "\n".join(case["questions"]))
    return "\n".join(lines) + "\n"


def prepare_case(prepared, args):
    case, files = prepared["raw"], prepared["files"]
    run = args.output / "runs" / case["id"]
    work, before_dir, scratch = run / "work", run / "before", run / "scratch"
    for directory in (work, before_dir, scratch):
        directory.mkdir(parents=True)
    for item in files:
        for directory in (work, before_dir):
            target = directory / item["target"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item["source"], target)
        # Review tools do not include writes. File mode is a second accidental-write guard.
        if case["mode"] not in STYLE_MODES or item is not files[0]:
            (work / item["target"]).chmod(0o444)
    prompt = make_prompt(case, files, scratch, args)
    (run / "prompt.txt").write_text(prompt, encoding="utf-8")
    save_json(run / "case.json", case)
    save_json(run / "inputs.json", files)
    save_json(run / "before.json", hashes(work))

    allowed = ["Read", "Grep", "Glob", "Skill"]
    tools = ["Read", "Grep", "Glob", "Skill"]
    if case["mode"] in STYLE_MODES:
        tools += ["Edit", "Write"]
        allowed += ["Edit(/" + str(work / files[0]["target"]) + ")"]
    else:
        tools += ["Agent"]
        allowed += ["Agent"]
    if case["mode"].startswith("sequential"):
        # Claude's Edit path rules cover Write too. These trusted-fixture runs are
        # instruction-isolated, not OS-sandboxed; inspect actual Bash/reader accesses.
        tools += ["Bash", "Write"]
        allowed += ["Bash(python3 *)", "Bash(mkdir *)", "Edit(/" + str(scratch) + "/**)"]
    if args.backend == "codex":
        sandbox = "workspace-write" if case["mode"] in STYLE_MODES or case["mode"].startswith("sequential") else "read-only"
        if args.codex_sandbox != "auto":
            sandbox = args.codex_sandbox
        command = [args.codex, "exec", "--ignore-user-config", "--ignore-rules",
                   "--skip-git-repo-check", "--ephemeral", "--json", "--sandbox", sandbox,
                   "-c", 'approval_policy="never"',
                   "-C", str(work), "--add-dir", str(scratch),
                   "-o", str(run / "report.txt"), prompt]
    else:
        command = [args.claude, "-p", prompt, "--setting-sources", "",
                   "--settings", '{"autoMemoryEnabled":false}', "--strict-mcp-config",
                   "--tools", ",".join(tools), "--allowedTools", *allowed,
                   "--add-dir", str(scratch), "--permission-mode", "dontAsk",
                   "--no-session-persistence", "--max-budget-usd", str(args.max_budget_usd),
                   "--output-format", "stream-json", "--verbose", "--forward-subagent-text"]
        if not args.baseline:
            command += ["--plugin-dir", str(args.output / "plugins" / MODES[case["mode"]][0])]
    save_json(run / "invocation.json", {"command": command, "cwd": str(work),
                                       "baseline": args.baseline, "backend": args.backend})
    return run


def collect_result(run, code, elapsed, timed_out, backend):
    before = json.loads((run / "before.json").read_text(encoding="utf-8"))
    after = hashes(run / "work")
    save_json(run / "after.json", after)
    changed = [p for p in sorted(set(before) | set(after)) if before.get(p) != after.get(p)]
    result = {"id": run.name, "backend": backend, "exit_code": code, "elapsed_seconds": round(elapsed, 2),
              "quality_assessed": False,
              "timed_out": timed_out, "changed_files": changed,
              "changed_input_files": [p for p in changed if p in before],
              "created_files": [p for p in changed if p not in before],
              "scratch_files": hashes(run / "scratch")}
    original_changes = []
    for item in json.loads((run / "inputs.json").read_text(encoding="utf-8")):
        source = Path(item["source"])
        if not source.is_file() or sha256(source) != item["sha256"]:
            original_changes.append(str(source))
    result["original_sources_changed"] = original_changes
    final, trace, parse_errors, codex_errors = None, [], [], []
    with (run / "log.jsonl").open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                parse_errors.append(number)
                continue
            if event.get("type") == "system" and event.get("subtype") == "init":
                result["model"] = event.get("model")
            if event.get("type") == "result":
                final = event
            if backend == "codex":
                if event.get("type") == "turn.completed":
                    final = event
                if event.get("type") in ("error", "turn.failed"):
                    codex_errors.append(event)
                if "item" in event:
                    trace.append({"log_line": number, **event})
                continue
            message = event.get("message", {})
            if not isinstance(message, dict):
                continue
            for block in message.get("content", []):
                if isinstance(block, dict) and block.get("type") in ("tool_use", "tool_result", "text"):
                    trace.append({"log_line": number, "parent_tool_use_id": event.get("parent_tool_use_id"),
                                  "role": event.get("type"), **block})
    result["log_parse_error_lines"] = parse_errors
    result["result_received"] = final is not None
    if backend == "codex":
        result.update({"model": None, "model_note": "CLI default; the JSON event stream does not identify the model.",
                       "cost_usd": None, "budget_note": "Codex CLI has no per-run USD cap; only timeout is enforced.",
                       "is_error": bool(code or codex_errors), "errors": codex_errors,
                       "result_subtype": "completed" if final else "incomplete"})
        if final is not None:
            result["usage"] = final.get("usage")
            save_json(run / "result.json", final)
    elif final is not None:
        result.update({"result_subtype": final.get("subtype"), "is_error": final.get("is_error"),
                       "cost_usd": final.get("total_cost_usd"), "usage": final.get("usage"),
                       "model_usage": final.get("modelUsage")})
        (run / "report.txt").write_text(final.get("result", "") + "\n", encoding="utf-8")
        save_json(run / "result.json", final)
    save_json(run / "trace.json", trace)
    save_json(run / "completion.json", result)
    return result


def execute(run, timeout):
    invocation = json.loads((run / "invocation.json").read_text(encoding="utf-8"))
    save_json(run / "started.json", {"started_at": now()})
    print("START " + run.name, flush=True)
    started, timed_out = time.monotonic(), False
    with (run / "log.jsonl").open("x", encoding="utf-8") as out, (run / "stderr.txt").open("x") as err:
        process = subprocess.Popen(invocation["command"], cwd=invocation["cwd"],
                                   stdout=out, stderr=err, start_new_session=True)
        (run / "pid").write_text(str(process.pid) + "\n")
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            code = 124
    result = collect_result(run, code, time.monotonic() - started, timed_out, invocation["backend"])
    print("DONE " + json.dumps({k: result.get(k) for k in (
        "id", "exit_code", "result_subtype", "elapsed_seconds", "cost_usd", "changed_files")}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", required=True, type=Path, help="New output directory; never overwritten")
    parser.add_argument("--plugin-root", type=Path, default=REPO / "plugins")
    parser.add_argument("--case", action="append", default=[], help="Select an id; repeat to select several")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--max-budget-usd", type=float, default=6)
    parser.add_argument("--timeout", type=float, default=600, help="Seconds per invocation")
    parser.add_argument("--claude", default="claude")
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--backend", choices=("claude", "codex"), default="claude")
    parser.add_argument("--codex-sandbox", choices=("auto", "read-only", "workspace-write", "danger-full-access"),
                        default="auto", help="Default: read-only reviews, workspace-write edits/sequence; override only when needed")
    parser.add_argument("--dry-run", action="store_true", help="Prepare inputs/commands without invoking a model")
    parser.add_argument("--baseline", action="store_true", help="Style cases only: same editing request without plugin")
    args = parser.parse_args()
    if args.jobs < 1 or args.max_budget_usd <= 0 or args.timeout <= 0:
        parser.error("jobs, max-budget-usd, and timeout must be positive")
    args.manifest, args.output, args.plugin_root = (
        p.resolve() for p in (args.manifest, args.output, args.plugin_root))
    try:
        cases = read_cases(args.manifest, args.case, args.baseline)
        args.output.mkdir(parents=True, exist_ok=False)
        plugins = {}
        if not args.baseline:
            for name in sorted({MODES[c["raw"]["mode"]][0] for c in cases}):
                destination = args.output / "plugins" / name
                shutil.copytree(args.plugin_root / name, destination,
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                plugins[name] = hashes(destination)
        try:
            revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            revision = None
        metadata = {"created_at": now(), "git_head": revision, "plugin_files": plugins,
                    "runner_sha256": sha256(Path(__file__)), "manifest_sha256": sha256(args.manifest),
                    "baseline": args.baseline, "dry_run": args.dry_run, "backend": args.backend,
                    "codex_sandbox": args.codex_sandbox if args.backend == "codex" else None}
        if not args.dry_run:
            executable = args.codex if args.backend == "codex" else args.claude
            metadata["cli_version"] = subprocess.check_output(
                [executable, "--version"], text=True, timeout=20).strip()
        save_json(args.output / "snapshot.json", metadata)
        runs = [prepare_case(case, args) for case in cases]
        if args.dry_run:
            print(f"Prepared {len(runs)} case(s) in {args.output}; no model invoked.")
            return 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            results = list(pool.map(lambda run: execute(run, args.timeout), runs))
        save_json(args.output / "results.json", results)
        return int(any(r["exit_code"] != 0 or not r["result_received"] or r.get("is_error") for r in results))
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
