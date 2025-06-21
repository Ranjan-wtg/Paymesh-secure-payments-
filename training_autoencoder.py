import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
import os

# 📂 Your dataset
DATA_PATH = r"D:\The New Data Trio\fraud_dataset.csv"
BASE_DIR = r"D:\The New Data Trio"
MODEL_PATH = os.path.join(BASE_DIR, "fraud_autoencoder.pt")
SCALER_MEAN_PATH = os.path.join(BASE_DIR, "scaler_mean.npy")
SCALER_STD_PATH = os.path.join(BASE_DIR, "scaler_std.npy")

# ✅ Load dataset (expects 'amount' and 'time' columns)
df = pd.read_csv(DATA_PATH)

# Extract hour as float
def extract_hour(t):
    try:
        h, m = map(int, t.split(":"))
        return h + m / 60.0
    except:
        return np.nan

df["hour"] = df["time"].apply(extract_hour)
df = df[["amount", "hour"]].dropna().astype(np.float32)

# ✅ Autoencoder definition
class TxnAutoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(2, 4),
            nn.ReLU(),
            nn.Linear(4, 2)
        )
        self.decoder = nn.Sequential(
            nn.Linear(2, 4),
            nn.ReLU(),
            nn.Linear(4, 2)
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))

# ✅ Train the autoencoder
def train_autoencoder(df):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df.values)
    inputs = torch.tensor(X_scaled, dtype=torch.float32)

    model = TxnAutoencoder()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.MSELoss()

    for epoch in range(100):
        outputs = model(inputs)
        loss = criterion(outputs, inputs)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        if epoch % 10 == 0:
            print(f"Epoch {epoch}: Loss = {loss.item():.4f}")

    # Save model + scaler
    torch.save(model.state_dict(), MODEL_PATH)
    np.save(SCALER_MEAN_PATH, scaler.mean_)
    np.save(SCALER_STD_PATH, scaler.scale_)

    print("\n✅ Model and scaler saved!")

# 🔁 Run training
if __name__ == "__main__":
    train_autoencoder(df)
