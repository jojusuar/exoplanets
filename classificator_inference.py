import joblib
import pandas as pd
import keras
from sklearn.discriminant_analysis import StandardScaler
import numpy as np

filename = 'TOI_2025.10.03_22.05.45.csv'

df = pd.read_csv(filename, comment='#')
cols_to_drop = [
    "rowid",'tfopwg_disp', "toi", "toipfx", "tid", "ctoi_alias", "pl_pnum",
    "rastr", "raerr1", "raerr2", "decstr", "dec", "decerr1", "decerr2",
    "st_pmralim", "st_pmrasymerr",
    "st_pmdeclim", "st_pmdecsymerr",
    "pl_tranmidlim", "pl_tranmidsymerr",
    "pl_orbperlim", "pl_orbpersymerr",
    "pl_trandurhlim", "pl_trandurhsymerr",
    "pl_trandeplim", "pl_trandepsymerr",
    "pl_radelim", "pl_radesymerr",
    "pl_insolerr1", "pl_insolerr2", "pl_insollim", "pl_insolsymerr",
    "pl_eqterr1", "pl_eqterr2", "pl_eqtlim", "pl_eqtsymerr",
    "st_tmaglim", "st_tmagsymerr",
    "st_distlim", "st_distsymerr",
    "st_tefflim", "st_teffsymerr",
    "st_logglim", "st_loggsymerr",
    "st_radlim", "st_radsymerr",
    "toi_created", "rowupdate"
]
df_clean = df.drop(columns=cols_to_drop).reset_index(drop=True)

Y = df['tfopwg_disp'].map({'FP': 0, 'FA': 0, 'CP': 1, 'KP': 1})
X = df.drop(columns=cols_to_drop)
X_filled = X.fillna(0)
X_encoded = pd.get_dummies(X_filled, drop_first=False).astype(np.float32)

mask = Y.isna()
X_encoded = X_encoded[mask]

scaler = joblib.load('scaler.pkl')
X_scaled = scaler.transform(X_encoded).astype(np.float32)

labels = ['FALSE POSITIVE', 'CONFIRMED']
model = keras.models.load_model('tess.keras')
pred_org = model.predict(X_scaled)
pred = (pred_org >= 0.5).astype(int).flatten()

candidates_meta = df.loc[mask, ['toi']]

with open('results.csv', 'w') as f:
    f.write('toi,tfopwg_disp_pred,tfopwg_disp_pred_value\n')
    for i, (_, row) in enumerate(candidates_meta.iterrows()):
        f.write(f"{row['toi']},{labels[pred[i]]},{pred_org[i][0]}\n")
