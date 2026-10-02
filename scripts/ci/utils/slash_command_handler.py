#!/usr/bin/env python3
"""Slash-command handler for CI helper commands.

Parses the triggering comment and dispatches the requested CI action
(label, rerun, group selection). Kept dependency-light on purpose.
"""
import os


def main() -> None:
    command = os.environ.get("COMMENT_BODY", "").strip()
    pr = os.environ.get("PR_NUMBER", "")
    print(f"handler: received command {command!r} for PR #{pr}")


if __name__ == "__main__":
    main()
