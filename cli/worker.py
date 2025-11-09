import typer
import time
import os
from core.worker_engine import WorkerManager
from core.config import Config

app = typer.Typer(help="control background worker threads for QueueCTL")


@app.command()
def start(
    count: int = typer.Option(None, "--count", "-c", help="number of workers to start (override config)")
):
    """launch worker threads to process queued jobs"""

    border = "-" * 60
    typer.secho("\n[WORKER] launching worker processes", fg=typer.colors.CYAN, bold=True)
    typer.echo(border)

    # load config
    cfg = Config().all()
    worker_count = count or cfg.get("worker_count", 1)
    backoff = cfg.get("backoff_base", 2)

    typer.echo(f"Workers : {typer.style(worker_count, fg=typer.colors.GREEN)}")
    typer.echo(f"Backoff : {typer.style(backoff, fg=typer.colors.GREEN)}")
    typer.echo(border)

    mgr = WorkerManager(worker_count=worker_count, backoff_base=backoff)
    mgr.start_workers()

    typer.secho(f"OK {worker_count} worker(s) online", fg=typer.colors.GREEN, bold=True)
    typer.secho("Press Ctrl+C or run 'queuectl worker stop' to terminate", fg=typer.colors.BRIGHT_BLACK)

    # monitor loop
    try:
        while True:
            stop_file = getattr(WorkerManager, "STOP_SIGNAL_FILE", "stop_signal.json")

            if getattr(WorkerManager, "stop_flag", False):
                typer.secho("WARN stop flag detected (internal)", fg=typer.colors.YELLOW)
                break

            if os.path.exists(stop_file):
                typer.secho("WARN external stop signal received", fg=typer.colors.YELLOW)
                break

            active = [t for t in getattr(WorkerManager, "workers", []) if t.is_alive()]
            if not active:
                typer.secho("[INFO] no active workers remaining", fg=typer.colors.BLUE)
                break

            time.sleep(0.5)

    except KeyboardInterrupt:
        typer.secho("\nWARN keyboard interrupt — shutting down workers...", fg=typer.colors.YELLOW)
        mgr.stop_all()

    # graceful shutdown
    typer.secho("\n[WAIT] finalizing worker shutdown...", fg=typer.colors.CYAN)
    timeout = 10
    end_time = time.time() + timeout
    while time.time() < end_time and any(t.is_alive() for t in getattr(WorkerManager, "workers", [])):
        time.sleep(0.2)

    # clean up
    if os.path.exists(WorkerManager.STATUS_FILE):
        os.remove(WorkerManager.STATUS_FILE)

    typer.echo(border)
    typer.secho("OK all workers stopped cleanly", fg=typer.colors.GREEN, bold=True)
    typer.echo(border)


@app.command()
def stop():
    """signal all workers to stop gracefully"""
    typer.secho("[WORKER] sending stop signal...", fg=typer.colors.CYAN)
    WorkerManager.stop_all()
    typer.secho("OK stop signal issued successfully", fg=typer.colors.GREEN, bold=True)
