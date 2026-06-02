#!/usr/bin/env python3
"""
过滤满足条件的 open issue，再调用 small-talk agent 回复。

触发条件：issue 处于 open 状态，且最新 timeline activity 的操作者名字中不包含 "bot"。
"""
import json
import subprocess
import sys


def gh(*args: str) -> str:
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_repo() -> tuple[str, str]:
    info = json.loads(gh("repo", "view", "--json", "owner,name"))
    return info["owner"]["login"], info["name"]


def get_qualifying_issues() -> list[int]:
    owner, repo = get_repo()
    raw = gh("issue", "list", "--state", "open", "--json", "number,author")
    issues = json.loads(raw)

    qualifying = []
    for issue in issues:
        number = issue["number"]
        issue_author = issue["author"]["login"]

        # REST timeline 包含所有类型的 activity（评论、打标签、关闭等）
        # 评论事件用 user 字段，其余事件用 actor 字段
        timeline = json.loads(
            gh("api", "--paginate", f"/repos/{owner}/{repo}/issues/{number}/timeline")
        )

        if timeline:
            last = timeline[-1]
            last_actor = (last.get("actor") or last.get("user") or {}).get("login", "")
        else:
            last_actor = issue_author

        if last_actor and "bot" not in last_actor.lower():
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
