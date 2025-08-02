"""Command-line interface."""

from __future__ import annotations

from typing import Annotated as Ann
from typer import Option as Opt
from typer import Typer

__all__ = []

cli = Typer(
    name="auto-appearance",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


_OF = Ann[bool, Opt("-f", "--force", help="Change regardless of time.")]
_OV = Ann[bool, Opt("-v", "--verbose", help="Be verbose.")]
_OLat = Ann[float, Opt("--lat", help="Latitude.")]
_OLon = Ann[float, Opt("--lon", help="Longitude.")]


@cli.command()
def main(lat: _OLat, lon: _OLon, force: _OF = False, verbose: _OV = False):
    """Toggle macOS's appearance to match the sun's position."""
    import logging
    from auto_appearance.app import update_appearance

    fmt = "[%(asctime)s] %(message)s"
    dtf = "%y-%m-%d %I:%M %p"
    logging.basicConfig(level=logging.WARNING, format=fmt, datefmt=dtf)
    logging.getLogger("auto_appearance").setLevel("DEBUG" if verbose else "INFO")

    update_appearance(lat=lat, lon=lon, force=force)


if __name__ == "__main__":
    cli()
