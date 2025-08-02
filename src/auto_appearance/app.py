"""Help macOS get its act together to change light/dark mode."""

from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime
from enum import StrEnum
from operator import itemgetter
from pathlib import Path
from typing import Final
from platformdirs import user_data_path

__all__ = ["update_appearance", "compute_sun_times"]

lg = logging.getLogger(__name__)

# Where to write metadata
JSON_PATH: Final[Path] = user_data_path(appname="Auto Appearance") / "last-update.json"


class Appearance(StrEnum):
    LIGHT = "light"
    DARK = "dark"


class Motion(StrEnum):
    SUNRISE = "sunrise"
    SUNSET = "sunset"


def update_appearance(lat: float, lon: float, force: bool = False) -> None:
    """Toggle macOS's appearance to match the sun's position.

    Args:
        lat: Latitude of the target location.
        lon: Longitude of the target location.
        force: Whether to force the update regardless of time.
        verbose: Whether to be verbose.

    """
    lg.debug(f"User provided {lat = } & {lon = }")

    # How we want dates displayed in logs
    dfmt_ = "%y-%m-%d %I:%M %p"

    # Check whether we need to even run the change
    last_movement = max(compute_sun_times(lat, lon, shift=1).values())
    last_update = _fetch_last_update()

    lu_ = "Never" if last_update is None else f"{last_update:{dfmt_}}"
    lg.info(f"Last motion = {last_movement:{dfmt_}}, Last update = {lu_}")

    # If the program made a change since the last motion, we
    # shouldn't run again. Don't want to override a user's
    # manual change, for example.
    if not force and last_update and last_update > last_movement:
        lg.info("Last change occurred after sun motion, so will not act.")
        return

    # At this point, we need to do the update. Sort the sunrise
    # and sunset times so we can use them in a moment.
    times = dict(sorted(compute_sun_times(lat, lon).items(), key=itemgetter(1)))

    msg_ = ", ".join(f"{k.title()} @ {times[k]:{dfmt_}}" for k in times)
    lg.info(f"Next sun times: {msg_}")

    # If sunrise is next we should be dark now and vice versa.
    next_motion = next(iter(times))
    appearance = Appearance.DARK if next_motion == Motion.SUNRISE else Appearance.LIGHT

    lg.info(f'Updating appearance = "{appearance}"')
    _set_appearance(appearance)


def compute_sun_times(lat: float, lon: float, shift: int = 0) -> dict[Motion, datetime]:
    """Compute sunrise and sunset times."""
    import ephem

    sun = ephem.Sun()  # type: ignore[unresolved-attribute]

    home = ephem.Observer()
    home.lat = str(lat)
    home.lon = str(lon)

    home.date -= shift

    rising = ephem.localtime(home.next_rising(sun))
    setting = ephem.localtime(home.next_setting(sun))
    lg.debug(f"Next rising time = {rising}, setting time = {setting}")

    return {Motion.SUNRISE: rising, Motion.SUNSET: setting}


def _fetch_last_update() -> datetime | None:
    """Read the last update time from storage."""
    if not JSON_PATH.exists():
        return None
    last_time = json.load(JSON_PATH.open()).get("last_update", None)
    if last_time is None:
        return None
    return datetime.fromisoformat(last_time)


def _set_appearance(mode: Appearance) -> None:
    """Set and record the OS appearance."""
    cmd = (
        'tell application "System Events" to '
        "tell appearance preferences to "
        f"set dark mode to {str(mode == 'dark').lower()}"
    )

    subprocess.run(["/usr/bin/osascript", "-e", cmd], check=True)  # noqa: S603

    JSON_PATH.parent.mkdir(exist_ok=True)
    json.dump({"last_update": datetime.now().isoformat()}, JSON_PATH.open("wt"))
