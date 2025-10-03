import joblib
import pandas as pd
import keras
from sklearn.discriminant_analysis import StandardScaler
import numpy as np

filename = 'cumulative_2025.10.01_20.20.34.csv'

df = pd.read_csv(filename, comment='#')
cols_to_drop = [
    'rowid', 'kepid', 'kepoi_name', 'kepler_name', 'koi_vet_stat', 'koi_vet_date',
    'koi_pdisposition', 'koi_score', 'koi_fpflag_nt', 'koi_fpflag_ss', 'koi_fpflag_co', 
    'koi_fpflag_ec', 'koi_disp_prov', 'koi_comment', 'koi_eccen', 'koi_eccen_err1', 
    'koi_eccen_err2', 'koi_longp', 'koi_longp_err1', 'koi_longp_err2', 'koi_ingress', 
    'koi_ingress_err1', 'koi_ingress_err2',  'koi_sma_err1', 'koi_sma_err2', 'koi_incl_err1', 
    'koi_incl_err2', 'koi_teq_err1', 'koi_teq_err2', 'koi_limbdark_mod', 'koi_ldm_coeff4', 
    'koi_ldm_coeff3', 'koi_tce_plnt_num', 'koi_tce_delivname', 'koi_quarters', 
    'koi_bin_oedp_sig', 'koi_trans_mod', 'koi_model_dof', 'koi_model_chisq', 
    'koi_datalink_dvr', 'koi_datalink_dvs', 'koi_sage', 'koi_sage_err1', 'koi_sage_err2'
]

df = pd.read_csv('cumulative_2025.10.01_20.20.34.csv', comment='#')
df_clean = df.drop(columns=cols_to_drop).reset_index(drop=True)

Y = df_clean['koi_disposition'].map({'FALSE POSITIVE': 0, 'CONFIRMED': 1})
X = df_clean.drop(columns=['koi_disposition'])
X_filled = X.fillna(0)
X_encoded = pd.get_dummies(X_filled, drop_first=False).astype(np.float32)

mask = Y.isna()
X_encoded = X_encoded[mask]

scaler = joblib.load('scaler.pkl')
X_scaled = scaler.transform(X_encoded).astype(np.float32)

labels = ['FALSE POSITIVE', 'CONFIRMED']
model = keras.models.load_model('xd.keras')
pred = model.predict(X_scaled)
pred = (pred >= 0.5).astype(int).flatten()

candidates_meta = df.loc[mask, ['kepid', 'kepoi_name']]

with open('results.csv', 'w') as f:
    f.write('kepid,kepoi_name,koi_disposition_pred\n')
    for i, (_, row) in enumerate(candidates_meta.iterrows()):
        f.write(f"{row['kepid']},{row['kepoi_name']},{labels[pred[i]]}\n")
