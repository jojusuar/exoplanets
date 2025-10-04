import os
import subprocess
import pandas as pd
import random as rand
import numpy as np

G = 6.67430e-11  # m^3 kg^-1 s^-2
R_sun = 6.957e8  # m
M_sun = 1.989e30 # kg

def estimate_semimajor_axis(row):
    try:
        R_star = row["st_rad"] * R_sun
        g_cgs = 10 ** row["st_logg"]       # cm/s^2
        g = g_cgs / 100                     # m/s^2
        M_star = g * R_star**2 / G          # kg

        P_sec = row["pl_orbper"] * 86400   # days -> seconds

        a_m = (G * M_star * P_sec**2 / (4 * np.pi**2))**(1/3)
        a_au = a_m / 1.496e11              # meters -> AU
        return a_au
    except:
        return np.nan

# --- Config ---
tess_file = "TOI_2025.10.03_22.05.45.csv"
results_file = "results.csv"
local_extras = "extras"
os.makedirs(local_extras, exist_ok=True)
scripts_dir = os.path.join(local_extras, "Scripts")
os.makedirs(scripts_dir, exist_ok=True)

# --- Load TESS catalog ---
df = pd.read_csv(tess_file, comment="#")

# Keep only TOIs marked as CANDIDATE
df_candidates = df[df["tfopwg_disp"] == "PC"].copy()

# Convert distance from parsecs → light-years
df_candidates["distance_ly"] = df_candidates["st_dist"] * 3.26156

# --- Merge predictions ---
results = pd.read_csv(results_file)
df_candidates = df_candidates.merge(
    results[["toi", "tfopwg_disp_pred", "tfopwg_disp_pred_value"]],
    on="toi",
    how="left"
)

# --- Generate STC file for host stars ---
stars_stc_path = os.path.join(local_extras, "toi_hosts.stc")
written_stars = set()

with open(stars_stc_path, "w") as stc_file:
    for idx, row in df_candidates.iterrows():
        if pd.isna(row["pl_rade"]):
            continue
        star_id = rand.randint(10000,999999)
        star_name = f'Star-{row["toi"]}'

        if star_name in written_stars:
            continue

        ra = row["ra"]
        dec = row["dec"]
        distance_ly = row["distance_ly"]
        appmag = row["st_tmag"] if pd.notna(row["st_tmag"]) else 12
        spectral_type = "G0"  # placeholder

        stc_file.write(f'{star_id} "{star_name}" {{\n')
        stc_file.write(f'    RA {ra:.6f}\n')
        stc_file.write(f'    Dec {dec:.6f}\n')
        stc_file.write(f'    Distance {distance_ly:.2f}\n')
        stc_file.write(f'    SpectralType "{spectral_type}"\n')
        stc_file.write(f'    AppMag {appmag:.2f}\n')
        stc_file.write('}\n\n')

        written_stars.add(star_name)

print(f"STC file generated: {stars_stc_path}")

# --- Generate SSC file for planets ---
textures = [
    'GJ_504_b.jpg','HAT-P-11_b.jpg','Kepler-452_b.jpg','Proxima_Cen_b.jpg',
    'HD_189733_b.jpg','Kepler-7_b.jpg','YZ_Cet_d.jpg','Kepler-22_b.jpg',
    'OGLE-2005-BLG-390L_b.jpg','exo-class1.*','exo-class2.*','exo-class3.*',
    'exo-class4.*','exo-class5.*','venuslike.*','asteroid.*'
]

planets_ssc_path = os.path.join(local_extras, "toi_candidates.ssc")

with open(planets_ssc_path, "w") as ssc_file:
    for idx, row in df_candidates.iterrows():
        star_name = f'Star-{row["toi"]}'
        planet_name = f'TOI-{row["toi"]}'

        if pd.isna(row["pl_rade"]):
            continue

        radius_km = row["pl_rade"] * 6371.0  # Earth radii → km
        texture = rand.choice(textures)

        ssc_file.write(f'"{planet_name}" "{star_name}"\n')
        ssc_file.write('{\n')
        ssc_file.write('    Class "Planet"\n')
        ssc_file.write(f'    Radius {radius_km:.2f}\n')
        ssc_file.write(f'    Texture "{texture}"\n')

        # Orbital info if available
        if pd.notna(row["pl_orbper"]):
            ssc_file.write('    EllipticalOrbit\n')
            ssc_file.write('    {\n')
            ssc_file.write(f'        Period {row["pl_orbper"]:.6f}\n')
            ssc_file.write(f'        SemiMajorAxis {estimate_semimajor_axis(row):.6f}\n')
            ssc_file.write('    }\n')

        ssc_file.write('}\n\n')

print(f"SSC file generated: {planets_ssc_path}")

# --- Generate CEL tour script ---
cel_file_path = os.path.join(scripts_dir, "toi_candidates.cel")

with open(cel_file_path, "w") as f_cel:
    f_cel.write("{\n")  # opening brace

    for idx, row in df_candidates.iterrows():
        if pd.isna(row["pl_rade"]):
            continue
        planet_name = f'TOI-{row["toi"]}'
        star_name = f"Star-{row["toi"]}"
        distance_ly = row["distance_ly"]

        pred = str(row.get("tfopwg_disp_pred", "unknown")).upper()
        value = float(row.get("tfopwg_disp_pred_value", 0.5))

        text = f'Planet: {planet_name}\nApprox. {round(distance_ly,2)} light years away from Earth\n'
        if pred == "CONFIRMED":
            text += "Prediction: Real exoplanet\n"
            text += f'Confidence: {int(value*100)}%'
        elif pred == "FALSE POSITIVE":
            text += 'Prediction: False positive\n'
            text += f'Confidence: {int((1-value)*100)}%'
        else:
            text += "Prediction: unknown\n"

        f_cel.write(f'select {{object "{star_name}"}}\n')
        f_cel.write(f'select {{object "{planet_name}"}}\n')
        f_cel.write('goto { time 8 distance 5 }\n')
        f_cel.write('wait { duration 8 }\n')
        f_cel.write(f'print {{ text "{text}"\n')
        f_cel.write('         origin "top"\n')
        f_cel.write('         row 5\n')
        f_cel.write('         column -8\n')
        f_cel.write('         duration 8 }\n')
        f_cel.write('orbit {duration 8 rate 45 axis [0 1 0] }\n\n')

    f_cel.write("}\n")  # closing brace

print(f"CEL script generated: {cel_file_path}")

# --- Optional: Copy files to system Celestia extras ---
celestia_extras = "/usr/share/celestia/extras/"
dest_scripts_path = os.path.join(celestia_extras, "Scripts")

if os.path.isdir(celestia_extras):
    try:
        subprocess.run(["sudo", "mkdir", "-p", dest_scripts_path], check=True)
        subprocess.run(["sudo", "cp", stars_stc_path, celestia_extras], check=True)
        subprocess.run(["sudo", "cp", planets_ssc_path, celestia_extras], check=True)
        subprocess.run(f"sudo cp -r {scripts_dir}/* {dest_scripts_path}/", shell=True, check=True)
        print("Files copied to system Celestia extras (SSC/STC/CEL)")
    except subprocess.CalledProcessError as e:
        print(f"Error copying files: {e}")
else:
    print(f"Celestia extras folder not found; CEL file remains in local Scripts folder.")
