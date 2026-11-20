# ai-dev-skills

三个自用 AI 开发辅助技能（SKILL.md 规范，可导入支持该格式的 AI 编程助手复用）：

| 技能 | 功能 | 触发示例 |
|------|------|----------|
| git-commit-assistant | 基于真实 Git diff 生成 Conventional Commits 提交信息、changelog、PR 描述；执行提交须用户确认 | "帮我写提交信息" |
| prompt-workbench | 本地 Prompt 模板库：变量填充、编辑自动留版本、A/B 对比（附纯标准库管理脚本 scripts/store.py，已实测） | "存一下这个提示词" |
| doc-generator | 扫描代码项目生成/更新 README 与 API 文档，每条描述有代码依据 | "给项目生成 README" |

## 目录结构

```
git-commit-assistant/SKILL.md
prompt-workbench/SKILL.md
prompt-workbench/scripts/store.py
doc-generator/SKILL.md
```

## 脚本快速上手（prompt-workbench）

```bash
python prompt-workbench/scripts/store.py add --name review --body '请审查{{lang}}代码：{{code}}'
python prompt-workbench/scripts/store.py render --name review --var lang=Python --var 'code=print(1)'
python prompt-workbench/scripts/store.py edit --name review --body '请严格审查{{lang}}代码：{{code}}'
python prompt-workbench/scripts/store.py diff --name review --a 1 --b 2
```

模板库默认存 `~/.prompt-workbench/store.json`，可用 `--store` 或环境变量 `PROMPT_STORE` 覆盖。要求 Python 3.8+，无第三方依赖。
