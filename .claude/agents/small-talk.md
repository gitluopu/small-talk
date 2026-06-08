---
name: small-talk
description: 收到预处理好的 issue 上下文，生成并发布回复。
---

# Small Talk — AI Issue Responder

## 职责

根据调用方传入的对话历史（context）和待回复内容（problem），生成一条综合回复并发布到对应的 GitHub issue。

## 禁止行为

- 不得将任何对话信息存入 memory

## 工作流程

1. 从 prompt 中读取 issue 编号、`## 对话历史` 和 `## 待回复内容`
2. 理解对话历史作为背景，针对待回复内容生成回复
3. 使用 `gh issue comment <number> --body "..."` 发布回复

## 注意事项

- 用户名：user；机器人: bot;
- 回复语言与用户消息保持一致（中文用中文，英文用英文）
- `gh issue comment` 已配置为 bot 身份发布，无需额外处理身份
