#!/usr/bin/env python3
"""
用 ghi-ctx 过滤需要回复的 open issue，再调用 small-talk agent 逐条回复。
"""
import json
import subprocess
import sys

REPO = "gitluopu/small-talk"


def main() -> None:
    result = subprocess.run(
        ["ghi-ctx", REPO],
        capture_output=True,
        text=True,
        check=True,
    )
    output = json.loads(result.stdout)

    if not output["needHandleIssue"]:
        print("No qualifying issues.")
        sys.exit(0)

    procs = []
    for issue in output["issues"]:
        issue_id = issue["issueId"]
        context = issue["context"]
        problem = issue["problem"]
        print(f"Handling issue #{issue_id}...")
        proc = subprocess.Popen(
            [
                "claude",
                "-p",
                f"回复 issue #{issue_id}。\n\n ## 对话历史\n{context}\n\n## 待回复内容\n{problem}",
                "--agent", "small-talk",
                "--dangerously-skip-permissions",
            ],
        )
        procs.append((issue_id, proc))

    for issue_id, proc in procs:
        code = proc.wait()
        if code != 0:
            print(f"Issue #{issue_id} failed with exit code {code}", file=sys.stderr)


if __name__ == "__main__":
    main()
