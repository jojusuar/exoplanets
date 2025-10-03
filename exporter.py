import pandas as pd

# Load CSV
filename = "cumulative_2025.10.01_20.20.34.csv"
df = pd.read_csv(filename, comment="#")

# Keep only candidates
df_candidates = df[df["koi_disposition"] == "CANDIDATE"]

# Track stars already written
written_stars = set()

# ---------- Generate STC file for host stars ----------
with open("koi_hosts.stc", "w") as stc_file:
    for idx, row in df_candidates.iterrows():
        star_id = int(row["kepid"])
        star_name = f'Star-{row["kepoi_name"]}'

        if star_name in written_stars:
            continue

        # Use RA/Dec from CSV
        ra = row["ra"]
        dec = row["dec"]

        # Fallback values if needed
        distance_ly = 100.0
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
with open("koi_candidates.ssc", "w") as ssc_file:
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
