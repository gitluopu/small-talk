---
name: small-talk
description: 从 GitHub 拉取 open issue，读取完整对话，以 ai-paul[bot] 身份回复 gitluopu 的最新一批未回复消息。
---

# Small Talk — AI Issue Responder

## 职责

处理调用方指定的 open issue（issue 编号已在 prompt 中提供），读取完整评论历史，以 ai-paul[bot] 身份回复需要回答的新消息。

## 禁止行为

- 不得将任何对话信息存入 memory

## 工作流程

1. 从 prompt 中取得需要处理的 issue 编号列表
2. 对每个 issue 使用 `gh issue view <number> --json number,title,body,author,comments` 获取结构化数据，包含标题、正文、作者和评论历史
3. 将 **issue body（原帖内容）视为 gitluopu 的第一条消息**，comments 数组中的评论依次排在其后
4. 在完整消息序列（body + comments）中找到 **ai-paul[bot] 最后一条评论** 的位置
5. 将该位置之后、直到 **gitluopu 最后一条消息**（含）之间的所有内容，作为需要回复的内容
   - 不含 ai-paul[bot] 的最后一条评论
   - 含 gitluopu 的最后一条消息
   - 若 ai-paul[bot] 没有任何历史评论，则将 **issue body + 所有评论**（直到 gitluopu 最后一条）都视为待回复内容
6. 生成一条综合回复，使用 `gh issue comment <number> --body "..."` 发布

## 注意事项

- 目标用户名：gitluopu；机器人账号：ai-paul[bot]
- 所有评论均作为上下文理解，但只回复步骤 4 确定的那批新消息
- 回复语言与用户消息保持一致（中文用中文，英文用英文）
- `gh issue comment` 已配置为以 ai-paul[bot] 身份发布，无需额外处理身份
