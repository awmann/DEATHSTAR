# DEATHSTAR
## **D**etecting and **E**valuating **A** **T**ransit: finding its **H**idden **S**ource in **T**ime-domain **A**rchival **R**ecords
### A system for confirming planets and identifying false positive signals in TESS data using ground-based time domain surveys

![](README_Assets/DEATHSTAR_gif.gif)

### Created by: **Gabrielle Ross**
### Last updated: **2/19/2024**

Please see this **Google Doc** for the most up-to-date documentation: **[https://docs.google.com/document/d/1XhSLHx4Errv8sN3Wgqgwl7IM7kJosu0pbtIqBg6fUhQ/edit](https://docs.google.com/document/d/1XhSLHx4Errv8sN3Wgqgwl7IM7kJosu0pbtIqBg6fUhQ/edit)**

Please **cite our paper** if you use this code: **[https://ui.adsabs.harvard.edu/abs/2023MNRAS.tmp.3722R/abstract](https://ui.adsabs.harvard.edu/abs/2023MNRAS.tmp.3722R/abstract)**

For more information, watch the **MIT TESS Science Talk (2/28/2024)** presentation on how to install: **[https://drive.google.com/file/d/1wbOvqsq7TivGIP5u1Gy6pFxRD5siPw-C/view?usp=sharing](https://drive.google.com/file/d/1wbOvqsq7TivGIP5u1Gy6pFxRD5siPw-C/view?usp=sharing)**


---

## This fork (awmann/DEATHSTAR)

This is an internally maintained fork of [GGgabbs/DEATHSTAR](https://github.com/GGgabbs/DEATHSTAR) (`upstream` remote), kept because the published southern-declination (ATLAS) path did not run as-is. Everything below is on top of the original pipeline described in the rest of this README; see `git log` for full commit messages, each of which documents the bug, root cause, and verification for that change.

**Fixed:**
- The ATLAS/southern-declination pipeline (dec < -28°) was non-functional as published: crashes in `get_TOI_info`, a dead OSU time-conversion dependency, `matplotlib` blocking on GUI windows, and `plot_MAD_vs_MAG`'s ATLAS branch computing a figure and never saving it.
- A silent process kill (no traceback) on some ATLAS frames, caused by a diverged 2D-Gaussian centroid fit sizing a massively oversized photometric aperture — now caught and the frame skipped instead of crashing.
- `lcbin()` (binned light curve plot) crashed or silently produced an empty panel for ATLAS data (it was written ZTF-only).

**Added:**
- `common.py` + `manual_ephemeris` parameter (threaded through `DEATHSTAR.setup()`): run DEATHSTAR on any target with a known ra/dec/period/epoch/depth/Tmag, not just alerted ExoFOP TOIs.
- `atlas_fetch.py`: ATLAS forced-photometry image fetching (submit/poll/download), which the upstream repo never implemented — only ZTF fetching existed. Resumable, concurrency-aware batch fetching via `fetch_atlas_images_batch()`.
- `is_reference_image` (`setup()` param): skip the one FITS-dependent plot so a target can be re-plotted from its cached `All_<TIC>_Star_Data.csv` (e.g. with a different `signal_tic_ID`) after its raw FITS have been deleted to save disk space.
- `is_ephemeris_scan` (`setup()` param): phase-folds every extracted field star — not just the target — at the target's ephemeris and flags any with a significant in-transit brightness drop. Complements `is_plotting_MAD_vs_MAG`, which can miss a real, sharp, localized eclipse in an otherwise well-behaved star. See the docstring on `Plotting.ephemeris_scan()` for the false-positive caveats (a bad night's frames can make many field stars "dip" at once — that pattern means systematic, not signal).

**Operational note:** raw FITS/image data for ATLAS or ZTF pulls should never be saved under Dropbox — only under `~/DEATHSTAR/Data` (gitignored) or `/tmp`. Final products (plots, CSVs, writeups) are fine in Dropbox. This came from a real disk-space incident from Dropbox syncing large FITS downloads.

---

## How DEATHSTAR Kills Planets:

1. 


---

## Downloading DEATHSTAR:

1. **Install [Anaconda](https://www.anaconda.com/download)** on your computer as this package and its dependencies will be installed inside of a conda environment
2. DEATHSTAR is a **complete pipeline** available on **[Github](https://github.com/GGgabbs/DEATHSTAR/tree/main)**

      Go to the GitHub page and download the code as a **.zip file**
3. **Unzip DEATHSTAR** and its contents:

     Unzip and extract the files wherever your project’s code is on your computer. This means that they need to share the same directory when running your own code (or change the path)!
     You will either be able to run DEATHSTAR in **your own .py file** as shown in the example **jupyter notebook**.
4. Creating the **conda environment** and **installing dependencies**:

     Open your **Anaconda Prompt** (for Windows) or **Terminal** (for Mac). This is important because this is what has conda installed
     Type in and run `conda create -n DEATHSTAR python=3.9.15 numpy matplotlib scipy` in your Anaconda Prompt/ Terminal to create the environment
     Activate the DEATHSTAR environment using `conda activate DEATHSTAR`

     **Install dependencies** using `pip install ztfquery` and then subsequently `pip3 install pandas astropy astroquery photutils pyastronomy fpdf ipython notebook`

     If your program uses **additional dependencies**, use `pip3 install [PACKAGE NAME]` to install them
6. Logins and accounts for datasets:

     **[Zwicky Transient Facility (ZTF)](https://irsa.ipac.caltech.edu/frontpage/)** login: in order to retrieve ZTF data, you need a login on their website (you only need to input your username and password the first time you run the code)
7. Opening DEATHSTAR:

     Navigate to the DEATHSTAR project folder (wherever you have extracted it) within your anaconda prompt using `cd [FOLDER NAME]` and replace `[FOLDER NAME]` with your own directory name
     Test package installation with the download program `Test.py` using `python Test.py` OR `python3 Test.py`
   
     **Note:** If you get an error saying `there is no fpdf module`, deactivate the DEATHSTAR conda environment using `conda deactivate`, install fpdf using `pip install fpdf` (which installs in general conda base environment), then reactivate DEATHSTAR using `conda activate DEATHSTAR` and then rerun `python Test.py` OR `python3 Test.py`
   
     This will prompt you to fill in your ZTF login information you just created. Then the program will go through the full extracting and plotting process in 1 go as a complete pipeline example
     In order to view example outputs, open a new Anaconda Prompt (or normal Terminal on Mac) via navigating to the project folder using `cd [FOLDER NAME]` and then activating the DEATHSTAR conda environment using `conda activate DEATHSTAR`
   
     Open the DEATHSTAR_Example.ipynb using the following command `jupyter notebook`
   
     Go to the browser where the Jupyter notebook has opened and open the .ipynb file
   
     **Note:** Jupyter will open in the browser window that you last used!

### Now this battle station is fully operational!


---

## Planet Murder with DEATHSTAR:

1. 


---
