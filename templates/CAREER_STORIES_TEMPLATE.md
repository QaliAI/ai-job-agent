# Career Story Bank (STAR Method)

> **Purpose**: Structured narratives (Situation, Task, Action, Result) describing high-impact projects, technical dilemmas, and interpersonal leadership. Used for answering application questions, cover letters, and interview preparation.

---

## Story 1: Scaling Event Ingestion Under 5x Traffic Surge

* **Target Competencies**: Distributed Systems, High Availability, Crisis Management, Kafka, Go
* **Situation**: CloudScale experienced an unprecedented 5x surge in inbound analytics events during a major client promotional launch, causing message queues to back up and data ingestion lag to exceed 4 hours.
* **Task**: Redesign the event ingestion subsystem to eliminate processing lag, prevent queue overflow, and establish auto-scaling resilience.
* **Action**:
  - Profiling identified bottleneck in single-threaded Python ingestion consumer.
  - Re-architected the ingestion worker tier in Go utilizing lightweight goroutines and a consumer group partition strategy with Apache Kafka.
  - Deployed Redis-based buffer for deduplicating repeated client events within a 60-second sliding window.
  - Established Prometheus metrics and Datadog alerts for consumer lag monitoring.
* **Result**: Ingestion lag reduced from 4 hours to under 2 seconds. System sustained 45,000 req/sec peak with zero dropped events, and infrastructure compute cost decreased by 22% due to Go's low memory footprint.

---

## Story 2: Resolving Severe PostgreSQL Production Latency & Deadlocks

* **Target Competencies**: Database Optimization, PostgreSQL, Troubleshooting, Cross-functional Communication
* **Situation**: The core transactional database suffered intermittent connection spikes and cascading deadlocks during daily peak hours, driving API p99 response times above 800ms and generating frequent HTTP 504 errors.
* **Task**: Diagnose the root cause of database contention, eliminate query deadlocks, and bring response times under 150ms SLA.
* **Action**:
  - Analyzed `pg_stat_statements` and active locks to trace the deadlock to un-indexed foreign key cascades in the billing transactions table.
  - Refactored conflicting ORM transactions into deterministic lock-ordered queries.
  - Added targeted composite indexes and configured PgBouncer connection pooling with transaction-level pooling.
  - Established staging benchmark harness simulating production workloads with `locust`.
* **Result**: Eliminated all deadlock incidents, dropped p99 API latency from 820ms to 95ms, and increased database connection headroom by 4x.
