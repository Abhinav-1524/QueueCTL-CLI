# 🚀 QueueCTL — Python-Based Background Job Queue System

**Author:** Abhinav Karri  
**Program:** ECE , Amrita University (Hyderabad, India)

---

## 🧩 Project Overview

**QueueCTL** is a lightweight, command-line-based background job queue system built in Python.  
It enables users to **enqueue, schedule, and execute shell command jobs**, manage **worker threads**, and automatically handle **failures and retries** using a **persistent SQLite database**.  

The project also includes a **Flask-powered web dashboard** for real-time job tracking and a **bash test suite** to verify all system functionalities.

---
## Demo Video
[!Link to Drive](https://drive.google.com/file/d/1N4YDYXeW8rVnZjmWBzu52OkKPrczqZWH/view?usp=sharing)
---
## ⚙️ Key Functionalities

- 🧠 **Job Scheduling & Execution** — Enqueue and run shell command jobs.  
- 🧵 **Multi-Worker Concurrency** — Run multiple workers simultaneously.  
- 🔁 **Retry & Backoff Handling** — Automatic exponential retries for failed jobs.  
- 💾 **Persistent Storage** — All jobs stored in SQLite with timestamps and metadata.  
- 🧰 **DLQ (Dead Letter Queue)** — Failed jobs are moved for manual inspection or requeue.  
- 🕓 **Job Prioritization & run_at Scheduling** — Execute based on priority and time.  
- 🌐 **Flask Dashboard** — Minimal UI for queue monitoring and configuration.  
- 🧪 **Automated Testing Suite** — Bash-based tests for every core functionality.  

---

## 🧠 Architecture Overview

| Layer | Responsibility |
|-------|----------------|
| **CLI Layer (`cli/`)** | Handles user commands (enqueue, list, worker, DLQ, etc.) |
| **Core Layer (`core/`)** | Handles persistence, worker logic, retry system, and configuration |
| **Web Layer (`web/`)** | Provides the Flask dashboard for visualization |
| **Tests (`tests/`)** | Automated functional validation scripts |
| **Main Entry (`main.py`)** | Central CLI app that integrates all commands |

---

## 🧰 Tech Stack

| Component | Technology |
|------------|-------------|
| **Language** | Python 3.11+ |
| **CLI Framework** | Typer |
| **Database** | SQLite |
| **Web Framework** | Flask |
| **Testing** | Bash Shell Scripts |
| **Packaging** | setuptools |
| **Persistence** | Local SQLite (`store.db`) |

---

## ⚡ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/<your-username>/queuectl.git
cd queuectl
```

### Step 2: Create and Activate a Virtual Environment

```bash
python -m venv venv
source venv/Scripts/activate      
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Install QueueCTL Locally
```bash
pip install -e .
```

## CLI Usage
All functionality is available through the queuectl command.

### View General Help
```bash 
queuectl --help
```

### View Specific Command Help
```bash
queuectl enqueue --help
queuectl worker-start --help
queuectl dlq-list --help
queuectl config-show --help
```

| Category             | Example Command                                | Description                          |
| -------------------- | ---------------------------------------------- | ------------------------------------ |
| **Add Job**          | `queuectl enqueue '{"command":"echo Hello"}'`  | Enqueue a new job                    |
| **Start Worker**     | `queuectl worker-start --count 2`              | Launch workers for execution         |
| **Stop Worker**      | `queuectl worker-stop`                         | Gracefully stop active workers       |
| **List Jobs**        | `queuectl list --status pending`               | List all jobs by status              |
| **Queue Status**     | `queuectl status`                              | Display live job summary and threads |
| **DLQ Management**   | `queuectl dlq-list`, `queuectl dlq-retry <id>` | View or retry failed jobs            |
| **Configuration**    | `queuectl config-set max_retries 5`            | Modify config values                 |
| **Launch Dashboard** | `queuectl dashboard`                           | Start the web dashboard (Flask)      |



## Job Lifecycle 

| State        | Description                          |
| ------------ | ------------------------------------ |
| `pending`    | Job is waiting to execute            |
| `processing` | Job currently running                |
| `completed`  | Job executed successfully            |
| `failed`     | Job failed but retryable             |
| `dead`       | Job permanently failed, moved to DLQ |


## Configuration Management
Default configuration is stored in config.json:
```json
{
    "max_retries": 4,
    "backoff_base": 2,
    "worker_count": 1,
    "job_timeout": 45
}
```

### Modify Configuration
```bash
queuectl config-show
queuectl config-set max_retries 5
queuectl config-get job_timeout
queuectl config-reset
```

## Web Dashboard
Launch the dashboard:
```bash
queuectl dashboard
```

<img width="1917" height="831" alt="web" src="https://github.com/user-attachments/assets/a8f2c0bb-fb5a-4b15-b6de-f7da9d6559cc" />

Access it in the browser on Local Host

### Dashboard features
- Real-time job summary
- Color-coded job states
- Auto-refresh every 5 seconds
- 20 most recent jobs with status, priority, and attempts

## Testing
A full Bash-based test suite is included to validate all functionality.

### Run All Tests
```bash
chmod +x tests/*.sh
tests/test_all.sh
```

### Run Specific Tests
```bash
tests/test_01_enqueue.sh        # Enqueue validation
tests/test_02_worker.sh         # Worker execution
```

## Project File Structure 
```
queuectl/
├── cli/
│   ├── enqueue.py
│   ├── worker.py
│   ├── list_jobs.py
│   ├── dlq.py
│   ├── config_cli.py
│   └── status_cli.py
│
├── core/
│   ├── storage.py
│   ├── worker_engine.py
│   └── config.py
│
├── web/
│   └── dashboard.py
│
├── tests/
│   ├── test_01_enqueue.sh
│   ├── test_02_worker.sh
│   ├── test_03_dlq.sh
│   ├── test_04_config.sh
│   ├── test_05_status.sh
│   ├── test_06_scheduled_jobs.sh
│   ├── test_07_persistence.sh
│   ├── test_08_multi_worker.sh
│   ├── test_09_dlq_purge_confirm.sh
│   ├── test_10_end_to_end.sh
│   └── utils.sh
│
├── main.py
├── setup.py
├── requirements.txt
├── config.json
└── README.md
```
