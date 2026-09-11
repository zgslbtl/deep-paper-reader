# Deep Paper Reader · v0.2

把一篇 PDF 变成可以直接双击打开的三栏阅读器：**50% 原始 PDF / 35% 通俗讲解 / 15% 知识卡片**。无需 API Key、登录、数据库或常驻服务。

```text
reader/
├── index.html
├── paper.pdf
└── assets/
```

## 使用

将此目录作为 `deep-paper-reader` Skill 放入自己的 Codex skills 目录，或直接让 Codex 读取本目录的 `SKILL.md`。然后提供 PDF，说：“用 Deep Paper Reader 读懂这篇论文并生成本地 Reader。” Codex 完成理解、写作和背景查证；脚本不调用模型。

读者双击 `index.html`。三栏独立滚动；PDF 支持文本选择、按页导航及相对适合宽度的缩放。展开原文后点页码跳到左栏。知识卡片在居中浮层中阅读，点击关闭或按 Escape 返回原位置。图表保留原图和 caption，点击图像可打开原尺寸。

## 生成流程：提取 → Codex 写内容 → 构建

```sh
python -m pip install -r requirements.txt
python scripts/extract_pdf.py /absolute/paper.pdf --out /absolute/work
# Codex 阅读全文与预览，在 work 写 content.json 和图表裁剪。
python scripts/build_reader.py /absolute/work/paper.pdf /absolute/work/content.json --out /absolute/reader
```

提取只产生原始 PDF、带页码全文、图注候选和核查预览；预览不用于左栏显示。内容 JSON 服务页面，不是分析数据库。写法见 [论文和图表指引](references/paper-and-figures.md) 与 [外部知识指引](references/external-knowledge.md)。构建只检查必要字段、文件、页码和来源链接格式；引文匹配疑点提示人工核查。链接格式检查不声称来源内容正确。

最小构建示例（合成测试材料，不是研究结论）：

```sh
python scripts/build_reader.py examples/demo/paper.pdf examples/demo/content.json --out output/demo-reader
```

## 内容组织

连续文章依次讲背景、缺口、目的、问题、研究设置、原始数据、分析步骤、发现、贡献、局限和图表。中文负责解释，英文简短概括。重要位置可展开原文证据；未知信息直接说明。

图表先解释为什么画、数据怎样来，再讲实际坐标/元素、读法、模式、对应统计和结论边界。知识卡片单独查证背景，并将“本文实际怎么用”标为 PAPER。只使用 PAPER、EXTERNAL、NOT REPORTED 三种标识。

## 浏览器与离线限制

已随库打包 PDF.js、worker、字体/CMap/WASM，不使用 CDN、在线字体或本地 JSON/PDF fetch。PDF 字节由本地脚本传入 PDF.js，缩放按屏幕像素密度重新渲染。页面本身不主动联网；来源链接由读者主动打开。

使用近期桌面 Chrome 或 Safari。若本地脚本/Worker 受到浏览器策略限制，双击 `assets/打开阅读器.command`，会用 Python 3 在 **127.0.0.1 的空闲端口**启动备用服务并打开浏览器；关闭终端或 Ctrl-C 即可停止。阅读者正常打开不需要 Python，备用启动才需要。备用服务不能解决禁用 JavaScript、受密码保护的 PDF 或缺少 Python 的问题。macOS 若阻止执行下载来的 `.command`，可从终端运行 `python3 assets/open_reader.py`，无需修改浏览器安全设置。

PDF 字节以 base64 同时保留于脚本，体积约增大三分之一且另有原 PDF 副本；大型 PDF 会有启动内存开销。可选择文本依赖 PDF 自身文字编码，扫描件没有自动 OCR。三栏面向桌面阅读，窄屏体验有限。公式为离线 Unicode 文本，无在线数学渲染依赖。屏幕缩放不能恢复原 PDF 已经模糊的位图细节。

## 开发与检查

Python 运行依赖仅 PyMuPDF。开发测试可额外安装 pytest。Node.js 仅用于重新打包依赖和浏览器测试；生成结果不需要 Node。

```sh
npm ci
npm run vendor
python -m pytest tests/test_reader.py
# 浏览器测试使用真实论文生成结果，路径可传入：
node tests/reader_browser.cjs output/bridging-reader-simple/index.html
```

依赖版本锁定于 package-lock.json；第三方许可证随 `ui/vendor/` 和生成包提供。浏览器实现参考 [PDF.js 官方示例](https://mozilla.github.io/pdf.js/examples/)。实际验收范围见 [tests/ACCEPTANCE.md](tests/ACCEPTANCE.md)。

v0.2 删除旧六 tab、研究逻辑图、复现面板、ID/bbox 跳转校验、问答占位、知识模式开关、多份 JSON 导出、四份 schema 和模板填充系统。旧版保留在 Git 历史；现有论文与分析 output 不会迁移或删除。没有兼容旧 schema 的中间层。
