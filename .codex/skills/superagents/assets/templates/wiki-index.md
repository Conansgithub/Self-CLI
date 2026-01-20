# superagents Wiki

本目录用于索引与解释性内容（不承载规范本体）。默认放在 `superagents/.sa/wiki/`（避免污染项目根目录）。

- 约定：`conventions.md`
- 工作流：`workflows.md`
- 状态枚举：`statuses.md`
- 评分门禁：`scoring.md`
- 风险门禁：`risk.md`
- Schema 版本：`schema-versions.md`
- 版本历史：`version-history.md`
- 项目接入：`integration.md`
- 故障排除：`troubleshooting.md`
- Specs 索引（自动生成）：`specs-index.generated.md`
- Tasks 索引（自动生成）：`tasks-index.generated.md`
- 机读索引（自动生成）：`catalog.generated.json`

生成/刷新索引：

```bash
python3 .codex/skills/superagents/scripts/sa_index.py
python3 .codex/skills/superagents/scripts/sa_compile.py
```
