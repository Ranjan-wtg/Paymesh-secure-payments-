import torch
import torch.nn as nn
import numpy as np
import os

# 🔧 File paths
BASE_DIR = r"D:\The New Data Trio"
MODEL_PATH = os.path.join(BASE_DIR, "fraud_autoencoder.pt")
SCALER_MEAN_PATH = os.path.join(BASE_DIR, "scaler_mean.npy")
SCALER_STD_PATH = os.path.join(BASE_DIR, "scaler_std.npy")

# ✅ Autoencoder architecture (must match training)
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

# ✅ Load model + scaler
def load_model_and_scaler():
    model = TxnAutoencoder()
    model.load_state_dict(torch.load(MODEL_PATH))
    model.eval()

    scaler_mean = np.load(SCALER_MEAN_PATH)
    scaler_std = np.load(SCALER_STD_PATH)

    return model, scaler_mean, scaler_std

# ✅ Main scoring function
def is_fraudulent(txn):
    """
    txn = {
        "amount": 16000,
        "time": "01:30"
    }
    Returns:
        {
            "fraud_score": float,
            "is_fraud": bool
        }
    """
    try:
        model, mean, std = load_model_and_scaler()
        hour = int(txn["time"].split(":")[0]) + int(txn["time"].split(":")[1]) / 60
        input_arr = np.array([txn["amount"], hour], dtype=np.float32)
        norm_input = (input_arr - mean) / std
        x = torch.tensor(norm_input, dtype=torch.float32).unsqueeze(0)
        recon = model(x)
        loss = torch.nn.functional.mse_loss(recon, x)
        score = float(loss.item())

        return {
            "fraud_score": round(score, 5),
            "is_fraud": score > 0.15  # ⚠️ Tune this threshold as needed
        }
    except Exception as e:
        return {"error": str(e)}

# ✅ Quick test
if __name__ == "__main__":
    test_txn = {"amount": 17000, "time": "00:30"}
    result = is_fraudulent(test_txn)
    print("🚨 Fraud Detection Result:")