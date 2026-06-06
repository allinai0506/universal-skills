# Gotchas — 常见踩坑记录

> **Gotchas 是本 skill 中最高价值的文档。**
> 这些条目来自实际使用中 Claude 常犯的错误，每次踩坑后应追加到本文档。

---

## Phase 2 差距分析 Gotchas

### G1: 只 grep 字段名，不验证类型

**症状**：gap-analysis 写"已实现"，实际类型不匹配。

```bash
# ❌ 错误：只检查字段名存在
grep -rn "budget" backend/src/main/java/com/xiyu/bid/tender/dto/

# ✅ 正确：检查完整声明（字段名 + 类型）
grep -rn "private.*budget" backend/src/main/java/com/xiyu/bid/tender/dto/ --include="*.java"
```

**经验**：grep 匹配到 `String budget` 和 `BigDecimal budget` 两种情况很常见。

---

### G2: 前端有组件，后端是 placeholder

**症状**：前端表单能填，后端不落地。

```bash
# 前端
grep -rn "handleSubmit\|onSubmit" src/views/Bidding/TenderForm.vue

# 后端（⚠️ 验证是否有真实持久化）
grep -rn "handleSubmit\|save\|persist" backend/src/main/java/com/xiyu/bid/tender/service/
```

**经验**：常出现在早期 scaffold 阶段——前端先写，后端接口是 `log.info("submit")`。

---

### G3: 状态枚举值不完整

**症状**：gap-analysis 说"已实现"，实际枚举值数量不足。

```bash
# 检查枚举实际值（必须逐个核对）
grep -rn "enum.*Status" backend/src/main/java/com/xiyu/bid/tender/ --include="*.java" -A 20
# 然后对照蓝图要求的枚举值列表
```

**经验**：枚举值数量是"多于等于蓝图"还是"少于蓝图"要分开判断。

---

### G4: 权限写在代码里，没有配菜单权限

**症状**：前端 `v-permission` 正确，但运行时按钮还是出现/消失了。

```bash
# 前端有 v-permission ✅
grep -rn "v-permission" src/views/Bidding/TenderList.vue

# 但数据库菜单权限表中没有 INSERT → ❌ 权限未生效
grep -rn "INSERT.*menu_permission\|menu_permission.*INSERT" \
  backend/src/main/resources/db/migration-mysql/V*.sql \
  | grep -i "tender\|create\|edit"
```

**经验**：前端权限指令和后端菜单权限配置必须同时存在。Spring Security `@PreAuthorize` 和前端 `v-permission` 是两道防线。

---

### G5: 使用旧的 gap-analysis 结论

**症状**：gap-analysis.md 中写"缺某字段"，但 grep 发现字段其实存在。

**根因**：gap-analysis.md 是基于之前某个时间点的代码状态写的，代码已更新但分析没有重新做。

**经验**：
- 每次开始 Phase 2 前，必须**重新验证**所有"已实现"项
- 不要直接引用旧的 gap-analysis 结论，必须重新运行 grep/Read 命令
- 验证时间要写进 gap-analysis.md

---

### G6: 只看 commit message，不读实际代码

**症状**：gap-analysis 引用了 commit message 说"实现了 X"，实际代码中没有 X。

**经验**：
- commit message 是给人类看的，不保证与代码一致
- Phase 2 禁止引用 commit message 作为"已实现"的证据
- 必须有 `grep/Read 代码 + 实际输出` 才算验证通过

---

### G7: 权限变更没配 Flyway 迁移

**症状**：改了 `RoleProfileCatalog.java`，但已有角色的菜单权限不生效。

**经验**：
- 改了 `menuPermissions` 必须写 Flyway INSERT/UPDATE 迁移
- 用 `Vxxx__update_role_permissions.sql` 命名
- 迁移要对已有测试数据生效

---

## Phase 4 验证 Gotchas

### G8: Token 获取成功，但权限是错的

**症状**：`/tmp/blueprint-tokens.json` 有 token，但用户登录后权限不符合预期。

**经验**：
- 测试用户必须存在于数据库（seed data）
- 确认 token 是本项目用户，而非其他系统用户
- 验证 token 时加 `--verbose` 看响应体

---

### G9: 后端启动成功，但 API 返回 401

**症状**：后端 `actuator/health` 通过，但业务 API 返回 401。

**经验**：
- actuator 是公开接口，不校验 JWT
- 业务 API 走 Spring Security 过滤器链
- 用 `curl -H "Authorization: Bearer $TOKEN"` 而非 cookie

---

### G10: 前端端口和后端端口不一致

**症状**：前端请求发到错误的后端端口，CORS 报错。

**经验**：
- 每次启动服务前，`source scripts/dev-env.sh` 检测当前分配端口
- Vite 的 `VITE_API_BASE_URL` 必须与后端实际端口一致
- 常见陷阱：改了后端端口但前端没改

---

### G11: Playwright 页面加载后 token 失效

**症状**：登录后页面空白，或跳转到登录页。

**经验**：
- localStorage 中的 token 可能在 `page.goto` 后被 Vue Router 清除
- `loginWithToken` 函数中，set token → reload → wait 才可靠
- token 有过期时间（JWT exp），过期后需重新获取

---

## Phase 3 实现 Gotchas

### G12: `mvn compile` 通过，但运行时报错

**症状**：编译通过，Spring 启动时 Bean 注入失败。

**经验**：
- `mvn compile` 只做编译检查，不做 Spring 上下文初始化
- 每次修改 Java 代码后，**必须重启后端**（不能热部署）
- 完整验证：`mvn spring-boot:run` 启动成功 + actuator health 通过

---

### G13: Flyway checksum 冲突

**症状**：后端启动时 Flyway 报错 `Validate failed`。

**经验**：
- 改了已提交的迁移文件（哪怕是注释）会导致 checksum 变
- 如果是本地调试：删除 `backend/target` 后重试
- 如果是生产：必须创建新迁移文件，不能改历史迁移

---

### G14: 前端 import 路径错误导致运行时 500

**症状**：`npm run build` 通过，但页面加载时 API 返回 500。

**经验**：
- Vite 编译时不会校验 API URL 正确性
- API URL 错误（路径写错）要到运行时才暴露
- 验证：在浏览器 Network 面板看实际请求 URL

---

## 通用 Gotchas

### G15: 检查点文件在不同 worktree 路径

**症状**：上次进度丢失，检查点 phase=1。

**经验**：
- 检查点文件在 `<worktree-root>/.blueprint-checkpoint.json`
- 不同 worktree 有不同的检查点文件
- 如果发现检查点丢失，先确认当前 worktree 是否正确

---

### G16: 蓝图表述模糊导致理解分歧

**症状**：Phase 2 验证时发现蓝图描述和实际理解不一致。

**经验**：
- 遇到模糊描述，先用 `lark-doc` 读蓝图标注文和评论
- 如果蓝图书面说不清，记录"存疑，待产品确认"并写入 gap-analysis
- 不要假设，按最保守的方式实现

---

## 更新记录

每次踩坑后追加：

```
### G{N}: [简述]
**发现时间**: YYYY-MM-DD
**触发场景**: [什么操作触发了这个坑]
**症状**: [什么现象]
**经验**: [如何避免]
```
