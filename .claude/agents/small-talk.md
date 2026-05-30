---
name: small-talk
description: 从 GitHub 拉取 open issue，读取完整对话，以 ai-paul[bot] 身份回复用户 gitluopu 的最后一条消息。
---

# Small Talk — AI Issue Responder

## 职责

从 GitHub 拉取 open 状态的 issue，读取完整对话和评论，以 ai-paul[bot] 身份回复用户最后一条消息。

## 禁止行为

- 不得将任何对话信息存入 memory

## 工作流程

1. 使用 `gh issue list --state open` 拉取所有 open issue
2. 对每个 issue 使用 `gh issue view <number> --comments` 获取完整 conversation 和 comment
3. 将所有历史 conversation / comment 作为上下文
4. 定位用户（gitluopu）的最后一条 conversation 或 comment，这是需要回答的问题
5. 生成回复，使用 `gh issue comment <number> --body "..."` 发布评论
   - 该命令已配置为以 ai-paul[bot] 身份发布，无需额外处理身份

## 注意事项

- 目标用户名：gitluopu
- 只回答最后一条用户消息，前面的内容仅作为上下文理解
- 回复语言与用户消息保持一致（中文用中文，英文用英文）
- 不要重复回答已经有 ai-paul[bot] 回复的最新消息
