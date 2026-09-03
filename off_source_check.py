"""ATLAS-native off-source check: for each candidate, re-run Plotting with
signal_tic_ID set to a nearby field star flagged by MAD-vs-MAG as anomalously
variable, phase-folded at the SAME period/epoch as the target. Uses the
already-extracted All_<TIC>_Star_Data.csv on disk -- no FITS, no re-fetch.
Produces Target_vs_Signal_Lightcurve_<flagged>.png (side-by-side target vs.
flagged-star phase fold) and Binned_signal<flagged>.png for each."""
import json, sys, time
import numpy as np
sys.path.insert(0, ".")
from DEATHSTAR import setup

rows = json.load(open("/tmp/vela_all_targets.json"))
by_tic = {r["tic"]: r for r in rows if r["pidx"] == 0}

# tic -> list of flagged comparison-star TICs (from MAD-vs-MAG, most elevated first)
FLAGGED = {
    74377674: [74377735, 74377687, 74377625],
    184269319: [184269333, 184269352, 184269309],
    285409162: [285409217],
    191408271: [191408154, 191408395],
}

for tic, flagged_list in FLAGGED.items():
    p = by_tic[tic]
    fit = p["fit"]
    arg = np.sqrt(max((1 + fit["rp_rs"]) ** 2 - fit["b"] ** 2, 1e-6)) / max(fit["a_rs"], 1.001)
    manual_ephemeris = dict(
        ra=p["ra"], dec=p["dec"], period=p["period"],
        epoch=p["t0"] + 2457000.0, depth=fit["rp_rs"] ** 2 * 1e6,
        Tmag=p["tmag"], duration=(p["period"] / np.pi) * np.arcsin(min(arg, 1.0)) * 24.0,
    )
    for flagged in flagged_list:
        t0 = time.time()
        print(f"\n{'='*80}\nTIC{tic} vs flagged field star {flagged}\n{'='*80}")
        try:
            # is_lcbin only actually fires inside setup()'s "is_done" branch,
            # which is only reached via the is_plotting_MAD_vs_MAG recursive
            # comparison-removal loop -- so MAD-vs-MAG has to stay on here
            # even though we don't care about its own plot for this run.
            setup(tic, is_ATLAS=True, is_overwrite=False, is_lcbin=True,
                  signal_tic_ID=flagged, is_plotting_MAD_vs_MAG=True,
                  manual_ephemeris=manual_ephemeris, is_reference_image=False)
            print(f"TIC{tic} vs {flagged}: OK in {time.time()-t0:.0f}s")
        except Exception as e:
            print(f"TIC{tic} vs {flagged}: FAILED: {e}")

print("\nOFF_SOURCE_CHECK_DONE")
