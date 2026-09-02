"""
Resume DEATHSTAR after the frame-extraction loop finished but the JD->BJD
conversion step crashed. The OSU astroutils convert.php service DEATHSTAR
depends on has been permanently retired (confirmed via its own replacement
notice page) -- not a transient outage. Its own suggested alternative list
includes barycorrpy / plain astropy light-travel-time correction, which is
what real BJD_TDB conversion is anyway, so replacing it locally is the
correct fix, not a workaround. All 878 frames' raw photometry is already
safely saved in All_400084288_Star_Data.csv; this only redoes the final
time-conversion + plotting steps, not the ~20-minute frame loop.
"""
import sys
sys.path.insert(0, ".")
import pandas as pd
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation
import astropy.units as u

EARTH_CENTER = EarthLocation.from_geocentric(0 * u.m, 0 * u.m, 0 * u.m)  # no-site approx,
                                                                            # <=21ms error vs a real
                                                                            # surface site -- negligible

import Extracting_Lightcurves as EL

TIC_ID = 400084288
RA, DEC = 133.663342, -49.349928


def local_bjd_convert(days_str, ra, dec, bjd_to_jd):
    if isinstance(days_str, str):
        jds = [float(x) for x in days_str.split(",")]
    else:
        jds = [float(days_str)]
    coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
    if bjd_to_jd:
        bjd = Time(jds, format="jd", scale="tdb", location=EARTH_CENTER)
        ltt = bjd.light_travel_time(coord)
        return list((bjd - ltt).utc.jd)
    t = Time(jds, format="jd", scale="utc", location=EARTH_CENTER)
    ltt = t.light_travel_time(coord)
    return list((t.tdb + ltt).jd)


EL.convert_BJD_and_JD = local_bjd_convert

path = f"TICs/{TIC_ID}/All_{TIC_ID}_Star_Data.csv"
all_star_dataframe = pd.read_csv(path, index_col=0)
if "jd_time" in all_star_dataframe.columns:
    non_converted_times = list(all_star_dataframe["jd_time"])
    print(f"{len(non_converted_times)} frames to convert JD -> BJD")

    starting_index = 0
    total_indexes = len(non_converted_times)
    mod_length = int(total_indexes % 400)
    full_converted_times = []
    if not (total_indexes - mod_length) == 0:
        for i in range(int((total_indexes - mod_length) / 400)):
            full_converted_times += local_bjd_convert(
                str(non_converted_times[starting_index:starting_index + 400]).replace("[", "").replace("]", ""),
                RA, DEC, False)
            starting_index += 400
    if not mod_length == 0:
        full_converted_times += local_bjd_convert(
            str(non_converted_times[starting_index:]).replace("[", "").replace("]", ""), RA, DEC, False)

    all_star_dataframe = all_star_dataframe.drop("jd_time", axis=1)
    all_star_dataframe.insert(0, "time", full_converted_times)
    all_star_dataframe.to_csv(path)
    print(f"BJD conversion done, saved back to {path}")
else:
    print("BJD conversion already done (found 'time' column) -- skipping straight to plotting")

# Now the plotting stage -- Plotting.py has its own (separately broken)
# get_TOI_info/convert_BJD_and_JD; patch both with our own known ephemeris
# (period_refined/t0_refined/fit from results.jsonl, same joint GP+batman
# fit used throughout this whole vetting project)
import Plotting as PL


def local_get_TOI_info(name_identifier):
    return {"ra": str(RA), "dec": str(DEC), "period": 3.17531762905,
            "period_uncertainty": 1e-4, "depth": 5643.91492900665,
            "epoch": 2460032.2663293323, "epoch_uncertainty": 1e-3,
            "duration": 3.7452925003737025, "Tmag": 13.1}


def local_bjd_convert_plotting(days_str, toi_info, bjd_to_jd):
    # Plotting.py's own convert_BJD_and_JD returns a bare (string-able) scalar,
    # not a list like Extracting_Lightcurves.py's version -- match that here
    return local_bjd_convert(days_str, float(toi_info["ra"]), float(toi_info["dec"]), bjd_to_jd)[0]


PL.get_TOI_info = local_get_TOI_info
PL.convert_BJD_and_JD = local_bjd_convert_plotting

from Plotting import setup as get_plots
get_plots(TIC_ID, True, signal_tic_ID=400084343, is_showing_index=True, is_saving=True,
          is_plotting_MAD_vs_MAG=True, is_done=True)
print("PLOTTING_DONE")
