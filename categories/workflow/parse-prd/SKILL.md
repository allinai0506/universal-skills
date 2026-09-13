---
name: parse-prd
version: 1.0.1
description: "解析飞书 PRD 文档：提取正文、画板、截图、HTML 片段和注释，合并为结构化需求简报。当用户提供飞书 PRD 链接时自动触发。"
allowed-tools: Read, Write, Grep, Bash
---

# parse-prd

解析飞书产品需求文档（PRD），输出可供下游（speckit-specify、Claude Agent）直接消费的结构化需求简报。

## 执行流程

### 1. 提取正文

```bash
lark-cli docs +fetch --api-version v2 --doc <PRD_URL> --format json > /tmp/prd-blocks.json
```

飞书文档返回的是 XML/HTML 格式内容，检查其中的元素类型：
- `<h1>` ~ `<h6>` / `<p>` / `<li>` → 直接提取为正文
- `<img>` → 记录 `src` 属性值（image file_token），下一步下载
- whiteboard 元素（`whiteboard_token` 属性） → 记录 token，下一步导出
- `<table>` → 转为 Markdown 表格
- `<pre><code>` → 下一步用 markitdown 转换
- `<blockquote>` / 评论 → 提取为备注/约束

### 2. 解析多模态内容

对每种非文本类型分别处理：

#### 截图 / UI 示例（image block）

用 `docs +media-download` 下载图片（不要用 `drive +download`，文档内嵌图片不是 drive 文件，会 403）：

```bash
cd /tmp && lark-cli docs +media-download --token <image_src_token> --output prd-img-<token>.png --overwrite
```

下载后用 Read 工具读取下载的图片，用视觉能力分析截图内容：
- 提取界面布局结构（顶部/侧边栏/内容区/操作区）
- 描述交互流程（按钮点击 → 弹窗 → 表单 → 提交）
- 识别 UI 组件类型（表格、表单、卡片、弹窗、标签等）
- 记录视觉规范（颜色、间距、图标风格）

对于有多张图片的章节，先全部下载，再逐张分析。

#### 画板（whiteboard）

```bash
lark-cli whiteboard +query --whiteboard-token <token> --output_as code
```

输出是 DSL/Mermaid 文本，Claude 可以直接理解结构。

如果 `--output_as code` 输出为空或不可读，回退到图片模式：

```bash
cd /tmp && lark-cli whiteboard +query --whiteboard-token <token> --output_as image --output prd-wb-<token>.png --overwrite
```

然后用 Read 工具读取图片，将流程/架构转为文字描述。

#### HTML 代码片段（code block）

```bash
cat /tmp/code-<block_id>.html | markitdown
```

或直接读取代码内容，嵌入需求简报。

### 3. 提取注释 / 评审意见

```bash
lark-cli docs +fetch --api-version v2 --doc <PRD_URL> --scope section --keyword "评论|备注|TODO|FIXME" --context-before 1 --context-after 1 --format json
```

以及文档底部的评论区内容（从原 fetch 结果的评论部分提取）。将评论中的约束条件、待确认问题和评审意见归入需求简报的「约束与风险」章节。

### 4. 合并为结构化需求简报

将以上所有输出合并为一个 Markdown 文件 `docs/prd-简报-<章节名>-<日期>.md`，结构如下：

```markdown
# PRD 需求简报：<文档标题> - <章节>

## 基本信息
- **文档链接**: <原始 PRD 链接>
- **章节**: <章节名>
- **提取日期**: <日期>
- **文档版本**: <从正文提取>

## 业务目标与背景
<从正文提取>

## 功能需求
### <功能一>
- **行为描述**: <文字描述>
- **交互流程**: <画板/Mermaid 描述>
- **UI 参考**: <截图描述 + 视觉分析>
- **权限规则**: <如有>

### <功能二>
...

## 视觉与交互参考
<所有 UI 截图和画板的文字化描述汇总>

## 技术约束
<HTML 代码片段、接口定义、数据结构>

## 约束与风险
<来自评论的约束、待确认点、评审意见>
```
