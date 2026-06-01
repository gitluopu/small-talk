#!/usr/bin/env python3
"""
过滤满足条件的 open issue，再调用 small-talk agent 回复。

触发条件：issue 处于 open 状态，且最后一条评论的作者是 gitluopu
（如果 issue 还没有任何评论，则检查 issue 本身的作者是否是 gitluopu）。
"""
import json
import subprocess
import sys

OWNER_LOGIN = "gitluopu"
BOT_LOGIN = "ai-paul[bot]"


def gh(*args: str) -> str:
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_qualifying_issues() -> list[int]:
    raw = gh("issue", "list", "--state", "open", "--json", "number")
    issues = json.loads(raw)

    qualifying = []
    for issue in issues:
        number = issue["number"]
        detail = json.loads(gh("issue", "view", str(number), "--json", "author,comments"))

        comments = detail.get("comments", [])
        if not comments:
            # 没有评论：bot 尚未回复，只有在 issue 由 gitluopu 开启时才处理
            if detail.get("author", {}).get("login") == OWNER_LOGIN:
                qualifying.append(number)
        else:
            last_author = comments[-1].get("author", {}).get("login", "")
            if last_author == OWNER_LOGIN:
                qualifying.append(number)

    return qualifying


def main() -> None:
    qualifying = get_qualifying_issues()

    if not qualifying:
        print("No qualifying issues.")
        sys.exit(0)

    issue_list = ", ".join(f"#{n}" for n in qualifying)
    print(f"Qualifying issue(s): {issue_list}. Invoking small-talk agent...")

    subprocess.run(
        [
            "claude",
            "-p", f"处理以下 open issues 并回复：{issue_list}",
            "--agent", "small-talk",
            "--dangerously-skip-permissions",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
