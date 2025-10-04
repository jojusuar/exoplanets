import os
import shutil
import subprocess
import numpy as np
import pandas as pd

# Load CSV
filename = "cumulative_2025.10.01_20.20.34.csv"
df = pd.read_csv(filename, comment="#")

R_sun = 6.957e8  # meters
L_sun = 3.828e26  # watts
sigma = 5.670374419e-8

distances_ly = []
df_candidates = df[df["koi_disposition"] == "CANDIDATE"].copy()

for idx, row in df_candidates.iterrows():
    try:
        R = row["koi_srad"] * R_sun
        T = row["koi_steff"]
        m = row["koi_kepmag"]

        # Compute luminosity
        L = 4 * np.pi * R**2 * sigma * T**4

        # Absolute magnitude
        M = 4.74 - 2.5 * np.log10(L / L_sun)

        # Distance in parsecs
        d_pc = 10 ** ((m - M + 5) / 5)

        # Convert to light-years
        d_ly = d_pc * 3.26156
        distances_ly.append(d_ly)
    except:
        distances_ly.append(100)  # fallback

df_candidates["distance_ly"] = distances_ly

# Track stars already written
written_stars = set()

local_extras = "extras"
os.makedirs(local_extras, exist_ok=True)

# ---------- Generate STC file for host stars ----------
stars_stc_path = "extras/koi_hosts.stc"
with open(stars_stc_path, "w") as stc_file:
    for idx, row in df_candidates.iterrows():
        star_id = int(row["kepid"])
        star_name = f'Star-{row["kepoi_name"]}'

        if star_name in written_stars:
            continue

        # Use RA/Dec from CSV
        ra = row["ra"]
        dec = row["dec"]

        # Fallback values if needed
        distance_ly = row['distance_ly']
        spectral_type = "G0"
        appmag = 12

        stc_file.write(f'{star_id} "{star_name}" {{\n')
        stc_file.write(f'    RA {ra:.6f}\n')
        stc_file.write(f'    Dec {dec:.6f}\n')
        stc_file.write(f'    Distance {distance_ly}\n')
        stc_file.write(f'    SpectralType "{spectral_type}"\n')
        stc_file.write(f'    AppMag {appmag}\n')
        stc_file.write('}\n\n')

        written_stars.add(star_name)

print("STC file 'koi_hosts.stc' generated successfully.")

# ---------- Generate SSC file for planets ----------
planets_ssc_path = "extras/koi_candidates.ssc"
with open(planets_ssc_path, "w") as ssc_file:
    for idx, row in df_candidates.iterrows():
        star_name = f'Star-{row["kepoi_name"]}'
        planet_name = row["kepoi_name"]
        radius_km = row["koi_prad"] * 6378  # convert Earth radii -> km

        ssc_file.write(f'"{planet_name}" "{star_name}"\n')
        ssc_file.write('{\n')
        ssc_file.write('    Class "Planet"\n')
        ssc_file.write(f'    Radius {radius_km:.2f}\n')
        ssc_file.write('    Texture "neptune.jpg"\n')

        # Include orbit if SMA and period are available
        if pd.notna(row["koi_sma"]) and pd.notna(row["koi_period"]):
            ssc_file.write('    EllipticalOrbit\n')
            ssc_file.write('    {\n')
            ssc_file.write(f'        Period {row["koi_period"]:.6f}\n')
            ssc_file.write(f'        SemiMajorAxis {row["koi_sma"]:.6f}\n')
            if pd.notna(row["koi_eccen"]):
                ssc_file.write(f'        Eccentricity {row["koi_eccen"]:.6f}\n')
            if pd.notna(row["koi_incl"]):
                ssc_file.write(f'        Inclination {row["koi_incl"]:.6f}\n')
            ssc_file.write('    }\n')

        ssc_file.write('}\n\n')

print("SSC file 'koi_candidates.ssc' generated successfully.")

results = pd.read_csv("results.csv")

# Merge predictions into candidates dataframe using kepoi_name as key
df_candidates = df_candidates.merge(
    results[["kepoi_name", "koi_disposition_pred", "koi_disposition_pred_value"]],
    on="kepoi_name",
    how="left"
)

# --- Local Scripts folder ---
scripts_dir = os.path.join(local_extras, "Scripts")
os.makedirs(scripts_dir, exist_ok=True)

cel_file_path = os.path.join(scripts_dir, "koi_candidates.cel")

with open(cel_file_path, "w") as f_cel:
    f_cel.write("{\n")  # opening brace for the whole tour

    for idx, row in df_candidates.iterrows():
        planet_name = row["kepoi_name"]
        distance_ly = row['distance_ly']
        star_name = f"Star-{planet_name}"

        # Get prediction text
        pred = str(row.get("koi_disposition_pred", "unknown"))
        value = float(row.get("koi_disposition_pred_value"))
        text = f'Planet: {planet_name}\nApprox. {round(distance_ly, 2)} light years away\n'
        if pred == "CONFIRMED":
            text += "Prediction: Real exoplanet\n"
            text += f'Confidence: {int(value * 100)}%'
        elif pred == "FALSE POSITIVE":
            text += 'Prediction: False positive\n'
            text += f'Confidence: {int( (1 - value) * 100)}%'

        else:
            text += "Prediction: unknown\n"
        
        f_cel.write(f'select {{object "{star_name}"}}\n')
        f_cel.write(f'select {{object "{planet_name}"}}\n')
        f_cel.write('goto { time 8 distance 5 }\n')
        f_cel.write('wait { duration 8 }\n')
        f_cel.write(f'print  {{ text "{text}"\n')
        f_cel.write('         origin "top"\n')
        f_cel.write('         row 5\n')
        f_cel.write('         column -8\n')
        f_cel.write('         duration 8 }\n')
        f_cel.write('orbit {duration 8 rate 45 axis [0 1 0] }\n\n')

    f_cel.write("}\n")  # closing brace

print(f"CEL file created at '{cel_file_path}'")

# --- System Celestia extras ---
celestia_extras = "/usr/share/celestia/extras/"
dest_scripts_path = os.path.join(celestia_extras, "Scripts")

if os.path.isdir(celestia_extras):
    try:
        # Ensure Scripts folder exists in system extras
        subprocess.run(["sudo", "mkdir", "-p", dest_scripts_path], check=True)

        # Copy SSC and STC files
        subprocess.run(["sudo", "cp", stars_stc_path, celestia_extras], check=True)
        subprocess.run(["sudo", "cp", planets_ssc_path, celestia_extras], check=True)

        # Copy all contents of local Scripts folder to system Scripts folder
        subprocess.run(f"sudo cp -r {scripts_dir}/* {dest_scripts_path}/", shell=True, check=True)

        print(f"Files copied to '{celestia_extras}' (SSC/STC) and Scripts (CEL) using sudo")
    except subprocess.CalledProcessError as e:
        print(f"Error copying files: {e}")
else:
    print(f"Celestia extras folder not found at '{celestia_extras}'. CEL file is in local 'Scripts' folder.")