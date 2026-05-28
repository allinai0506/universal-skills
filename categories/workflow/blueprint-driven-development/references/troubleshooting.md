# 蓝图实现故障排查

## 启动阶段

| 症状 | 原因 | 修复 |
|------|------|------|
| 后端启动 60 秒无响应 | 端口占用 | `pkill -f "server.port=${BACKEND_PORT}"` 后重试 |
| MySQL 连接失败 | DB 未运行 | `mysql -u root -pXiyuDB!2026 -e "SELECT 1"` 验证 |
| Flyway checksum 失败 | 迁移冲突 | `rm -rf backend/target` 清理缓存后重试 |
| Vite 文件修改不生效 | worktree HMR bug | `pkill -f vite && rm -rf node_modules/.vite` 后加 `--force` 重启 |

## 验证阶段

| 症状 | 原因 | 修复 |
|------|------|------|
| Token 获取失败 | 后端未就绪 | `cat /tmp/backend.log \| tail -20` 查看错误 |
| 页面加载后空白 | token 过期 | 重新获取 token 后重试 |
| 按钮显示与预期不符 | 权限代码未部署 | 确认 `mvn compile` 通过且重启后端 |
| CORS 报错 | `VITE_API_BASE_URL` 端口不对 | 确认 ${BACKEND_PORT} 与后端端口一致 |

## 实现阶段

| 症状 | 原因 | 修复 |
|------|------|------|
| `mvn compile` 失败 | 编译错误 | 读错误日志，修 Java 语法/类型错误 |
| `npm run build` 失败 | 构建错误 | 读 Vite 错误输出，修 import/类型错误 |
| 架构测试失败 | 循环依赖/包引用违规 | `mvn test -Dtest=ArchitectureTest` 读具体失败规则 |
| Spring 启动失败 | 配置/Bean 冲突 | `cat /tmp/backend.log \| grep ERROR` |
