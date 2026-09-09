# Deep Paper Reader v0.1

A provenance-aware research paper reader that reconstructs how a study moves from research questions through data and methods to findings and contributions, while separating paper evidence from external knowledge.

单篇论文、双语分析、本地运行。**Codex 阅读与推理；Python 提取与校验。无需 OpenAI API Key。**

## 快速运行合成 demo

在本项目目录 `deep-paper-reader` 中运行（Python 3.9+）：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/validate_evidence.py examples/demo --strict
python scripts/build_reader.py examples/demo --out output/demo-reader
python scripts/serve_reader.py output/demo-reader --port 8765
```

打开 <http://127.0.0.1:8765>。Ctrl-C 停止服务。端口占用时选择其他端口。

仓库随附 `examples/demo/` 的三页 PDF、完整 analysis/index、空的独立知识扩展 JSON 和验证报告。所有研究内容与数值均为 **synthetic software fixture**，不是真实研究结论。需要重新生成时：

```bash
python scripts/create_demo.py --out examples/demo
```

该命令只生成固定的合成测试材料，不分析用户论文。

## 分析一篇真实论文

让 Codex 使用本目录的 [SKILL.md](SKILL.md)，例如：

> 使用这里的 Deep Paper Reader Skill，分析 /absolute/path/paper.pdf。先只读论文，重建数据和分析证据链，通过校验后生成本地 Reader。未报告的方法理由不要补充。

如需安装为可发现的个人 Skill，将整个 `deep-paper-reader` 文件夹复制到 `~/.codex/skills/deep-paper-reader`，保留 scripts、schemas、prompts、ui 等子目录。后续可调用 `$deep-paper-reader`。

实际处理步骤：

```bash
python scripts/ingest_pdf.py /absolute/path/paper.pdf --out output/my-paper
python scripts/build_document_index.py output/my-paper/paper.pdf --out output/my-paper
python scripts/create_analysis_template.py output/my-paper
```

此时由 **Codex** 读取全文、页面预览和七个分阶段 prompts，按 schema 填写 `output/my-paper/paper_analysis.json`。`paper_analysis.draft.json` 仅是空白结构；不能直接将默认未报告状态当作分析结果。不存在 Python 自动生成研究发现的伪分析逻辑。

```bash
python scripts/validate_evidence.py output/my-paper --strict
python scripts/build_reader.py output/my-paper --out output/my-reader
python scripts/serve_reader.py output/my-reader --port 8765
```

构建器每次重新校验当前 JSON 和 PDF SHA-256，不信任旧 PASS 报告。ERROR 阻止构建；WARN 默认也阻止，只有逐项人工核对后才能使用 `--allow-warnings`。输出目录必须新建，或是本工具已标记的构建目录，避免覆盖其他文件。

## Architecture

```text
SKILL.md + prompts/                 Codex 分阶段阅读与填写 JSON
schemas/                           严格 JSON Schema / 统一 Evidence Block
config/default.json                v0.1 默认策略与渲染分辨率
scripts/ingest_pdf.py               PDF 身份与本地副本
scripts/build_document_index.py     文本、bbox、候选章节/图表/参考文献、页面 PNG
scripts/create_analysis_template.py 明确标为 draft 的结构脚手架
scripts/validate_evidence.py         状态、引文、页码、bbox、类型化引用校验
scripts/build_reader.py             校验后生成静态 Reader + Markdown 导出
scripts/serve_reader.py             127.0.0.1 HTTP server
ui/                                原生 HTML / CSS / JS，无构建框架或 CDN
examples/demo/                     可运行合成论文与完整数据
tests/                             Python 回归测试 + 浏览器 smoke 脚本
```

数据流：PDF → Ingest → Document Index → **Codex Paper-only Analysis** → Evidence Validation → Reader Data → Build / Serve。Phase 6 External Knowledge / Phase 7 Field Context 是预留扩展接口。

`paper_analysis.json` 分离 `results`、`findings`、`interpretations`、`contributions`；结构引用使用 ID，其余论文内容使用 Evidence Block。`data_items.kind` 区分 `collected` 与 `derived`；派生项通过 `derived_from` 指向来源。`analysis_steps` 以 `input_data`、`output_data`、`depends_on` 和 `related_results` 串联处理链。Schema 均禁止未声明的字段。

## Provenance contract

| 状态 | 使用方式 |
| --- | --- |
| `explicit` | 论文明确报告，至少一个精确原文引用 |
| `supported_synthesis` | 明示综合，至少两个不同 block 的证据 |
| `not_reported` | 固定双语缺失文本，空 evidence |
| `external_knowledge` | 仅独立 knowledge/context 文件，必须显式区分来源 |

论文说用了 Mann–Whitney U 并不代表解释了为什么选它。方法可为 explicit，`paper_rationale` 仍为 not_reported。旨在研究某事不等于正式提出了 RQ。

Evidence 的 page 是 **从 1 开始的 PDF 物理页码**，不是印刷页脚编号；bbox 是 `[x0,y0,x1,y1]`，来自未旋转页面的左上角坐标，单位 point。渲染图使用相同坐标系。section 必须是索引中当前候选章节名，不明时为空字符串。

## Reader 功能

- 桌面三栏约 52% / 32% / 16%；六个分析 tabs。
- 中英双语、三态标签、可展开的原文、hover quote、点击证据页码跳转并高亮 bbox。
- PDF 页面滚动、前后页、页码输入、缩放、原始 PDF 打开/下载。
- Study timeline、原始/派生数据表、Method–Data Matrix、可展开 analysis pipeline。
- Figure/Table atlas、全页回退说明、图形编码与来源、研究逻辑节点/边、复现 checklist 和未解问题。
- 本地 JSON 关键词搜索，JSON/Markdown/PDF 导出。
- 独立 knowledge_cards.json / field_context.json 加载；Article Only 隐藏外部正文，Background 显示已生成内容或明确空状态。
- Ask the Evidence 只提供问题准备 shell，明确没有实时问答模型。

## 测试

```bash
python -m pytest tests -q
```

涵盖 schema、页码/状态/ID 错误、缺失/近似引文、伪 bbox/section、缺失图表、派生数据、PDF 提取、旋转坐标、空白扫描页警告、构建门禁和导出。

浏览器 smoke 需要 Node.js/npm 与 Chromium。另开终端启动端口 8765 的 demo server，再在本目录执行：

```bash
mkdir -p output/playwright
npx --yes --package @playwright/cli playwright-cli open http://127.0.0.1:8765
npx --yes --package @playwright/cli playwright-cli resize 1600 1000
npx --yes --package @playwright/cli playwright-cli run-code "$(cat tests/ui_smoke.js)"
```

脚本检查六 tabs、第三页证据跳转、bbox 缩放一致性、PDF 页面加载、图表切换、知识模式、搜索、导出、console error 和非本地网络请求，并保存 `output/playwright/reader-evidence.png`。首次运行浏览器 CLI 可能需要下载其运行环境；Reader 自身不使用网络依赖。

## Known limitations

- v0.1 的 PDF 阅读区域采用 PyMuPDF 生成的页面图像，没有引入 PDF.js。支持可靠定位和 bbox 高亮，但没有页面文本选择、PDF 内搜索和矢量级无限缩放；原 PDF 可单独打开。
- 章节、caption、参考文献提取是启发式。复杂多栏、扫描、跨页表和特殊 caption 可能遗漏。Codex 必须逐页复查。未实现自动 OCR；不可提取文字时会明确警告。
- 提取 embedded images 只作为候选资源。未可靠识别完整图边界时，Atlas 使用全页预览并显示 fallback，不把片段冒充完整图。
- Validator 验证结构与引用锚点，**不能证明引文蕴涵总结，也不能证明穷尽全文**。Codex 仍必须做语义审查；PASS 不等于科学结论正确。
- `config/default.json` 中深度/分析功能项是 Skill 的工作流默认值；脚本只直接读取 `render_dpi`。v0.1 UI 固定双语，不实现任意配置组合。
- 没有外部联网研究、实时 LLM 聊天、多论文数据库、云部署、用户系统、NOESIS、RAG 或 citation manager 集成。

## Recommended v0.2

1. OCR 与多栏/跨页提取审计，优先提高证据覆盖率。
2. 本地 PDF.js 文本层与选中文本建立 evidence，保留现有 bbox 接口。
3. 逐条 claim 语义审查记录与修改追踪，区分机器锚点校验和人工认可。
4. 经用户开启的有来源 Knowledge Cards，及基于现有证据的问答接口。

本次实际验收结果见 [tests/ACCEPTANCE.md](tests/ACCEPTANCE.md)：38 项 Python 测试通过，六页签及证据跳转/高亮等浏览器 smoke 通过。
