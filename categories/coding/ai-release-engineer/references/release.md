# Release

## Immutable Artifact

标准流程：

```text
Commit SHA
→ Build
→ Artifact
→ Test
→ UAT
→ Production
```

Artifact 至少应具备：

- 唯一版本
- 来源 Commit
- 可验证 digest/checksum
- 构建时间
- 构建流水线记录

## Build Once

禁止：

```text
Build A → QA
Build B → UAT
Build C → Production
```

必须：

```text
Build A → QA → UAT → Production
```

环境差异通过配置、Secrets 和基础设施处理，而不是重新编译应用。

## Production Rollout

优先：

```text
Deploy
→ Health Check
→ Canary / Small Percentage
→ Observe
→ Expand
```

如果项目规模较小、不支持 Canary，可以采用：

```text
Deploy
→ Health Check
→ Observe
→ Full Release
```

不要为了形式上的 Canary 引入不必要的基础设施复杂度。

## Release Checklist

- [ ] Artifact identity verified
- [ ] Required quality gates passed
- [ ] Critical journeys passed
- [ ] Database compatibility checked
- [ ] Rollback procedure verified
- [ ] Monitoring signals available
- [ ] Release approved
