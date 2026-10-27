#!/usr/bin/env python3
import argparse, json, re, subprocess, sys, urllib.request
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/chat"
KEY_FILES = ["requirements.txt", "pyproject.toml", "package.json", "go.mod",
             "pom.xml", "Cargo.toml", "app.py", "main.py", "server.js",
             "index.js", "main.go", "README.md"]
IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}

SYSTEM_PROMPT = """You are a DevOps expert. Write a production-quality Dockerfile for the project described.
Rules:
- Use a small, specific base image tag (never 'latest').
- Copy dependency files first, then the rest of the code.
- Run as a non-root user where practical.
- Output ONLY the Dockerfile contents. No explanations, no markdown fences."""

def project_context(root):
    tree = []
    for p in sorted(root.rglob("*")):
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        rel = p.relative_to(root)
        if len(rel.parts) <= 2:
            tree.append(str(rel))
    parts = ["FILE TREE:\n" + "\n".join(tree[:80])]
    for name in KEY_FILES:
        f = root / name
        if f.is_file():
            parts.append("--- %s ---\n%s" % (name, f.read_text(errors="ignore")[:2000]))
    return "\n\n".join(parts)

def chat(model, messages):
    body = json.dumps({"model": model, "messages": messages, "stream": False}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.load(r)["message"]["content"]
    except OSError as e:
        sys.exit("Could not reach Ollama. Is it running? (%s)" % e)

def clean(reply):
    m = re.search(r"```(?:dockerfile|Dockerfile)?\n(.*?)```", reply, re.S)
    return (m.group(1) if m else reply).strip() + "\n"

def docker_build(root):
    r = subprocess.run(["docker", "build", "-t", "llm-generated-test", str(root)],
                       capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr)[-3000:]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--model", default="qwen2.5-coder:3b")
    ap.add_argument("--retries", type=int, default=3)
    args = ap.parse_args()
    root = Path(args.project).resolve()
    if not root.is_dir():
        sys.exit("%s is not a directory" % root)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Write a Dockerfile for this project:\n\n" + project_context(root)},
    ]
    for attempt in range(1, args.retries + 2):
        print("\n[attempt %d] asking %s ..." % (attempt, args.model))
        reply = chat(args.model, messages)
        dockerfile = clean(reply)
        (root / "Dockerfile").write_text(dockerfile)
        print(dockerfile)
        print("[build] running docker build ...")
        ok, log = docker_build(root)
        if ok:
            print("\nBuild succeeded. Dockerfile saved to", root / "Dockerfile")
            return
        print("[build] FAILED. Sending error back to the model.\n")
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content":
            "That Dockerfile failed to build with this error:\n\n%s\n\nFix it. Output ONLY the corrected Dockerfile." % log})
    sys.exit("Gave up. Read the last error yourself.")

if __name__ == "__main__":
    main()
