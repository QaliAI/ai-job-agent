# Career Stories: Jordan Taylor

## Story 1: Scaling Background Processing Under Peak Traffic
* **Competencies**: Distributed Task Queues, Go, Redis, Concurrency
* **Situation**: Background task queues were backing up during peak hours, causing customer notification delays of up to 45 minutes.
* **Task**: Redesign background worker architecture to handle 30,000+ jobs/min with real-time completion.
* **Action**: Migrated worker core to Go using worker pool goroutines, implemented Redis sorted sets for task prioritization, and added backpressure flow control.
* **Result**: Sustained 35,000 jobs/minute with sub-second execution latency and zero memory leaks.

## Story 2: Database Indexing & Connection Pooling Overhaul
* **Competencies**: PostgreSQL, Query Optimization, Reliability
* **Situation**: Transaction spikes caused connection pool exhaustion and high query latency on primary PostgreSQL databases.
* **Task**: Eliminate connection bottlenecks without costly database instance resizing.
* **Action**: Audited slow queries via `pg_stat_statements`, eliminated N+1 ORM queries, deployed PgBouncer transaction pooling, and created composite partial indexes.
* **Result**: Reduced average query response time by 48% and cut database CPU utilization by 30%.
