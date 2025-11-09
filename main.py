import sys
import subprocess
import typer

# CLI command imports (import function names from cli modules)
from cli.enqueue import enqueue as enqueue_cmd
from cli.list_jobs import list as list_jobs_cmd
from cli.worker import start as worker_start_cmd, stop as worker_stop_cmd
from cli.dlq import list as dlq_list_cmd, retry as dlq_retry_cmd, purge as dlq_purge_cmd
from cli.config_cli import set as config_set_cmd, get as config_get_cmd, show as config_show_cmd, reset as config_reset_cmd
from cli.status_cli import show as status_show_cmd

app = typer.Typer(
    help="QueueCTL — lightweight background job processor (CLI-based)",
    add_completion=False,
)

# Core Queue Ops
app.command("enqueue")(enqueue_cmd)
app.command("list")(list_jobs_cmd)

# Worker Management
app.command("worker-start")(worker_start_cmd)
app.command("worker-stop")(worker_stop_cmd)

# Dead Letter Queue
app.command("dlq-list")(dlq_list_cmd)
app.command("dlq-retry")(dlq_retry_cmd)
app.command("dlq-purge")(dlq_purge_cmd)

# Configuration
app.command("config-set")(config_set_cmd)
app.command("config-get")(config_get_cmd)
app.command("config-show")(config_show_cmd)
app.command("config-reset")(config_reset_cmd)

# System State
app.command("status")(status_show_cmd)


@app.command("dashboard")
def dashboard():
    """launch the QueueCTL web dashboard"""
    border = "-" * 60
    typer.secho("\nlaunching dashboard", fg=typer.colors.CYAN, bold=True)
    typer.echo(border)
    typer.secho("URL -> http://127.0.0.1:5000", fg=typer.colors.BRIGHT_BLUE)
    typer.echo(border)
    subprocess.run([sys.executable, "web/dashboard.py"])


if __name__ == "__main__":
    typer.secho("╭--------------------------------------------╮", fg=typer.colors.BRIGHT_BLACK)
    typer.secho("│        QueueCTL Command Line Utility       │", fg=typer.colors.BRIGHT_CYAN, bold=True)
    typer.secho("╰--------------------------------------------╯", fg=typer.colors.BRIGHT_BLACK)
    app()
