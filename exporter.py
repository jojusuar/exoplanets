import pandas as pd

# Load the CSV
filename = "cumulative_2025.10.01_20.20.34.csv"
df = pd.read_csv(filename, comment="#")

# Keep only candidates
df_candidates = df[df["koi_disposition"] == "CANDIDATE"]

# Open SSC file for writing
with open("koi_candidates.ssc", "w") as f:
    for idx, row in df_candidates.iterrows():

        # Create planet orbiting that star
        planet_name = row["kepoi_name"]
        radius_km = row["koi_prad"] * 6378  # Earth radii -> km
        f.write(f'"{planet_name}" "Sol"\n')
        f.write('{\n')
        f.write('    Class "Planet"\n')
        f.write('    Texture "neptune.jpg"\n')
        f.write(f'    Radius {radius_km:.2f}\n')

        # Include orbit if data is available
        if pd.notna(row["koi_sma"]) and pd.notna(row["koi_period"]):
            f.write('    EllipticalOrbit\n')
            f.write('    {\n')
            f.write(f'        Period {row["koi_period"]:.6f}\n')
            f.write(f'        SemiMajorAxis {row["koi_sma"]:.6f}\n')
            # Optional: include eccentricity and inclination if available
            if pd.notna(row["koi_eccen"]):
                f.write(f'        Eccentricity {row["koi_eccen"]:.6f}\n')
            if pd.notna(row["koi_incl"]):
                f.write(f'        Inclination {row["koi_incl"]:.6f}\n')
            f.write('    }\n')

        f.write('}\n\n')

print("SSC file 'koi_candidates.ssc' generated successfully.")
