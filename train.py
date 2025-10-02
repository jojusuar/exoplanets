import pandas as pd
import keras
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def build_mlp(column_count, num_classes):
    inputs = keras.Input(shape=(column_count,))
    x = keras.layers.Dense(512, activation="relu")(inputs)
    x = keras.layers.Dense(256, activation="relu")(x)
    x = keras.layers.Dense(128, activation="relu")(x)
    output = keras.layers.Dense(num_classes, activation="softmax")(x)
    return keras.Model(inputs, output)



df = pd.read_csv("cumulative_2025.10.01_20.20.34.csv", comment='#')

df = df.drop(
    columns=[
        "rowid", "kepid", "kepoi_name", "kepler_name", "koi_vet_stat", "koi_vet_date",
        "koi_pdisposition", "koi_score", "koi_fpflag_nt",
        "koi_fpflag_ss", "koi_fpflag_co", "koi_fpflag_ec",
        "koi_disp_prov", "koi_comment"
    ]
)

Y = df['koi_disposition']
Y_encoded = pd.get_dummies(Y, drop_first=False).values

X = df.drop(columns=['koi_disposition'])
X_encoded = pd.get_dummies(X, drop_first=False).values 

X_train, X_test, Y_train, Y_test = train_test_split(
    X_encoded, Y_encoded, test_size=0.2, random_state=42, shuffle=True
)

model = build_mlp(X_encoded.shape[1], Y_encoded.shape[1])

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-3),
    loss="categorical_crossentropy",
)

early_stop = keras.callbacks.EarlyStopping(
    monitor='val_loss',
    patience=50,
    restore_best_weights=True
)

model.fit(
    X_train, Y_train,
    batch_size=32,
    epochs=1000,
    validation_split=0.1,
    callbacks=[early_stop]
)

model.save('xd.keras')



# TEST
Y_pred_probs = model.predict(X_test)
Y_pred = np.argmax(Y_pred_probs, axis=1)

Y_true = np.argmax(Y_test, axis=1)
cm = confusion_matrix(Y_true, Y_pred)

print(classification_report(Y_true, Y_pred))

plt.figure(figsize=(8,6))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")
plt.show()