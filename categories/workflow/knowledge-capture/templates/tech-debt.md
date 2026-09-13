<!--
  追加到 docs/exec-plans/tech-debt-tracker.md 对应分类下。
  按 type 归类：遗留清理类 / 文档同步类 / 待登记。
  新登记的一律 status: open。
  不写 wiki frontmatter；tech-debt-tracker 是结构化台账。
-->

- area: <`模块/包/文件路径`>
  type: <god-class | dead-code | mock-leak | out-of-sync-doc | dependency-debt | test-gap>
  severity: <high | medium | low>
  status: open
  source: <发现来源，如 "session 2026-06-18 排查 XX 时发现" / "某次 review">
  note: <一句话说明问题与建议处理方式>
