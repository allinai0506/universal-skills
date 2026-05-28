# 角色权限矩阵（标讯中心）

> 用于验证阶段对照蓝图的权限矩阵。
> 只包含标讯中心相关权限。完整角色权限以数据库/代码为准。

## 角色一览

| 角色 | RoleProfile | 后端代码枚举 | 密码 |
|------|-------------|-------------|------|
| 投标管理员 | `bid_admin` | `RoleProfile.BID_ADMIN` | `Test@123` |
| 投标组长 | `bid_lead` | `RoleProfile.BID_LEAD` | `Test@123` |
| 项目负责人 | `sales` | `RoleProfile.SALES` | `Test@123` |
| 投标专员 | `bid_specialist` | `RoleProfile.BID_SPECIALIST` | `Test@123` |

## 标讯中心模块权限矩阵（参考蓝图）

| 功能 | bid_admin | bid_lead | sales | bid_specialist |
|------|:---------:|:--------:|:-----:|:--------------:|
| 查看标讯列表 | ✅ | ✅ | ✅ | ✅ |
| 创建标讯 | ✅ | ✅ | ✅ | — |
| 编辑标讯 | ✅ | ✅ | — | — |
| 删除标讯 | ✅ | — | — | — |
| 提交审核 | ✅ | ✅ | ✅ | — |
| 审核标讯 | — | — | — | ✅ |
| 查看详情 | ✅ | ✅ | ✅ | ✅ |
| 导出标讯 | ✅ | ✅ | ✅ | ✅ |
| 批量导入 | ✅ | — | — | — |

> ⚠️ 此表为参考框架，具体权限以下列方式之一确认：
> 1. 后端 `RoleProfileCatalog.java` 中的 `menuPermissions` 定义
> 2. Flyway 迁移脚本中的权限 INSERT 语句
> 3. 蓝图的权限矩阵章节
>
> 验证时以角色矩阵和页面实际渲染为准，不要仅依赖本表。

## 权限验证清单要点

- ✅ 每个按钮的 `v-if` / `v-permission` 指令与角色匹配
- ✅ 后端 Controller 的 `@PreAuthorize` 或 AOP 切面拦截
- ✅ 无权限的 API 返回 403
- ✅ 前端不渲染无权限的操作按钮（不仅仅是 disabled）
