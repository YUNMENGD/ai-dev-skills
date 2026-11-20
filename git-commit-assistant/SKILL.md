---
name: git-commit-assistant
description: 基于 Git 真实变更生成 Conventional Commits 提交信息、版本 changelog 与 PR 描述。当用户要求写/生成提交信息、commit message、changelog、发布说明或 PR 描述时触发。
---

# AI Git 提交助手

基于仓库真实 diff 生成规范的提交相关文本，绝不编造不存在的变更。

## 通用硬约束
- 只生成文本；执行 `git commit`、`git push`、创建 PR 必须用户另行明确同意，默认展示结果后即停。
- 提交信息默认中文描述（type/scope 保留英文关键字）；用户要求英文时用英文。
- 生成前先读 `git status --porcelain` 与对应 diff；diff 为空时告知用户无变更并停止。
- 发现暂存区含敏感文件（.env、凭据、密钥）时先警告用户，生成文本中不得包含其内容。
- diff 超过 60KB 时改用 `git diff --stat` 加关键文件 diff 摘录生成，并注明基于摘要。

## 工作流 A：提交信息
1. 在目标仓库运行 `git diff --cached --stat` 与 `git diff --cached`。暂存区为空时改用 `git diff` 并告知用户这是未暂存变更；只生成文本，不代为暂存。
2. 归纳变更本质（做了什么、为什么），选 type：feat/fix/docs/style/refactor/perf/test/build/ci/chore/revert。
3. 输出格式：
   - 首行 `<type>(<scope>): <祈使句摘要，≤50 字符>`，scope 取模块名、可省略；
   - 复杂变更空一行后加 2–5 条要点正文；
   - 有破坏性变更时加 `BREAKING CHANGE:` 段落。
4. 展示结果并询问是否执行提交；用户明确同意后才运行 `git commit`（多行信息用多个 `-m` 或临时文件），随后 `git log -1 --stat` 回读核验。

## 工作流 B：changelog
1. 确定区间：用户指定 tag/commit 区间；未指定时 `git describe --tags --abbrev=0` 取最近 tag 到 HEAD，无 tag 则默认最近 30 条并向用户说明。
2. `git log <区间> --pretty=format:"%h|%s"`，必要时加 `--stat`。
3. 按 type 归组：新功能 / 修复 / 性能 / 重构 / 文档 / 其他，每条 `- 摘要（短哈希）`；合并同义提交，剔除 merge 噪声。
4. 输出 Markdown（版本号与日期由用户提供或取自 tag）。用户要求写入 CHANGELOG.md 时默认在文件顶部原地插入，写前先读原文件。

## 工作流 C：PR 描述
1. 确认基分支（默认 main/master）与当前分支（`git branch --show-current`）。
2. `git log <base>..HEAD --oneline` 与 `git diff <base>...HEAD --stat`，按需读关键 diff。
3. 生成：标题（一句话）、变更动机、改动点清单、测试情况（只写用户确认过的，否则标"未验证"）、风险与回滚说明。
4. 只输出文本；推送与创建 PR 需用户另行明确授权。
