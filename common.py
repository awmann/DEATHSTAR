"""
common.py
=========
Shared target-info and time-conversion logic for Extracting_Lightcurves.py
and Plotting.py. Previously duplicated (slightly differently) in both
files -- that duplication is exactly why a `dec` typo bug existed in one
copy and not the other. Two real fixes live here:

1. get_target_info() accepts a manual_ephemeris override. DEATHSTAR's
   whole purpose is confirming/refuting *candidate* signals, so requiring
   an alerted ExoFOP TOI with submitted planet_parameters (the previous
   only path) is backwards -- most targets worth running this on are
   exactly the ones that AREN'T alerted yet. manual_ephemeris takes
   priority when supplied; give it {ra, dec, period, epoch, depth, Tmag}
   at minimum (period_uncertainty/epoch_uncertainty/duration default to
   sane fallbacks if omitted -- duration in particular can be derived from
   period/depth/Tmag with a rough a/Rs assumption, but pass it explicitly
   if you have a real transit-model fit; the fallback is not a substitute).

2. convert_time_to_bjd() replaces the OSU astroutils convert.php
   dependency, which has been permanently retired (confirmed via its own
   shutdown notice page, which points to barycorrpy/plain astropy as the
   suggested replacement -- this *is* that replacement). Geocentric light
   travel time (no specific observatory site) matches what the old service
   computed; the difference vs a real site is at most ~21ms, negligible
   for ground-based photometric cadences.
"""
import json
import urllib.request

import numpy as np
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation
import astropy.units as u

_EARTH_CENTER = EarthLocation.from_geocentric(0 * u.m, 0 * u.m, 0 * u.m)

REQUIRED_MANUAL_KEYS = ("ra", "dec", "period", "epoch", "depth", "Tmag")


def get_target_info(tic_id, manual_ephemeris=None):
    """Returns a dict: ra, dec, period (days), period_uncertainty (days),
    depth (ppm), epoch (BJD), epoch_uncertainty (days), duration (hours),
    Tmag. Pulled from ExoFOP for an alerted TOI, or taken directly from
    manual_ephemeris when supplied (required for any non-alerted TIC --
    ExoFOP's planet_parameters is empty for those and the lookup will
    raise IndexError)."""
    if manual_ephemeris is not None:
        missing = [k for k in REQUIRED_MANUAL_KEYS if k not in manual_ephemeris]
        if missing:
            raise ValueError(f"manual_ephemeris is missing required key(s): {missing}")
        info = dict(manual_ephemeris)
        info.setdefault("period_uncertainty", 0.0)
        info.setdefault("epoch_uncertainty", 0.0)
        if "duration" not in info:
            # rough fallback (circular, edge-on, a/Rs~10) -- pass a real
            # value from your own transit fit whenever you have one
            info["duration"] = 3.0
        return {k: float(info[k]) for k in
                ("ra", "dec", "period", "period_uncertainty", "depth",
                 "epoch", "epoch_uncertainty", "duration", "Tmag")}

    url = f"https://exofop.ipac.caltech.edu/tess/target.php?id={tic_id}&json"
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())
    pp = data.get("planet_parameters") or []
    if len(pp) < 2:
        raise IndexError(
            f"TIC {tic_id} has no ExoFOP-submitted planet_parameters (not an "
            f"alerted TOI, or no community fit yet) -- pass manual_ephemeris "
            f"instead of relying on the ExoFOP lookup for this target."
        )
    return {
        "ra": float(data["coordinates"]["ra"]),
        "dec": float(data["coordinates"]["dec"]),
        "period": float(pp[1]["per"]),
        "period_uncertainty": float(pp[1]["per_e"]),
        "depth": float(pp[1]["dep_p"]),
        "epoch": float(pp[1]["epoch"]),
        "epoch_uncertainty": float(pp[1]["epoch_e"]),
        "duration": float(pp[1]["dur"]),
        "Tmag": float(data["magnitudes"][0]["value"]),
    }


def convert_time_to_bjd(days, ra, dec, bjd_to_jd=False):
    """days: a single JD/BJD value, or a comma-separated string of them
    (matching the old OSU API's batch-query convention, still used by
    Extracting_Lightcurves.py's chunked calls). Returns a list of floats."""
    jds = [float(x) for x in days.split(",")] if isinstance(days, str) else [float(days)]
    coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
    if bjd_to_jd:
        t = Time(jds, format="jd", scale="tdb", location=_EARTH_CENTER)
        ltt = t.light_travel_time(coord)
        return list((t - ltt).utc.jd)
    t = Time(jds, format="jd", scale="utc", location=_EARTH_CENTER)
    ltt = t.light_travel_time(coord)
    return list((t.tdb + ltt).jd)
