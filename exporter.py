import os
import subprocess
import pandas as pd
import random as rand
import numpy as np

G = 6.67430e-11  # m^3 kg^-1 s^-2
R_sun = 6.957e8  # m
M_sun = 1.989e30 # kg
L_sun = 3.828e26  # watts
sigma = 5.670374419e-8

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
    
def estimate_distance(row):
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
        return d_ly
    except:
        return 100

def generate_star(star_id, star_name, ra, dec, distance_ly, appmag, spectral_type):
    entry = ''
    entry += f'{star_id} "{star_name}" {{\n'
    entry += f'    RA {ra:.6f}\n'
    entry += f'    Dec {dec:.6f}\n'
    entry += f'    Distance {distance_ly:.2f}\n'
    entry += f'    SpectralType "{spectral_type}"\n'
    entry += f'    AppMag {appmag:.2f}\n'
    entry += '}\n\n'
    return entry

textures = [
    'GJ_504_b.jpg','HAT-P-11_b.jpg','Kepler-452_b.jpg','Proxima_Cen_b.jpg',
    'HD_189733_b.jpg','Kepler-7_b.jpg','YZ_Cet_d.jpg','Kepler-22_b.jpg',
    'OGLE-2005-BLG-390L_b.jpg','exo-class1.*','exo-class2.*','exo-class3.*',
    'exo-class4.*','exo-class5.*','venuslike.*','asteroid.*'
]

def generate_planet(star_name, planet_name, radius_km, period, semimajoraxis, eccentricity, inclination):
    entry = ''
    texture = rand.choice(textures)
    entry += f'"{planet_name}" "{star_name}"\n'
    entry += '{\n'
    entry += '    Class "Planet"\n'
    entry += f'    Radius {radius_km:.2f}\n'
    entry += f'    Texture "{texture}"\n'
    entry += '    EllipticalOrbit\n'
    entry += '    {\n'
    entry += f'        Period {period:.6f}\n'
    entry += f'        SemiMajorAxis {semimajoraxis:.6f}\n'
    entry += f'        Eccentricity {eccentricity:.6f}\n'
    entry += f'        Inclination {inclination:.6f}\n'
    entry += '    }\n'
    entry += '}\n\n'
    return entry

def generate_script_entry(planet_name, star_name, distance_ly, pred, value):
    text = f'Planet: {planet_name}\nApprox. {round(distance_ly,2)} light years away from Earth\n'
    if pred == "CONFIRMED":
        text += "Prediction: Real exoplanet\n"
        text += f'Confidence: {int(value*100)}%'
    elif pred == "FALSE POSITIVE":
        text += 'Prediction: False positive\n'
        text += f'Confidence: {int((1-value)*100)}%'
    else:
        text += "Prediction: unknown\n"
    entry = ''
    entry += f'select {{object "{star_name}"}}\n'
    entry += f'select {{object "{planet_name}"}}\n'
    entry += 'goto { time 8 distance 5 }\n'
    entry += 'wait { duration 8 }\n'
    entry += f'print {{ text "{text}"\n'
    entry += '         origin "top"\n'
    entry += '         row 5\n'
    entry += '         column -8\n'
    entry += '         duration 8 }\n'
    entry += 'orbit {duration 8 rate 45 axis [0 1 0] }\n\n'
    return entry


# --- Config ---
tess_file = "tess_db.csv"
tess_predictions_file = "tess_predictions.csv"
kepler_file = "kepler_db.csv"
kepler_predictions_file = "kepler_predictions.csv"
local_extras = "extras"
os.makedirs(local_extras, exist_ok=True)
scripts_dir = os.path.join(local_extras, "Scripts")
os.makedirs(scripts_dir, exist_ok=True)

# --- Load TESS catalog ---
df_tess = pd.read_csv(tess_file, comment="#")
df_tess_candidates = df_tess[df_tess["tfopwg_disp"] == "PC"].copy()
df_tess_candidates["distance_ly"] = df_tess_candidates["st_dist"] * 3.26156
tess_predictions = pd.read_csv(tess_predictions_file)
df_tess_candidates = df_tess_candidates.merge(
    tess_predictions[["toi", "tfopwg_disp_pred", "tfopwg_disp_pred_value"]],
    on="toi",
    how="left"
)

# --- Load Kepler catalog ---
df_kepler = pd.read_csv(kepler_file, comment="#")
df_kepler_candidates = df_kepler[df_kepler["koi_disposition"] == "CANDIDATE"].copy()
kepler_predictions = pd.read_csv(kepler_predictions_file)
df_kepler_candidates = df_kepler_candidates.merge(
    kepler_predictions[["kepid", "koi_disposition_pred", "koi_disposition_pred_value"]],
    on="kepid",
    how="left"
)
distances_ly = []
for idx, row in df_kepler_candidates.iterrows():
    distances_ly.append(estimate_distance(row))
df_kepler_candidates["distance_ly"] = distances_ly


# --- Generate STC file for host stars ---
tess_stars_stc_path = os.path.join(local_extras, "toi_hosts.stc")
kepler_stars_stc_path = os.path.join(local_extras, "koi_hosts.stc")

with open(tess_stars_stc_path, "w") as stc_file:
    for idx, row in df_tess_candidates.iterrows():
        if pd.isna(row["pl_rade"]):
            continue
        entry = generate_star(
                            star_id=rand.randint(10000,999999),
                            star_name=f'Star-{row["toi"]}',
                            ra=row["ra"],
                            dec=row["dec"],
                            distance_ly=row["distance_ly"],
                            appmag=row["st_tmag"] if pd.notna(row["st_tmag"]) else 12,
                            spectral_type="G0"
                            )
        stc_file.write(entry)


with open(kepler_stars_stc_path, "w") as stc_file:
    for idx, row in df_kepler_candidates.iterrows():
        entry = generate_star(
                            star_id=int(row["kepid"]),
                            star_name=f'Star-{row["kepoi_name"]}',
                            ra=row["ra"],
                            dec=row["dec"],
                            distance_ly=row['distance_ly'],
                            appmag=12,
                            spectral_type="G0"
                            )
        stc_file.write(entry)

print(f"STC file generated: {kepler_stars_stc_path}")

# --- Generate SSC file for planets ---
tess_planets_ssc_path = os.path.join(local_extras, "toi_candidates.ssc")
kepler_planets_ssc_path = os.path.join(local_extras, "koi_candidates.ssc")

with open(tess_planets_ssc_path, "w") as ssc_file:
    for idx, row in df_tess_candidates.iterrows():
        if pd.isna(row["pl_rade"]):
            continue
        radius_km = row["pl_rade"] * 6378  # Earth radii to km
        entry = generate_planet(star_name=f'Star-{row["toi"]}',
                                planet_name=f'TOI-{row["toi"]}',
                                radius_km=radius_km,
                                period=row["pl_orbper"],
                                semimajoraxis=estimate_semimajor_axis(row),
                                eccentricity=0,
                                inclination=0)
        ssc_file.write(entry)

print(f"SSC file generated: {tess_planets_ssc_path}")

with open(kepler_planets_ssc_path, "w") as ssc_file:
    for idx, row in df_kepler_candidates.iterrows():
        radius_km = row["koi_prad"] * 6378
        entry = generate_planet(star_name=f'Star-{row["kepoi_name"]}',
                                planet_name=f'{row["kepoi_name"]}',
                                radius_km=radius_km,
                                period=row["koi_period"],
                                semimajoraxis=row["koi_sma"],
                                eccentricity=row["koi_eccen"],
                                inclination=row["koi_incl"])
        ssc_file.write(entry)

print(f"SSC file generated: {kepler_planets_ssc_path}")

# --- Generate CEL tour script ---
tess_cel_file_path = os.path.join(scripts_dir, "toi_candidates.cel")
kepler_cel_file_path = os.path.join(scripts_dir, "koi_candidates.cel")

with open(tess_cel_file_path, "w") as f_cel:
    f_cel.write("{\n")  # opening brace
    for idx, row in df_tess_candidates.iterrows():
        if pd.isna(row["pl_rade"]):
            continue
        entry = generate_script_entry(
                                    planet_name=f'TOI-{row["toi"]}',
                                    star_name=f"Star-{row["toi"]}",
                                    distance_ly = row["distance_ly"],
                                    pred=str(row.get("tfopwg_disp_pred", "unknown")).upper(),
                                    value=float(row.get("tfopwg_disp_pred_value", 0.5))
                                    )
        f_cel.write(entry)
    f_cel.write("}\n")  # closing brace

print(f"CEL script generated: {tess_cel_file_path}")

with open(kepler_cel_file_path, "w") as f_cel:
    f_cel.write("{\n")  # opening brace
    for idx, row in df_kepler_candidates.iterrows():
        entry = generate_script_entry(
                                    planet_name=row["kepoi_name"],
                                    star_name=f"Star-{row["kepoi_name"]}",
                                    distance_ly = row["distance_ly"],
                                    pred=str(row.get("koi_disposition_pred", "unknown")),
                                    value=float(row.get("koi_disposition_pred_value"))
                                    )
        f_cel.write(entry)
    f_cel.write("}\n")  # closing brace

print(f"CEL script generated: {kepler_cel_file_path}")


# --- Optional: Copy files to system Celestia extras ---
celestia_extras = "/usr/share/celestia/extras/"
dest_scripts_path = os.path.join(celestia_extras, "Scripts")

if os.path.isdir(celestia_extras):
    try:
        subprocess.run(["sudo", "mkdir", "-p", dest_scripts_path], check=True)
        subprocess.run(["sudo", "cp", tess_stars_stc_path, celestia_extras], check=True)
        subprocess.run(["sudo", "cp", tess_planets_ssc_path, celestia_extras], check=True)
        subprocess.run(["sudo", "cp", kepler_stars_stc_path, celestia_extras], check=True)
        subprocess.run(["sudo", "cp", kepler_planets_ssc_path, celestia_extras], check=True)
        subprocess.run(f"sudo cp -r {scripts_dir}/* {dest_scripts_path}/", shell=True, check=True)
        print("Files copied to system Celestia extras (SSC/STC/CEL)")
    except subprocess.CalledProcessError as e:
        print(f"Error copying files: {e}")
else:
    print(f"Celestia extras folder not found; CEL file remains in local Scripts folder.")
