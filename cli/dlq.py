import typer
from core.storage import Database

app = typer.Typer(help="Dead Letter Queue (DLQ) management")

db = Database()


# ------------------------------
# list DLQ
# ------------------------------
@app.command()
def list():
    """show all jobs currently marked as dead"""
    try:
        jobs = db.list_by_status("dead")
        if not jobs:
            typer.secho("WARN no jobs in DLQ", fg=typer.colors.YELLOW)
            raise typer.Exit()

        border = "-" * 60
        typer.secho("\nDead Letter Queue", fg=typer.colors.BRIGHT_BLUE, bold=True)
        typer.echo(border)

        for j in jobs:
            typer.secho(f"ID        : {j['id']}", fg=typer.colors.CYAN)
            typer.echo(f"Command   : {j['command']}")
            typer.echo(f"Attempts  : {j['attempts']}/{j['max_retries']}")
            typer.echo(f"Created   : {j['created_at']}")
            typer.echo(f"Updated   : {j['updated_at']}")
            typer.secho(f"Status    : {j['status']}", fg=typer.colors.BRIGHT_BLACK)
            typer.echo(border)

    except Exception as e:
        typer.secho(f"ERR failed to list DLQ: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


# ------------------------------
# retry DLQ job
# ------------------------------
@app.command()
def retry(job_id: str):
    """move a DLQ job back to pending"""
    try:
        job = db.get_job(job_id)
        if not job:
            typer.secho(f"ERR no job found with ID {job_id}", fg=typer.colors.RED)
            raise typer.Exit(1)

        if job["status"] != "dead":
            typer.secho(
                f"WARN job {job_id} not in DLQ (status: {job['status']})",
                fg=typer.colors.YELLOW,
            )
            raise typer.Exit(1)

        db.update_status(job_id, "pending")
        db.con.execute("UPDATE jobs SET attempts=0 WHERE id=?", (job_id,))
        db.con.commit()

        typer.secho(f"OK job {job_id} moved to pending", fg=typer.colors.GREEN, bold=True)

    except Exception as e:
        typer.secho(f"ERR retry failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


# ------------------------------
# purge DLQ
# ------------------------------
@app.command()
def purge(confirm: bool = typer.Option(False, "--confirm", help="confirm permanent deletion")):
    """delete all DLQ jobs (irreversible)"""
    if not confirm:
        typer.secho("WARN add '--confirm' to purge DLQ", fg=typer.colors.YELLOW)
        raise typer.Exit(1)

    try:
        with db.con:
            db.con.execute("DELETE FROM jobs WHERE status='dead'")
        typer.secho("OK all DLQ jobs deleted", fg=typer.colors.GREEN, bold=True)
    except Exception as e:
        typer.secho(f"ERR purge failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)
