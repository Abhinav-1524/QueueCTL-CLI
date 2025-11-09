# QueueCTL — Architectural Overview

### Backend Developer Internship Project  
**Author:** Abhinav Karri | Electronics & Communication Engineering — Amrita University  
**Project Title:** Command-Line Driven Background Job Queue System  

---

## 1. Overview

`QueueCTL` is a **command-line-based background task scheduler and processor** that executes shell commands asynchronously.  
It supports **multi-threaded workers**, **automatic retry using exponential backoff**, **persistent job storage** via SQLite, and includes a **web-based dashboard** for live system monitoring through Flask.

This document outlines the **software design**, **component-level structure**, and **interaction flow** between key modules.

---

## 2. System Architecture (High-Level)

```
┌─────────────────────────────────────────────┐
│                Command Line                 │
│                  (queuectl)                 │
│     User Input & CLI Command Execution      │
└────────────────────────┬────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────┐
│              CLI Interface (Typer)          │
│   Parses commands → triggers backend logic  │
└────────────────────────┬────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────┐
│              Worker Engine                  │
│     Handles job scheduling, threading,      │
│   execution, retries, and state updates     │
└────────────────────────┬────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────┐
│              SQLite Database                │
│   Persistent storage for jobs, states,      │
│     configuration, and DLQ records          │
└────────────────────────┬────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────┐
│             Web Dashboard (Flask)           │
│  Real-time job monitoring & configuration   │
│   via browser interface (localhost:5000)    │
└────────────────────────┬────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────┐
│                Job Lifecycle                │
│   Pending → Processing → Completed →        │
│   Failed → Dead (DLQ Retry Path)            │
└─────────────────────────────────────────────┘
```



---

## 3. Core Modules

### 3.1 Command-Line Interface (`cli/`)
Implements all user-level commands through the **Typer** library, providing a clean, structured CLI experience.

| File | Functionality |
|------|----------------|
| `enqueue.py` | Adds new tasks into the queue, supports scheduling, prioritization, and retries |
| `worker.py` | Starts or stops worker threads that process background tasks |
| `list_jobs.py` | Lists jobs based on their current status |
| `dlq.py` | Handles the Dead Letter Queue for failed or unprocessed jobs |
| `config_cli.py` | Manages configuration updates and displays system parameters |
| `status_cli.py` | Shows current system and worker health statistics |

---

### 3.2 Core Layer (`core/`)
Contains the fundamental logic powering the queue management and job lifecycle.

| File | Functionality |
|------|----------------|
| `worker_engine.py` | Manages worker lifecycle, thread orchestration, and retry policies |
| `storage.py` | Responsible for database transactions and persistence mechanisms |
| `config.py` | Loads and maintains runtime configuration values from `config.json` |

---

### 3.3 Web Layer (`web/dashboard.py`)
Provides a **Flask-powered** visualization panel that enables:
- Real-time system overview
- Job distribution by state (pending, running, success, failed, dead)
- Auto-refresh capability (every 5 seconds)
- Clean and responsive design for rapid status checks

---

## 4. Workflow and Data Movement

### 4.1 Job Execution Pipeline

1. **Job Submission**
   - A user executes:  
     `queuectl enqueue '{"command": "echo Hello"}'`
   - The command is recorded in SQLite with a `pending` status and assigned a unique identifier.

2. **Worker Initialization**
   - Executing `queuectl worker-start --count 3` launches multiple worker threads.
   - Each worker fetches pending jobs for processing.

3. **Execution Phase**
   - The job is locked for execution and marked as `processing`.
   - The command runs via Python’s `subprocess.run()` method.

4. **Completion Handling**
   - On success → status updates to `completed`.  
   - On failure → retries are scheduled following an exponential backoff.

5. **Dead Letter Queue (DLQ)**
   - Jobs that exceed retry limits are tagged as `dead`.
   - They can be retried manually through `queuectl dlq-retry <job_id>`.

---

## 5. Database Schema (SQLite)

| Column | Type | Purpose |
|--------|------|----------|
| `id` | TEXT | Unique job identifier |
| `command` | TEXT | Command or script to execute |
| `status` | TEXT | Current state: pending / processing / completed / failed / dead |
| `priority` | INTEGER | Defines job execution order |
| `attempts` | INTEGER | Number of retry attempts |
| `max_retries` | INTEGER | Retry limit |
| `run_at` | TEXT | Scheduled execution time |
| `created_at` | TEXT | Time when the job was created |
| `updated_at` | TEXT | Last updated timestamp |

---

## 6. Worker Engine Design

### Multi-threaded Execution Model

- Workers are implemented as **Python threads** within a shared process.
- Each thread:
  1. Fetches a single pending job.
  2. Executes using `subprocess.run()`.
  3. Logs output in `logs/<job_id>.log`.
  4. Updates the job’s record in SQLite.
  5. On failure, calculates retry delay:
     ```
     delay = backoff_base ^ attempts
     ```
  6. Transfers irrecoverable jobs to the Dead Letter Queue.

---

## 7. Concurrency and Fault Tolerance

- Employs the **threading** library for parallel execution.
- SQLite ensures **transactional integrity** during concurrent operations.
- Workers listen for a shutdown trigger file (`stop_signal.json`) to terminate gracefully.
- Active worker states are monitored through `worker_threads.json`.

---

## 8. Configuration Management

System parameters are centralized in a `config.json` file.

**Example Configuration:**
```json
{
    "max_retries": 4,
    "backoff_base": 2,
    "worker_count": 1,
    "job_timeout": 45
}

```
| Key            | Description                                         |
| -------------- | --------------------------------------------------- |
| `max_retries`  | Defines how many times a failed task can be retried |
| `backoff_base` | Base value for exponential retry delay              |
| `worker_count` | Default number of threads to launch                 |
| `job_timeout`  | Time limit for each job before timeout              |

```
```

## 9. Web Dashboard Interface

The **Flask-powered dashboard** provides a clear, auto-refreshing web interface for monitoring system activity.

### Features:
- Displays live job statistics by category — *pending, processing, completed, failed,* and *dead.*
- Shows the **20 most recent jobs** along with priority, attempts, and timestamps.
- Refreshes automatically every **5 seconds** for real-time updates.
- Built with **lightweight CSS and Bootstrap-inspired styling** to ensure readability and fast rendering.

### Purpose:
The dashboard enables developers and system administrators to visually monitor worker performance, identify failed jobs, and confirm that the queue system is functioning efficiently.

---

## 10. Logging and Error Management

To maintain transparency and traceability, QueueCTL uses a structured logging system and unified error-handling mechanism.

### Key Logging Details:
- Each job execution writes output to a dedicated log file located in the `logs/` directory.
- Logs are named as `<job_id>.log` for quick identification.
- System-wide messages are prefixed for consistency:
  - `[INFO]` – General operational messages  
  - `[OK]` – Successful job execution or completion  
  - `[WARN]` – Recoverable issue detected  
  - `[FAIL]` – Critical error or failure condition  

### Error Recovery:
- Failed jobs are retried based on exponential backoff logic.
- Exhausted jobs are sent to the Dead Letter Queue (DLQ) for manual inspection.
- Typer’s colored CLI output improves readability, helping users easily differentiate between success, warning, and failure states.

---

## 11. Persistence and System Recovery

QueueCTL ensures **data durability and smooth recovery** during system restarts or unexpected shutdowns.

### Persistence Layer:
- All job-related information is stored in an **SQLite database** (`store.db`).
- Job states are updated atomically, ensuring consistency across concurrent threads.

### Recovery Logic:
Upon restarting the system:
1. Jobs previously marked as `processing` are safely reset to `pending`.
2. Newly spawned workers automatically resume job execution.
3. Incomplete jobs are re-queued without duplication or data loss.

This design ensures **fault tolerance**, so no job is lost or left in an undefined state even after an interruption.

---

## Summary

- **QueueCTL** adopts a **modular, three-layer design**: Command-Line Interface, Core Processing Engine, and Web Monitoring Dashboard.  
- Its **multi-threaded architecture** allows simultaneous task execution, improving system throughput.  
- **SQLite-based persistence** provides lightweight yet reliable data storage with transactional safety.  
- The **Flask dashboard** offers real-time insights into queue and worker performance.  
- With robust **error handling**, **automatic recovery**, and **retry mechanisms**, the system is production-ready and designed for scalability and maintainability.

---
