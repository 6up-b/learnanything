"""Local administration for the narrow mobile capture service."""
from pathlib import Path
import json
from typing import Annotated

import typer

from learnloop_mobile.config import load_config

app = typer.Typer(no_args_is_help=True)
inbox_app = typer.Typer(no_args_is_help=True)
app.add_typer(inbox_app, name="inbox")
ConfigOption = Annotated[Path | None, typer.Option("--config", help="Machine mobile.toml")]


def _config(path):
    try:
        return load_config(path)
    except (OSError, ValueError) as exc:
        typer.echo(f"Invalid mobile configuration: {exc}", err=True)
        raise typer.Exit(78) from None


def _repo(config, *, read_only=False):
    from learnloop_mobile.host import SchemaMismatch, attach
    try:
        return attach(config, read_only=read_only)
    except (SchemaMismatch, OSError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(78) from None


def _print(value):
    typer.echo(json.dumps(value, indent=2, default=str))


@app.command()
def serve(config: ConfigOption = None, host: str = "127.0.0.1"):
    """Serve on loopback only; expose it exclusively through Tailscale Serve."""
    if host != "127.0.0.1":
        typer.echo("Only --host 127.0.0.1 is permitted", err=True)
        raise typer.Exit(78)
    settings = _config(config)
    from learnloop_mobile.host import SchemaMismatch, create_app
    import uvicorn
    try:
        application = create_app(settings)
    except (SchemaMismatch, OSError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(78) from None
    uvicorn.run(application, host="127.0.0.1", port=settings.port, workers=1,
                proxy_headers=False, access_log=False, limit_concurrency=32,
                timeout_keep_alive=5, h11_max_incomplete_event_size=16 * 1024,
                http="h11", ws="none")


@app.command()
def pair(config: ConfigOption = None, label: str = "Phone", scope: str = "capture"):
    """Issue a five-minute, single-use QR fragment and manual pairing code."""
    from learnloop.capture import CaptureError, create_pairing
    import qrcode
    settings = _config(config)
    try:
        result = create_pairing(_repo(settings), label=label, scope=scope)
    except CaptureError as exc:
        typer.echo(exc.message, err=True)
        raise typer.Exit(1) from None
    url = f"https://{settings.hostname}/pair#s={result['secret']}"
    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.print_ascii(invert=True)
    typer.echo(url)
    typer.echo(f"Manual code: {result['code']}\nExpires: {result['expires_at']}")


@app.command()
def devices(config: ConfigOption = None):
    """List paired devices, including never-seen devices."""
    from learnloop.capture import list_devices
    _print(list_devices(_repo(_config(config))))


@app.command()
def revoke(device_id: str, config: ConfigOption = None):
    """Revoke a device on its next request."""
    from learnloop.capture import revoke_device
    _print(revoke_device(_repo(_config(config)), device_id))


@inbox_app.command("list")
def inbox_list(config: ConfigOption = None, limit: int = 100, offset: int = 0):
    """List captures without starting any background processing."""
    from learnloop.capture import list_captures
    _print(list_captures(_repo(_config(config), read_only=True), limit=limit, offset=offset))


@app.command()
def doctor(
    config: ConfigOption = None,
    env_file: Annotated[Path | None, typer.Option("--env-file")] = None,
    as_json: Annotated[bool, typer.Option("--json")] = False,
):
    """Inspect local configuration, Serve, and policy confirmation requirements."""
    from learnloop_mobile.doctor import doctor as run_doctor
    result = run_doctor(_config(config), env_file=env_file)
    _print(result)
    if not result["ok"]:
        raise typer.Exit(1)
