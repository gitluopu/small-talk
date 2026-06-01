# Design: GitHub Actions 自动化 + Anthropic SDK 重构

## 背景

当前 `small-talk` bot 需要手动执行 `run.sh` 才能回复 issue，没有自动化触发机制。
`main.py` 依赖本地安装的 `claude` CLI（`--agent small-talk --dangerously-skip-permissions`），
无法在标准 GitHub-hosted runner 上运行。

Issue #5（股市问题）由 `gitluopu` 提出后长期未收到自动回复，正是缺乏自动化的直接体现。

## 方案

### 1. 重构 `main.py`：以 Anthropic Python SDK 替代 claude CLI

**改动**：将 `subprocess.run(["claude", ...])` 替换为直接调用 `anthropic.Anthropic().messages.create()`。

优点：
- 无需在运行环境安装 claude CLI
- 标准 GitHub-hosted runner 可直接使用
- 错误处理更精确，逐个 issue 可捕获异常

系统提示从 `.claude/agents/small-talk.md` 中动态加载（去除 frontmatter），
最终 prompt 附加说明：只返回回复正文，由 Python 调用 `gh issue comment` 发布。

### 2. 新增 GitHub Actions Workflow

文件：`.github/workflows/small-talk.yml`

触发条件：
- `issues: [opened]`：有新 issue 时立即触发
- `schedule: cron '0 */6 * * *'`：每 6 小时轮询一次（兜底）
- `workflow_dispatch`：手动触发

所需 Secrets：
- `ANTHROPIC_API_KEY`：调用 Claude API
- `GITHUB_TOKEN`：内置，用于 `gh issue comment`（发布者为 GitHub Actions bot）

> **注意**：发布者身份将是 `github-actions[bot]` 而非 `ai-paul[bot]`。
> 若需保留 `ai-paul[bot]` 身份，需在仓库配置 GitHub App token 并设为 Secret `BOT_TOKEN`。

### 3. 新增单元测试

文件：`tests/test_main.py`

覆盖：
- `get_qualifying_issues()` 的过滤逻辑（无 issue、无评论-owner 开启、无评论-他人开启、最后评论是 owner、最后评论是 bot）
- `build_issue_context()` 的格式化输出

### 4. 更新 `pyproject.toml`

- 添加 `anthropic>=0.40` 生产依赖
- 添加 `pytest`、`pytest-mock` 开发依赖

## 接口兼容性

- `run.sh` 保持不变，本地执行入口不变
- issue 过滤逻辑（`get_qualifying_issues()`）逻辑不变
- 环境变量 `OWNER_LOGIN` 仍可覆盖默认值
