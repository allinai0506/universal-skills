---
name: performance-tuning
description: Use when optimizing code for speed, memory, or throughput - high CPU usage, GC pressure, slow hot paths, lock contention, excessive object allocation, or when designing performance-critical Java/backend code. Covers estimation, measurement (JMH/profiling), GC optimization, API design, concurrency, and serialization.
---

# Code Performance Tuning

## Overview

Core principle: **算法领先、减少浪费（内存/计算）、精准测量。**

Performance is not an afterthought — it's a discipline of estimation, measurement, and targeted optimization. Don't waste time on micro-optimizations, but never miss the critical 3% that defines system quality.

## When to Activate

- Writing or reviewing performance-critical code (hot paths, high-throughput services)
- Diagnosing high CPU usage, GC pressure, slow latency, or memory bloat
- Designing APIs or data structures for high-concurrency scenarios
- Choosing between serialization formats or concurrency strategies
- Planning capacity or evaluating architectural trade-offs
- Profiling shows "flat profile" (no obvious hotspot — means losses are scattered)

**When NOT to use:** Premature optimization without measurement data; cosmetic micro-tuning of cold paths.

## Quick Reference

| Area | Key Technique | Core Rule |
|------|--------------|-----------|
| Mindset | Back-of-envelope calc | Estimate before coding |
| Measurement | JMH + profiler | Never guess — measure |
| Memory | Reduce allocation | Fewer objects = less GC |
| API/Logic | Batch + fast path | Amortize per-call overhead |
| Concurrency | Sharding + short critical sections | Minimize lock contention |
| Serialization | Primitive > Protobuf (in-memory) | Match format to use case |

---

## 1. Estimation & Mindset

### Back-of-Envelope Calculation

Before implementing, estimate resource costs with simple math to eliminate bad designs early.

```
磁盘寻道:     ~10ms      (HDD)
SSD 随机读:   ~100μs
内存访问:     ~100ns
网络往返(同机房): ~0.5ms
网络往返(跨域):   ~30-150ms
1Gbps 网络传输 1MB: ~8ms
```

**Example:** Reading 1000 small files from HDD vs one batched read:
- 1000 files × 10ms seek = 10s (unacceptable)
- 1 batched read = 10ms + transfer time

### The Critical 3%

Don't waste time on meaningless micro-optimizations. But never miss the 3% of code that determines system quality. Focus energy on:
- Hot paths executed millions of times
- Latency-critical request handlers
- Memory allocation in tight loops

### Prevent Flat Profiles

A "flat profile" means performance losses are scattered everywhere — no single hotspot to optimize. This happens when performance is completely ignored during initial development.

**Prevention:** Keep performance in mind during design. Even light awareness (choosing the right data structure, avoiding obvious waste) prevents scattered losses that are impossible to fix later.

---

## 2. Measurement & Analysis Tools

### Microbenchmarking with JMH

Never use `System.nanoTime()` loops for benchmarking — JIT compilation, dead code elimination, and JVM warmup produce misleading results.

```java
@BenchmarkMode(Mode.Throughput)
@OutputTimeUnit(TimeUnit.MILLISECONDS)
@State(Scope.Thread)
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 10, time = 1)
@Fork(2)
public class StringConcatBenchmark {

    @Benchmark
    public String concatBuilder() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 100; i++) {
            sb.append("item").append(i);
        }
        return sb.toString();
    }
}
```

**Key JMH rules:**
- Always use `@State` for shared state
- Return values to prevent dead code elimination
- Use `@Fork` to catch JVM-level optimizations
- Never benchmark inside a plain `main()` method

### Profiling

| Tool | Use Case |
|------|----------|
| Async-profiler | Low-overhead CPU + allocation profiling (production-safe) |
| JFR (Java Flight Recorder) | Built-in continuous monitoring |
| pprof | Go/C++ profiling |
| VisualVM | Quick local analysis |

**Workflow:** Profile → identify top CPU consumers → check allocation hotspots → optimize → re-measure.

### Stats Collection Cost

Recording statistics (counters, timers, histograms) has a cost. On hot paths:
- Use **sampling** instead of recording every event
- Lower stats frequency on non-critical paths
- Avoid expensive string formatting in metrics collection

```java
// ❌ BAD: Every call constructs a metric string
void process(Request req) {
    metrics.record("request." + req.getType() + ".duration", elapsed);
}

// ✅ GOOD: Sample or use pre-computed keys
private static final MetricKey REQUEST_DURATION = MetricKey.of("request.duration");
void process(Request req) {
    if (ThreadLocalRandom.current().nextInt(100) < SAMPLE_RATE) {
        metrics.record(REQUEST_DURATION, elapsed);
    }
}
```

---

## 3. Java Memory Management & GC Optimization

### Reduce Object Allocation

This is the core of Java optimization. Fewer allocations = less allocator time + less GC pressure.

```java
// ❌ BAD: Creates a new object per iteration
List<String> results = new ArrayList<>();
for (Item item : items) {
    String formatted = String.format("prefix-%s-suffix", item.getName());
    results.add(formatted);
}

// ✅ GOOD: Reuse, avoid String.format overhead
List<String> results = new ArrayList<>(items.size());  // pre-size!
StringBuilder sb = new StringBuilder(64);
for (Item item : items) {
    sb.setLength(0);  // reuse StringBuilder
    sb.append("prefix-").append(item.getName()).append("-suffix");
    results.add(sb.toString());
}
```

### Container Pre-sizing

When data size is known, preset capacity to avoid array resizing and copying.

```java
// ❌ BAD: Default capacity 10, triggers multiple resizes
List<User> users = new ArrayList<>();
for (UserId id : allIds) {
    users.add(fetchUser(id));
}

// ✅ GOOD: Pre-size to avoid resize/copy overhead
List<User> users = new ArrayList<>(allIds.size());

// HashMap: capacity = expected_size / 0.75 + 1
Map<String, Order> orders = new HashMap<>((int)(expectedSize / 0.75f) + 1);
```

### Object Reuse & Hoisting

Move temporary objects out of loops and reuse them.

```java
// ❌ BAD: New StringBuilder per iteration
for (Record r : records) {
    StringBuilder sb = new StringBuilder();
    sb.append(r.getField1()).append(",").append(r.getField2());
    write(sb.toString());
}

// ✅ GOOD: Hoist and reuse
StringBuilder sb = new StringBuilder(128);
for (Record r : records) {
    sb.setLength(0);
    sb.append(r.getField1()).append(",").append(r.getField2());
    write(sb.toString());
}
```

### Index Over Object Reference

In pointer-dense data structures, use primitive arrays + integer indices instead of many small objects. Better memory efficiency and cache locality.

```java
// ❌ BAD: Many small objects, poor cache locality
class Edge { int target; double weight; }
List<Edge>[] graph = new List[nodeCount];

// ✅ GOOD: Primitive arrays, compact memory layout
int[] edgeTargets = new int[edgeCount];
double[] edgeWeights = new double[edgeCount];
int[] edgeOffsets = new int[nodeCount + 1];  // CSR format
```

---

## 4. Efficient API & Logic Design

### Bulk APIs

Process multiple elements in one call to amortize per-call overhead (lock acquisition, network, syscalls).

```java
// ❌ BAD: N separate calls, N lock acquisitions
for (Key key : keys) {
    cache.put(key, getValue(key));
}

// ✅ GOOD: Single batch call, one lock acquisition
Map<Key, Value> batch = new HashMap<>();
for (Key key : keys) {
    batch.put(key, getValue(key));
}
cache.putAll(batch);
```

### Fast Paths

Design shortcut logic for the most common simple case, avoiding expensive general processing.

```java
// ❌ BAD: Every request goes through full validation pipeline
Response handle(Request req) {
    return fullValidationPipeline(req);
}

// ✅ GOOD: Fast path for common case, slow path for edge cases
Response handle(Request req) {
    if (req.isSimpleRequest()) {
        return fastHandle(req);  // 99% of traffic
    }
    return fullValidationPipeline(req);  // 1% edge cases
}
```

### Lazy Evaluation

Defer expensive computation until the result is actually needed.

```java
// ❌ BAD: Eagerly computes even if unused
class Service {
    private final ExpensiveResult cached = computeExpensiveResult();
}

// ✅ GOOD: Lazy initialization
class Service {
    private volatile ExpensiveResult cached;
    ExpensiveResult getResult() {
        if (cached == null) {
            synchronized (this) {
                if (cached == null) {
                    cached = computeExpensiveResult();
                }
            }
        }
        return cached;
    }
}
```

### Avoid Logging on Hot Paths

Even disabled `LOG.debug()` can incur cost from argument construction.

```java
// ❌ BAD: String concatenation always executes
LOG.debug("Processing " + request.getId() + " with " + request.getItems().size() + " items");

// ✅ GOOD: Guard check, or use parameterized logging
if (LOG.isDebugEnabled()) {
    LOG.debug("Processing {} with {} items", request.getId(), request.getItems().size());
}
```

---

## 5. Concurrency & Synchronization

### Sharding (Segmented Locking)

Split high-contention structures into independent segments with separate locks.

```java
// ❌ BAD: Single lock, all threads serialize
class Counter {
    private final Object lock = new Object();
    private long count = 0;
    void increment() {
        synchronized (lock) { count++; }
    }
}

// ✅ GOOD: Sharded counters, minimal contention
class ShardedCounter {
    private final long[] counters;
    private final int shards;
    ShardedCounter(int shards) {
        this.shards = shards;
        this.counters = new long[shards];
    }
    void increment(int threadId) {
        int idx = threadId % shards;
        synchronized (new Object[0]) {} // placeholder
        // Use striped locks or AtomicIntegerArray
    }
}
```

**ConcurrentHashMap** is the canonical example: segments (or bins in Java 8+) each have independent locks.

### Shorten Critical Sections

Minimize code inside `synchronized`/`ReentrantLock`. **Never do I/O or network calls while holding a lock.**

```java
// ❌ BAD: I/O inside lock — blocks all other threads
synchronized (lock) {
    Data data = fetchFromNetwork();  // blocking!
    process(data);
}

// ✅ GOOD: Fetch outside lock, update inside
Data data = fetchFromNetwork();  // no lock held
synchronized (lock) {
    update(data);  // minimal critical section
}
```

### Lock-Free Alternatives

For extreme performance, use `Atomic*` classes or higher-level concurrent abstractions instead of mutexes.

```java
// ❌ BAD: Synchronized for simple counter
synchronized (lock) { count++; }

// ✅ GOOD: Lock-free atomic
private final AtomicLong count = new AtomicLong();
count.incrementAndGet();

// Or even better: LongAdder for high-contention counters
private final LongAdder count = new LongAdder();
count.increment();
```

| Scenario | Recommended |
|----------|------------|
| Simple counter | `LongAdder` (high contention) / `AtomicLong` (low contention) |
| Single producer-consumer | `AtomicReference` + CAS |
| Read-heavy map | `ConcurrentHashMap` |
| Queue | `ConcurrentLinkedQueue` / `ArrayBlockingQueue` |

---

## 6. Data Format & Serialization

### Protobuf vs Native Structures

Protobuf is convenient for serialization, but its object representation is much heavier than native Java structures. For in-memory computation, use native structures.

```java
// ❌ BAD: Using Protobuf objects for in-memory computation
List<OrderProto.Order> orders = new ArrayList<>();
for (OrderProto.Order o : orders) {
    total += o.getAmount();  // Protobuf getter overhead
}

// ✅ GOOD: Use plain Java objects for hot computation
class Order { final double amount; Order(double a) { this.amount = a; } }
List<Order> orders = new ArrayList<>();
for (Order o : orders) {
    total += o.amount;  // direct field access
}
// Convert to Protobuf only at serialization boundary
```

### Optimize Protobuf Fields

- **Field numbers 1-15** use 1 byte for encoding — prioritize most-used fields here
- **`fixed32`** for large numbers that don't need varint compression
- **`sint32`/`sint64`** for negative numbers (avoids 10-byte varint encoding)
- **`repeated` packed** for primitive lists (single field, no per-element tag)

```protobuf
// ❌ BAD: Wasteful encoding
message Order {
  optional int32 negative_value = 16;  // field >15 = 2 bytes tag; negative int32 = 10 bytes
  repeated int32 tags = 17;            // non-packed = tag per element
}

// ✅ GOOD: Compact encoding
message Order {
  optional int64 amount = 1;           // field 1-15 = 1 byte tag
  optional sint32 adjustment = 2;      // sint32 handles negatives efficiently
  repeated int32 tags = 3 [packed=true]; // packed = single tag + length
}
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Optimizing without measuring | Always profile first — intuition is often wrong |
| Micro-optimizing cold paths | Focus on the critical 3%, ignore the rest |
| Ignoring allocation in loops | Hoist/reuse objects, pre-size containers |
| I/O inside synchronized blocks | Move I/O outside, keep critical sections minimal |
| Using Protobuf for in-memory data | Use native POJOs; convert at boundaries only |
| Benchmarking with `System.nanoTime()` | Use JMH — it handles JIT/warmup/dead-code |
| Logging with string concat on hot paths | Guard with `isDebugEnabled()` or use parameterized |
| Default HashMap/ArrayList capacity | Pre-size when data volume is known |
| Single lock for high-contention data | Shard into segments with independent locks |
| Flat profile (no hotspot) | Design with performance awareness from the start |

## Performance Tuning Workflow

```
1. ESTIMATE    → Back-of-envelope calc to rule out bad designs
2. MEASURE     → JMH benchmark + profiler (Async-profiler/JFR)
3. IDENTIFY    → Find the critical 3% (hot path, allocation, contention)
4. OPTIMIZE    → Reduce allocation → shorten critical sections → fast paths
5. RE-MEASURE  → Verify improvement, check for regressions
6. MONITOR     → Production monitoring with sampling on hot paths
```
