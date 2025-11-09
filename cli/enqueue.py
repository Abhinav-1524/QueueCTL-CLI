import typer
import json
import uuid
from datetime import datetime, timezone
from dateutil import parser
from core.storage import Database
from core.config import Config

app = typer.Typer(help="enqueue jobs into QueueCTL")

db = Database()


@app.command()
def enqueue(
    job: str = typer.Argument(..., help="job JSON, e.g. '{\"command\":\"echo hello\"}'")
):
    """add a new job (with optional priority or run_at)"""

    # load defaults
    cfg = Config().all()

    # parse + validate input
    try:
        payload = json.loads(job)
    except json.JSONDecodeError:
        typer.secho("invalid JSON format", fg=typer.colors.RED)
        raise typer.Exit(1)

    job_id = payload.get("id", str(uuid.uuid4()))
    cmd = payload.get("command")

    if not cmd:
        typer.secho("missing required field 'command'", fg=typer.colors.RED)
        raise typer.Exit(1)

    # resolve parameters
    retries = int(payload.get("max_retries", cfg.get("max_retries", 3)))
    priority = int(payload.get("priority", 0))
    run_at = payload.get("run_at")

    # normalize run_at to UTC
    if run_at:
        try:
            dt = parser.parse(run_at)
            if not dt.tzinfo:
                dt = dt.astimezone()
            run_at = dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            run_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    else:
        run_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    # save job (use insert_job to match core.storage API)
    try:
        db.insert_job(job_id, cmd, retries, priority=priority, run_at=run_at)
    except Exception as e:
        typer.secho(f"failed to enqueue: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

    # display confirmation
    border = "-" * 60
    typer.secho("\njob added successfully", fg=typer.colors.GREEN, bold=True)
    typer.echo(border)
    typer.secho(f"ID        : {job_id}", fg=typer.colors.CYAN)
    typer.echo(f"Command   : {cmd}")
    typer.echo(f"Retries   : {retries}")
    typer.echo(f"Priority  : {priority}")
    typer.echo(f"Run At    : {run_at} UTC")
    typer.echo(border)
