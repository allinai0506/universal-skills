# 根因猎手 - 诊断命令速查（按域分类）

## 使用方法

根据 Bug 现象特征，先定位到对应域，再调用对应命令集。每个命令都给出了预期输出格式。

---

## 域 A：Java / Spring Boot（JPA/Hibernate 链路）

### A1. 日志追踪
```bash
# 查看最近日志（按时间倒序）
tail -200 logs/application.log | grep -A5 "NullPointer\|ConcurrentModification"

# 搜索特定异常的完整链路
grep -A 20 "NestedServletException\|Transaction rolled back" logs/application.log

# 按请求 ID 追踪完整链路
grep "requestId=abc123" logs/application.log

# 查看特定时间的日志
grep "2026-06-07 08:3[0-5]" logs/application.log
```

### A2. JPA / Hibernate 诊断
```bash
# 开启 SQL 日志（临时，在 application-test.yml 中覆盖）
# spring.jpa.show-sql: true
# spring.jpa.properties.hibernate.format_sql: true

# 验证 SQL 参数是否正确
# 预期：参数列表中 ?1=?'BANK_RECEIPT' 匹配数据库中的实际值
# 实际偏差：参数是 'BANK_SLIP' → 查不到数据

# 检查 Entity 的 @Version 字段（乐观锁）
grep -rn "@Version" src/main/java/com/xiyu/bid/entity/
# 如果有 @Version，插入时 Hibernate 会自动 SET version = version + 1

# 检查事务传播
grep -rn "@Transactional\|@Transactional(readOnly=true)" src/
# readOnly=true 禁止写操作，尝试写入会抛 ReadOnlyException
```

### A3. Flyway 迁移诊断
```bash
# 查看已应用的迁移版本
ls -t src/main/resources/db/migration-mysql/V*.sql | head -5

# 验证迁移中是否有某列
grep -l "ADD COLUMN.*version" src/main/resources/db/migration-mysql/V*.sql

# 检查 H2 保留关键字（CI 测试会失败）
grep -E "value|key|user|rank|groups" src/main/resources/db/migration-mysql/*.sql
```

### A4. JVM 状态
```bash
# 线程 dump（定位死锁/死循环）
jstack <pid> > thread_dump_$(date +%s).txt
# 死锁特征：Found one Java-level deadlock
# 死循环特征：WAITING on owned by ... Runn

# 堆 dump（定位 OOM）
jmap -dump:format=b,file=heap_$(date +%s).hprof <pid>
# 用 MAT 分析：支配树 → 找最大对象路径

# GC 日志分析（定位频繁 Full GC）
grep "Full GC\|Allocation Failure" gc.log | awk '{print $1,$2,$NF}' | tail -20
```

### A5. Spring Security
```bash
# 检查 SecurityConfig 放行路径（不要在生产中扩大）
grep -n "permitAll\|/actuator\|/h2-console" src/main/java/com/xiyu/bid/config/SecurityConfig.java

# 检查 JWT 过滤器链
grep -rn "JwtAuthenticationFilter\|SecurityFilterChain" src/
```

---

## 域 B：React / TypeScript（前端状态链路）

### B1. 组件状态调试
```javascript
// 在关键位置添加调试日志
console.log('[DEBUG ComponentName]', {
  propName: props.propName,
  stateValue: this.state.value,
  timestamp: Date.now()
});

// React DevTools 使用建议
// 1. 安装 React DevTools 扩展
// 2. 选中组件 → Components → 查看 props/state
// 3. 重点关注：useEffect 依赖数组是否正确
```

### B2. API 请求追踪
```javascript
// 在 axios interceptor 中添加完整链路日志
axios.interceptors.request.use(config => {
  console.group(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
  console.log('params:', config.params);
  console.log('data:', config.data);
  console.log('headers:', config.headers);
  console.groupEnd();
  return config;
});

axios.interceptors.response.use(
  response => {
    console.group(`[API Response] ${response.status} ${response.config.url}`);
    console.log('data:', JSON.stringify(response.data)?.slice(0, 200));
    console.groupEnd();
    return response;
  },
  error => {
    console.group(`[API Error] ${error.config?.url}`);
    console.log('status:', error.response?.status);
    console.log('data:', error.response?.data);
    console.groupEnd();
    return Promise.reject(error);
  }
);
```

### B3. 状态管理（Redux/Zustand）
```javascript
// Redux DevTools 使用
// 1. 安装 Redux DevTools 扩展
// 2. 打开 DevTools → State
// 3. 找到对应 reducer，检查 mutation 前后状态差异

// Zustand 调试
import { useStore } from './store';
// 在 DevTools 中可直接查看和 time-travel 调试
```

### B4. 路由与生命周期
```javascript
// 检查 useEffect 依赖（最常见的状态丢失原因）
useEffect(() => {
  // BUG: 缺少 deps 导致不更新
  fetchData();
}, []); // ← 如果 fetchData 依赖 props.id，应该加在 deps 里

// 正确写法
useEffect(() => {
  fetchData(props.id);
}, [props.id]);
```

---

## 域 C：微信小程序（WeChat Mini Program）

### C1. 网络请求
```javascript
// 在 wx.request 拦截器中添加调试
const requestInterceptor = (options) => {
  console.log('[WX Request]', options.url, options.data);
  return options;
};

// 检查 HTTPS（生产必须）
// wx.request({ url: 'https://...' }) ✓
// wx.request({ url: 'http://...' }) ✗ 开发调试临时放开

// 检查 storage key 前缀（防止多项目冲突）
console.log('storage keys:', wx.getStorageInfoSync().keys);
```

### C2. 生命周期调试
```javascript
// 在关键生命周期中添加日志
Page({
  onLoad(options) {
    console.log('[Page onLoad]', options);
    // BUG 预警：onLoad 中做同步 setStorage 可能导致渲染延迟
  },
  onShow() {
    console.log('[Page onShow]', Date.now());
    // 每次展示都触发，如果做了非必要的 DB 查询会很慢
  },
  onReady() {
    console.log('[Page onReady]');
  }
});
```

### C3. 小程序特定问题
```javascript
// 检查分包加载（主包过大的典型症状）
// app.json 中 subPackages 配置

// 检查 permission（用户未授权的典型症状）
wx.getSetting({
  success(res) {
    console.log('[Auth]', res.authSetting);
    // { 'scope.userLocation': false } ← 未授权地理位置
  }
});
```

---

## 域 D：数据库（MySQL 8.0）

### D1. 连接与会话
```sql
-- 查看当前连接和锁等待
SELECT
  trx_id,
  trx_state,
  trx_started,
  TIMESTAMPDIFF(SECOND, trx_started, NOW()) AS running_seconds,
  trx_query,
  r.trx_isolation_level
FROM information_schema.INNODB_TRX t
JOIN information_schema.INNODB_TRANSACTIONS trx ON t.trx_id = trx.trx_id
JOIN information_schema.INNODB_LOCK_WAITS lw ON t.trx_id = lw.requesting_trx_id
JOIN information_schema.INNODB_LOCKS l ON lw.blocking_lock_id = l.lock_id
JOIN information_schema.INNODB_TRX r ON l.lock_trx_id = r.trx_id
ORDER BY running_seconds DESC;

-- 查看锁等待树
SELECT * FROM sys.innodb_lock_waits;
```

### D2. 慢查询与索引
```sql
-- 最近的慢查询
SELECT
  start_time,
  query_time,
  rows_sent,
  rows_examined,
  LEFT(digest_text, 200) AS query
FROM performance_schema.events_statements_history
WHERE digest_text IS NOT NULL
  AND start_time > DATE_SUB(NOW(), INTERVAL 1 HOUR)
  AND query_time > 1
ORDER BY query_time DESC
LIMIT 20;

-- 检查缺失索引（某列在 WHERE 中但无索引）
-- 对应查询：EXPLAIN SELECT * FROM table WHERE col = 'xxx';
EXPLAIN ANALYZE
  SELECT * FROM tender_document
  WHERE document_type = 'BANK_RECEIPT';

-- 检查外键引用完整性（删除父记录前先检查子记录）
SELECT c.TABLE_NAME, c.COLUMN_NAME, c.CONSTRAINT_NAME
FROM information_schema.KEY_COLUMN_USAGE c
JOIN information_schema.TABLE_CONSTRAINTS t
  ON c.CONSTRAINT_NAME = t.CONSTRAINT_NAME
WHERE c.REFERENCED_TABLE_NAME = 'parent_table'
  AND t.CONSTRAINT_TYPE = 'FOREIGN KEY';
```

### D3. 数据一致性
```sql
-- 检查子表中有孤立记录（父表无对应行）
SELECT c.TABLE_NAME, COUNT(*) AS orphaned_count
FROM information_schema.COLUMNS c
JOIN information_schema.KEY_COLUMN_USAGE k
  ON c.TABLE_SCHEMA = k.TABLE_SCHEMA
  AND c.TABLE_NAME = k.TABLE_NAME
  AND c.COLUMN_NAME = k.COLUMN_NAME
JOIN information_schema.TABLE_CONSTRAINTS tc
  ON k.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
WHERE tc.CONSTRAINT_TYPE = 'FOREIGN KEY'
  AND k.REFERENCED_TABLE_SCHEMA = DATABASE()
GROUP BY c.TABLE_NAME;

-- 检查字符集一致性（utf8 vs utf8mb4 导致的 emoji 存储问题）
SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND CHARACTER_SET_NAME = 'utf8'  -- 应该是 utf8mb4
  AND DATA_TYPE IN ('varchar', 'char', 'text');
```

### D4. Flyway 版本
```sql
-- 查看当前 Flyway schema history
SELECT * FROM flyway_schema_history
WHERE success = 1
ORDER BY installed_rank DESC
LIMIT 10;

-- 验证某迁移是否已执行
SELECT COUNT(*) AS applied
FROM flyway_schema_history
WHERE version = 'V1__init.sql'
  AND success = 1;
```

---

## 域 E：缓存与消息队列（Redis）

### E1. Redis 键值
```bash
# 检查 key 是否存在及 TTL
redis-cli GET <key>
redis-cli TTL <key>
redis-cli TYPE <key>

# 查找匹配的 key（谨慎使用 KEYS 命令，生产环境用 SCAN）
redis-cli SCAN 0 MATCH "*tender*" COUNT 100

# 检查缓存穿透（null 值缓存）
redis-cli GET "cache:tender:123"
# 预期：有值 或 不存在
# 偏差：空字符串 "" → 可能表示"缓存了 null"，需要区分

# 检查缓存雪崩（大量 key 同时过期）
redis-cli --scan --pattern "*user*" | xargs -I{} redis-cli TTL "{}" \
  | awk '{if($1 < 3600) count++} END {print "Keys expiring within 1h:", count}'
```

### E2. 消息队列积压
```bash
# 查看队列深度
redis-cli LLEN queue:tender:process

# 查看消费者状态
redis-cli XINFO GROUPS stream:tender:events

# 检查死信队列
redis-cli LRANGE queue:dlq 0 -1
```

---

## 域 F：跨域 / 集成（Webhook + 第三方回调）

### F1. Webhook 链路追踪
```bash
# 检查 Webhook 日志（西域投标平台）
# 路径: backend/logs/webhook-delivery.log
tail -50 logs/webhook-delivery.log | grep "delivery_id\|tender_id"

# 检查幂等键冲突
grep "idempotency_key\|duplicate" logs/webhook-delivery.log

# 验证签名
# 1. 获取 WebhookConfig 中的 secret
grep -n "webhook.*secret" src/main/resources/application*.yml
# 2. 用 HMAC-SHA256 验证签名
echo -n "payload" | openssl dgst -sha256 -hmac "secret_key"
```

### F2. HTTP 抓包
```bash
# 抓取特定端口的 TCP 包
sudo tcpdump -i any -nn 'tcp port 8080' -w capture_$(date +%s).pcap &

# 检查 DNS 解析
nslookup api.example.com
dig api.example.com

# 检查 SSL 证书
openssl s_client -connect api.example.com:443 -servername api.example.com \
  </dev/null 2>/dev/null | openssl x509 -noout -dates
```

---

## 域 G：架构与 CI（分层 / 循环依赖）

### G1. ArchUnit 架构规则
```bash
# 运行完整架构测试
cd backend && mvn test -Dtest=ArchitectureTest -q

# 运行特定规则
mvn test -Dtest=ArchitectureTest#strict_module_controller_should_not_depend_on_repository -q

# 检查 Entity 放置位置违规
mvn test -Dtest=ArchitectureTest#jpa_entities_forbidden_in_non_persistence_packages -q

# 检查循环依赖
mvn test -Dtest=ArchitectureTest#no_circular_dependencies -q
```

### G2. Git Bisect
```bash
# 自动定位引入 Bug 的提交
git bisect start
git bisect bad HEAD                    # 当前版本有 Bug
git bisect good <good-commit-hash>     # 某个历史版本正常
# Git 自动 checkout 中间版本，测试后：
#   git bisect good   # 当前版本正常，继续找更早的
#   git bisect bad    # 当前版本有 Bug，继续找更晚的
# 重复直到找到第一个 bad 提交
git bisect reset                      # 完成后重置

# 查找引入特定字符串的提交
git log -p --all -S 'problematic_string' -- '*.java' | head -50
```

---

## 命令输出格式约定

每个命令的输出必须包含：
1. **命令本身**（便于复现）
2. **预期输出**（正常情况是什么样）
3. **偏差标识**（找到 Bug 时的输出特征）

```
$ redis-cli GET cache:tender:123
(nil)                    ← 预期：有值；实际：nil → Cache Miss，触发穿透

$ grep "BANK_RECEIPT" logs/application.log
2026-06-07 08:30:12 normalizeType input=BANK_RECEIPT output=BANK_SLIP
                         ← 偏差！output 不应该是 BANK_SLIP
```
