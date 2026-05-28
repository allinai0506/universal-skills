# 服务启动脚本

## 前后端联调启动

```bash
export XIYU_DEV_CONFIRMED=1
source scripts/dev-env.sh  # 自动设置 FRONTEND_PORT / BACKEND_PORT / DB_NAME

# 后端启动（后台）
DB_NAME=${DB_NAME:-xiyu_bid_claude} \
JWT_SECRET="xiyu-bid-poc-local-dev-secret-key-please-change-in-prod-32bytes-min" \
DB_PASSWORD="XiyuDB!2026" \
CORS_ALLOWED_ORIGINS="http://localhost:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}" \
mvn spring-boot:run -Dspring-boot.run.profiles=dev,mysql \
  -Dspring-boot.run.arguments="--server.port=${BACKEND_PORT}" \
  > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

# 前端启动（后台）
VITE_API_BASE_URL=http://127.0.0.1:${BACKEND_PORT} ./node_modules/.bin/vite \
  --port ${FRONTEND_PORT} --force > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!

# 等待启动
echo "等待后端启动..."
for i in $(seq 1 30); do
  if curl -s http://127.0.0.1:${BACKEND_PORT}/actuator/health > /dev/null 2>&1; then
    echo "后端就绪"
    break
  fi
  sleep 2
done
echo "前端地址：http://127.0.0.1:${FRONTEND_PORT}"
```

> **启动失败恢复**：如果后端 60 秒未就绪：
> 1. `cat /tmp/backend.log | tail -30` 查看错误
> 2. 常见原因：端口占用、DB 连接失败、checksum 冲突
> 3. 修复后重试
