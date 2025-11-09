import typer
import os
import json
from datetime import datetime
from core.storage import Database

app = typer.Typer(help="show live queue + worker status")
db = Database()


@app.command()
def show():
    """display job summary and active worker threads"""
    border = "-" * 60
    typer.echo()

    # -----------------------------------------------
    # JOB SUMMARY
    # -----------------------------------------------
    typer.secho("Queue Summary", fg=typer.colors.BRIGHT_BLUE, bold=True)
    typer.echo(border)

    summary = db.summary()
    states = ["pending", "processing", "completed", "failed", "dead"]

    for state in states:
        count = summary.get(state, 0)
        color = {
            "pending": typer.colors.CYAN,
            "processing": typer.colors.MAGENTA,
            "completed": typer.colors.GREEN,
            "failed": typer.colors.RED,
            "dead": typer.colors.BRIGHT_BLACK,
        }.get(state, typer.colors.WHITE)
        typer.secho(f"{state.capitalize():<12}: {count}", fg=color)

    typer.echo(border)

    # -----------------------------------------------
    # WORKER STATUS
    # -----------------------------------------------
    typer.secho("\nWorker Threads", fg=typer.colors.BRIGHT_BLUE, bold=True)
    typer.echo(border)

    status_file = "worker_threads.json"
    stop_file = "stop_signal.json"

    # active worker info
    try:
        if os.path.exists(status_file):
            with open(status_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            active = data.get("active_workers", 0)
            threads = data.get("threads", [])
            timestamp = data.get("timestamp", "N/A")

            typer.secho(f"Active  : {active}", fg=typer.colors.GREEN if active else typer.colors.YELLOW)
            typer.echo(f"Threads : {', '.join(threads) if threads else '(none)'}")
            typer.echo(f"Updated : {timestamp}")
        else:
            typer.secho("Active  : 0 (no threads running)", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"WARN unable to read worker status: {e}", fg=typer.colors.RED)

    # stop signal
    try:
        if os.path.exists(stop_file):
            with open(stop_file, "r", encoding="utf-8") as f:
                stop_data = json.load(f)
            ts = stop_data.get("timestamp", "unknown")
            typer.secho(f"\nStop Signal : {ts}", fg=typer.colors.BRIGHT_BLACK)
    except Exception as e:
        typer.secho(f"WARN stop signal read error: {e}", fg=typer.colors.RED)

    typer.echo(border)

    typer.secho(f"OK status updated @ {datetime.now().strftime('%H:%M:%S')}", fg=typer.colors.GREEN, bold=True)
