import typer
from core.storage import Database

app = typer.Typer(help="list and filter queue jobs")
db = Database()


@app.command()
def list(
    status: str = typer.Option(
        "all",
        "--status",
        "-s",
        help="filter by job status (pending, processing, completed, failed, dead, or all)",
    )
):
    """show jobs by status"""
    try:
        # fetch jobs
        if status.lower() == "all":
            rows = db.con.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
        else:
            rows = db.list_by_status(status)

        border = "-"* 70
        typer.secho(f"\nQueue — {status.upper()}", fg=typer.colors.BRIGHT_BLUE, bold=True)
        typer.echo(border)

        if not rows:
            typer.secho(f"WARN no jobs with status '{status}'", fg=typer.colors.YELLOW)
            raise typer.Exit()

        # table header
        typer.secho(f"{'ID':<34} {'STATE':<11} {'PRIORITY':<8} {'TRIES':<7} {'CREATED'}", bold=True)
        typer.echo(border)

        # job entries
        for job in rows:
            color = {
                "pending": typer.colors.CYAN,
                "processing": typer.colors.MAGENTA,
                "completed": typer.colors.GREEN,
                "failed": typer.colors.RED,
                "dead": typer.colors.BRIGHT_BLACK,
            }.get(job["status"], typer.colors.WHITE)

            typer.secho(
                f"{job['id']:<34} "
                f"{job['status']:<11} "
                f"{job['priority']:<8} "
                f"{job['attempts']:<7} "
                f"{job['created_at']}",
                fg=color,
            )

        typer.echo(border)
        typer.secho(f"OK total jobs: {len(rows)}", fg=typer.colors.GREEN)

    except Exception as e:
        typer.secho(f"ERR failed to list jobs: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)
