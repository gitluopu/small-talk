#!/usr/bin/env python3
"""
过滤满足条件的 open issue，调用 Anthropic API 生成回复并发布。

触发条件：issue 处于 open 状态，且最后一条评论的作者是 gitluopu
（如果 issue 还没有任何评论，则检查 issue 本身的作者是否是 gitluopu）。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import anthropic

OWNER_LOGIN = os.environ.get("OWNER_LOGIN", "gitluopu")
BOT_LOGIN = "ai-paul[bot]"
MODEL = "claude-opus-4-8"
AGENT_PROMPT_PATH = Path(__file__).parent / ".claude" / "agents" / "small-talk.md"

_FALLBACK_SYSTEM_PROMPT = """\
你是 ai-paul[bot]，GitHub issue 的自动回复机器人。
读取提供的 issue 内容（标题、正文、评论历史），生成一条综合回复。
回复语言与用户消息保持一致（中文用中文，英文用英文）。
只返回回复正文，不要包含任何额外说明或命令。\
"""


def gh(*args: str) -> str:
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def load_system_prompt() -> str:
    """Load system prompt from agent definition file, stripping YAML frontmatter."""
    if not AGENT_PROMPT_PATH.exists():
        return _FALLBACK_SYSTEM_PROMPT
    content = AGENT_PROMPT_PATH.read_text()
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].strip()
            # Replace the gh command step with a plain instruction
            body += (
                "\n\n**重要**：只返回回复的正文内容，"
                "系统会自动通过 `gh issue comment` 发布，无需包含命令或额外说明。"
            )
            return body
    return content


def get_qualifying_issues() -> list[int]:
    raw = gh("issue", "list", "--state", "open", "--json", "number")
    issues = json.loads(raw)

    qualifying = []
    for issue in issues:
        number = issue["number"]
        detail = json.loads(gh("issue", "view", str(number), "--json", "author,comments"))

        comments = detail.get("comments", [])
        if not comments:
            if detail.get("author", {}).get("login") == OWNER_LOGIN:
                qualifying.append(number)
        else:
            last_author = comments[-1].get("author", {}).get("login", "")
            if last_author == OWNER_LOGIN:
                qualifying.append(number)

    return qualifying


def build_issue_context(number: int) -> str:
    detail = json.loads(
        gh("issue", "view", str(number), "--json", "number,title,body,author,comments")
    )

    title = detail.get("title", "")
    body = detail.get("body", "")
    author = detail.get("author", {}).get("login", "unknown")
    comments = detail.get("comments", [])

    context = f"Issue #{number} by {author}: {title}\n\n{body}"

    if comments:
        context += "\n\n--- 评论记录 ---"
        for c in comments:
            c_author = c.get("author", {}).get("login", "unknown")
            c_body = c.get("body", "")
            context += f"\n\n**{c_author}**: {c_body}"

    return context


def process_issue(number: int, client: anthropic.Anthropic, system_prompt: str) -> None:
    context = build_issue_context(number)

    message = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": (
                    "请处理以下 GitHub issue，生成回复内容"
                    "（只返回回复正文）：\n\n" + context
                ),
            }
        ],
    )

    reply_text = message.content[0].text
    gh("issue", "comment", str(number), "--body", reply_text)
    print(f"Replied to issue #{number}")


def main() -> None:
    qualifying = get_qualifying_issues()

    if not qualifying:
        print("No qualifying issues.")
        sys.exit(0)

    issue_list = ", ".join(f"#{n}" for n in qualifying)
    print(f"Qualifying issue(s): {issue_list}. Generating replies...")

    client = anthropic.Anthropic()
    system_prompt = load_system_prompt()

    for number in qualifying:
        try:
            process_issue(number, client, system_prompt)
        except Exception as e:
            print(f"Error processing issue #{number}: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
