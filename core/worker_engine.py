import os
import json
import time
import signal
import threading
import platform
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

import typer
from core.storage import Database
from core.config import Config


class WorkerManager:
    """Worker pool that executes queued jobs with retry and logging."""

    STATUS_FILE = "worker_threads.json"
    STOP_SIGNAL_FILE = "stop_signal.json"
    stop_flag = False
    workers: list[threading.Thread] = []

    def __init__(self, worker_count: int = 1, backoff_base: int = 2):
        self.db = Database()
        self.config = Config()
        self.worker_count = worker_count
        self.backoff_base = backoff_base

    def _run_job_cycle(self) -> None:
        db = Database()
        logs = Path("logs")
        logs.mkdir(exist_ok=True)

        while not WorkerManager.stop_flag:
            self._refresh_status()

            # acquire job using storage.acquire_job (matches storage.py)
            job = db.acquire_job()
            if not job:
                time.sleep(1)
                continue

            job_id = job["id"]
            cmd = job["command"]
            attempts, max_retries = job["attempts"], job["max_retries"]
            timeout = int(self.config.get("job_timeout", 30))

            # mark processing already done by acquire_job; ensure log written
            log_path = logs / f"{job_id}.log"
            self._log_start(log_path, cmd, job_id, timeout)

            start = time.time()
            try:
                result = subprocess.run(cmd, shell=True, text=True, timeout=timeout)
                self._log_result(log_path, result, start)

                if result.stdout:
                    self._print_output(cmd, job_id, result.stdout)

                if result.returncode == 0:
                    db.update_status(job_id, "completed")
                    self._emit("OK", f"Job {job_id} finished — success")
                else:
                    raise subprocess.SubprocessError(f"Exit code {result.returncode}")

            except subprocess.TimeoutExpired:
                self._emit("WARN", f"{job_id} timeout after {timeout}s")
                self._append(log_path, f"TIMEOUT: {timeout}s")
                self._retry_or_fail(db, job_id, attempts, max_retries)

            except Exception as e:
                self._emit("ERR", f"{job_id} failed — {e}")
                self._append(log_path, f"ERROR: {e}")
                self._retry_or_fail(db, job_id, attempts, max_retries)

            if WorkerManager.stop_flag:
                self._emit("->", f"{threading.current_thread().name} received stop signal")
                break

            time.sleep(0.5)

        self._emit("->", f"{threading.current_thread().name} exited cleanly")
        self._refresh_status()

    def _retry_or_fail(self, db: Database, job_id: str, attempts: int, max_retries: int) -> None:
        try:
            db.bump_attempts(job_id)
            job = db.get_job(job_id)
            current = job["attempts"] if job else attempts + 1

            if current >= max_retries:
                db.update_status(job_id, "dead")
                self._emit("ERR", f"{job_id} moved to DLQ — max retries hit")
                return

            delay = self.backoff_base ** current
            retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)

            with db.con:
                db.con.execute(
                    "UPDATE jobs SET status='pending', run_at=?, updated_at=? WHERE id=?",
                    (
                        retry_at.strftime("%Y-%m-%d %H:%M:%S"),
                        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                        job_id,
                    ),
                )
            self._emit("->", f"{job_id} retry scheduled in {delay}s ({current}/{max_retries})")

        except Exception as e:
            db.update_status(job_id, "dead")
            self._emit("ERR", f"Retry handler error for {job_id}: {e}")

    def _log_start(self, path: Path, cmd: str, job_id: str, timeout: int) -> None:
        header = (
            f"[{datetime.now(timezone.utc).isoformat()}] START {job_id}\n"
            f"COMMAND : {cmd}\nTIMEOUT : {timeout}s\n{'-'*60}\n"
        )
        self._append(path, header)

    def _log_result(self, path: Path, result, start: float) -> None:
        duration = round(time.time() - start, 3)
        msg = (
            f"\nSTDOUT:\n{result.stdout or '(empty)'}"
            f"\nSTDERR:\n{result.stderr or '(none)'}"
            f"\nEXIT: {result.returncode}, DURATION: {duration}s\n{'-'*60}\n"
        )
        self._append(path, msg)

    @staticmethod
    def _append(path: Path, text: str) -> None:
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception:
            pass

    def start_workers(self) -> None:
        self._cleanup_stop_flag()
        self.db.restore_processing()

        self.workers.clear()
        for i in range(self.worker_count):
            t = threading.Thread(target=self._run_job_cycle, name=f"Worker-{i+1}", daemon=True)
            t.start()
            self.workers.append(t)

        self._emit("->", f"{self.worker_count} worker(s) started")
        self._refresh_status()
        self._setup_signals()

    @classmethod
    def stop_all(cls) -> None:
        cls.stop_flag = True
        try:
            with open(cls.STOP_SIGNAL_FILE, "w", encoding="utf-8") as f:
                json.dump({"stop": True, "timestamp": datetime.now(timezone.utc).isoformat()}, f, indent=2)
        except Exception:
            pass
        print("\n- Stop file written — workers will exit gracefully.")

    @staticmethod
    def _cleanup_stop_flag() -> None:
        try:
            if os.path.exists(WorkerManager.STOP_SIGNAL_FILE):
                os.remove(WorkerManager.STOP_SIGNAL_FILE)
        except Exception:
            pass

    @staticmethod
    def _setup_signals() -> None:
        def handler(signum, frame):
            print("\n- Interrupt received, stopping workers...")
            WorkerManager.stop_all()

        try:
            signal.signal(signal.SIGINT, handler)
            if platform.system() != "Windows":
                signal.signal(signal.SIGTERM, handler)
        except Exception:
            pass

    @staticmethod
    def _refresh_status() -> None:
        try:
            active = [t.name for t in threading.enumerate() if t.name.startswith("Worker-")]
            with open(WorkerManager.STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    {"active_workers": len(active), "threads": active, "timestamp": datetime.now(timezone.utc).isoformat()},
                    f,
                    indent=2,
                )
        except Exception:
            pass

    def _print_output(self, cmd: str, job_id: str, text: str) -> None:
        border = "-" * 60
        typer.secho(f"\n{border}", fg=typer.colors.BRIGHT_BLACK)
        typer.secho(f" Output: {cmd}  ({job_id})", fg=typer.colors.CYAN, bold=True)
        typer.secho(border, fg=typer.colors.BRIGHT_BLACK)
        typer.secho(text.strip(), fg=typer.colors.GREEN)
        typer.secho(border, fg=typer.colors.BRIGHT_BLACK)

    @staticmethod
    def _emit(icon: str, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"{ts} {icon} {msg}")
