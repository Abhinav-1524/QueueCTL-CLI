import typer
from core.config import Config

app = typer.Typer(help="QueueCTL configuration utility")

cfg = Config()

# ------------------------------
# set value
# ------------------------------
@app.command()
def set(key: str, value: str):
    """update a config key"""
    try:
        if value.lower() in {"true", "false"}:
            val = value.lower() == "true"
        else:
            try:
                val = int(value)
            except ValueError:
                val = value

        cfg.set(key, val)
        typer.secho(f"OK {key} updated -> {val}", fg=typer.colors.GREEN, bold=True)

    except Exception as e:
        typer.secho(f"ERR failed to update config: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

# ------------------------------
# get value
# ------------------------------
@app.command()
def get(key: str):
    """fetch a config key"""
    try:
        val = cfg.get(key)
        if val is None:
            typer.secho(f"WARN no entry for '{key}'", fg=typer.colors.YELLOW)
        else:
            typer.secho(f"{key}: {val}", fg=typer.colors.CYAN, bold=True)
    except Exception as e:
        typer.secho(f"ERR read error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

# ------------------------------
# show all
# ------------------------------
@app.command()
def show():
    """show all current settings"""
    try:
        data = cfg.all()
        border = "-"* 40
        typer.secho("\nQueueCTL Configuration", fg=typer.colors.BRIGHT_BLUE, bold=True)
        typer.echo(border)
        for k, v in data.items():
            typer.secho(f"{k:<15} {v}", fg=typer.colors.WHITE)
        typer.echo(border)
    except Exception as e:
        typer.secho(f"ERR unable to load config: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

# ------------------------------
# reset
# ------------------------------
@app.command()
def reset():
    """restore default values"""
    try:
        cfg.restore_defaults()
        typer.secho("OK configuration reset to defaults", fg=typer.colors.GREEN, bold=True)
    except Exception as e:
        typer.secho(f"ERR reset failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)
