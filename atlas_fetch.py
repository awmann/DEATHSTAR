"""
atlas_fetch.py
===============
The missing piece of DEATHSTAR: actually download ATLAS FITS images for a
target, into the Data/Atlas/<TIC>/ layout Extracting_Lightcurves.py expects.

DEATHSTAR's public repo has no ATLAS downloader at all -- Extracting_Lightcurves.py
just looks for pre-existing .fits files. The public forced-photometry API
(fallingstar-data.com/forcedphot/) is documented as flux-tables-only in its
human-readable API guide, but its OpenAPI schema (GET /api/schema/, not
linked from the guide page) reveals a real image-cutout path:

  1. POST /api-token-auth/          {username, password} -> token
  2. POST /queue/                   {ra, dec, mjd_min, mjd_max, use_reduced}
                                     -> forced-photometry task id
  3. poll GET /queue/{id}/          until finished=true
  4. POST /queue/{id}/requestimages/  -> queues a follow-up image-stack job
  5. poll GET /queue/{id}/          until imagerequest_finished=true
  6. GET  result_imagezip_url       -> zip of per-epoch FITS frames

use_reduced=True asks for reduced (not difference) images -- DEATHSTAR does
its own multi-star aperture photometry across the field, which needs actual
per-epoch flux levels, not sky-subtracted differences.

Auth: export ATLAS_USERNAME / ATLAS_PASSWORD, or ATLAS_TOKEN directly.
"""
import os
import io
import time
import zipfile
from pathlib import Path

import requests

BASE = "https://fallingstar-data.com/forcedphot"


def get_token(username=None, password=None):
    token = os.environ.get("ATLAS_TOKEN")
    if token:
        return token
    username = username or os.environ["ATLAS_USERNAME"]
    password = password or os.environ["ATLAS_PASSWORD"]
    r = requests.post(f"{BASE}/api-token-auth/", data={"username": username, "password": password}, timeout=30)
    r.raise_for_status()
    return r.json()["token"]


def _headers(token):
    return {"Authorization": f"Token {token}"}


def submit_task(token, ra, dec, mjd_min, mjd_max, use_reduced=True, comment=""):
    payload = {"ra": ra, "dec": dec, "mjd_min": mjd_min, "mjd_max": mjd_max,
               "use_reduced": use_reduced, "send_email": False, "comment": comment}
    r = requests.post(f"{BASE}/queue/", headers=_headers(token), data=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def poll_task(token, task_id, key="finished", timeout_s=1800, interval_s=15):
    url = f"{BASE}/queue/{task_id}/"
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        r = requests.get(url, headers=_headers(token), timeout=30)
        r.raise_for_status()
        data = r.json()
        if data.get(key):
            return data
        if data.get("error_msg"):
            raise RuntimeError(f"ATLAS task {task_id} failed: {data['error_msg']}")
        print(f"  ...waiting on task {task_id} ({key}=False, queuepos={data.get('queuepos')})")
        time.sleep(interval_s)
    raise TimeoutError(f"ATLAS task {task_id} did not reach {key}=True within {timeout_s}s")


def request_images(token, task_id):
    r = requests.post(f"{BASE}/queue/{task_id}/requestimages/", headers=_headers(token), timeout=30)
    if r.status_code not in (200, 201, 302):
        raise RuntimeError(f"requestimages failed ({r.status_code}): {r.text[:300]}")


def download_and_unzip(url, out_dir, token=None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    headers = _headers(token) if token else {}
    r = requests.get(url, headers=headers, timeout=300)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        names = zf.namelist()
        zf.extractall(out_dir)
    fits_files = [f for f in names if f.lower().endswith((".fits", ".fits.fz"))]
    print(f"  extracted {len(fits_files)} FITS file(s) to {out_dir}")
    return fits_files


def fetch_atlas_images(tic_id, ra, dec, mjd_min, mjd_max, use_reduced=True,
                        out_base="Data/Atlas", token=None):
    """Top-level: ATLAS coords+date range -> Data/Atlas/<tic_id>/*.fits,
    matching exactly what Extracting_Lightcurves.py already expects to find."""
    token = token or get_token()
    out_dir = Path(out_base) / str(tic_id)

    print(f"TIC{tic_id}: submitting forced-phot task (ra={ra:.5f} dec={dec:.5f} "
          f"mjd=[{mjd_min},{mjd_max}] use_reduced={use_reduced}) ...")
    task = submit_task(token, ra, dec, mjd_min, mjd_max, use_reduced=use_reduced,
                        comment=f"DEATHSTAR TIC{tic_id}")
    task_id = task["id"]
    print(f"  task id={task_id}, polling for forced-photometry completion...")
    task = poll_task(token, task_id, key="finished")
    print(f"  forced-photometry finished. requesting image stack...")

    request_images(token, task_id)
    task = poll_task(token, task_id, key="imagerequest_finished")

    # the zip lives on the CHILD image-request task (request_type=IMGZIP),
    # not on the parent forced-photometry task -- imagerequest_task_id points to it
    img_task_id = task.get("imagerequest_task_id")
    r = requests.get(f"{BASE}/queue/{img_task_id}/", headers=_headers(token), timeout=30)
    r.raise_for_status()
    img_task = r.json()
    zip_url = img_task.get("result_imagezip_url")
    if not zip_url:
        raise RuntimeError(f"No result_imagezip_url on finished image task {img_task_id}: {img_task}")
    print(f"  image request finished. downloading {zip_url} ...")
    fits_files = download_and_unzip(zip_url, out_dir, token=token)
    return out_dir, fits_files


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("tic_id", type=int)
    ap.add_argument("ra", type=float)
    ap.add_argument("dec", type=float)
    ap.add_argument("--mjd-min", type=float, default=58000.0)
    ap.add_argument("--mjd-max", type=float, default=61200.0)
    ap.add_argument("--difference", action="store_true", help="use difference images instead of reduced")
    args = ap.parse_args()
    fetch_atlas_images(args.tic_id, args.ra, args.dec, args.mjd_min, args.mjd_max,
                        use_reduced=not args.difference)
