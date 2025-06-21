import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, roc_curve, auc, precision_recall_curve
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json

# ========================
# Configuration
# ========================
DATA_PATH = r"D:\The New Data Trio\fraud_dataset.csv"
BASE_DIR = r"D:\The New Data Trio"
MODEL_PATH = os.path.join(BASE_DIR, "fraud_autoencoder.pt")
SCALER_MEAN_PATH = os.path.join(BASE_DIR, "scaler_mean.npy")
SCALER_STD_PATH = os.path.join(BASE_DIR, "scaler_std.npy")
PLOT_DIR = os.path.join(BASE_DIR, "plots")
METRICS_PATH = os.path.join(BASE_DIR, "fraud_metrics.json")

# Create directories if needed
os.makedirs(PLOT_DIR, exist_ok=True)

# Set plotting style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'

# ========================
# Data Preparation
# ========================
def load_and_preprocess_data():
    """Load and preprocess transaction data"""
    df = pd.read_csv(DATA_PATH)
    
    # Extract hour from time
    df["hour"] = df["time"].apply(lambda t: 
        (lambda x: x[0] + x[1]/60.0 if len(x)==2 else np.nan)
        (list(map(int, t.split(":")))))
    
    # Filter and convert
    df = df[["amount", "hour"]].dropna().astype(np.float32)
    
    # Add synthetic fraud labels for evaluation (10% fraud rate)
    np.random.seed(42)
    df['is_fraud'] = np.random.choice([0, 1], size=len(df), p=[0.9, 0.1])
    
    return df

# ========================
# Model Definition
# ========================
class FraudAutoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(2, 8),
            nn.ReLU(),
            nn.Linear(8, 4),
            nn.ReLU(),
            nn.Linear(4, 2)
        )
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(2, 4),
            nn.ReLU(),
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, 2)
        )

    def forward(self, x):
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed, latent

# ========================
# Training & Evaluation
# ========================
def train_and_evaluate():
    """Train autoencoder and generate evaluation metrics"""
    # Load and prepare data
    df = load_and_preprocess_data()
    X = df[['amount', 'hour']].values
    y = df['is_fraud'].values  # Synthetic fraud labels
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    inputs = torch.tensor(X_scaled, dtype=torch.float32)
    
    # Initialize model
    model = FraudAutoencoder()
    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)
    criterion = nn.MSELoss()
    
    # Training loop
    train_losses = []
    for epoch in range(200):
        model.train()
        optimizer.zero_grad()
        reconstructed, _ = model(inputs)
        loss = criterion(reconstructed, inputs)
        loss.backward()
        optimizer.step()
        train_losses.append(loss.item())
        
        if epoch % 20 == 0:
            print(f"Epoch {epoch:3d} | Loss: {loss.item():.6f}")
    
    # Save model and scaler
    torch.save(model.state_dict(), MODEL_PATH)
    np.save(SCALER_MEAN_PATH, scaler.mean_)
    np.save(SCALER_STD_PATH, scaler.scale_)
    
    # ========================
    # Generate Paper-Ready Metrics
    # ========================
    model.eval()
    with torch.no_grad():
        reconstructed, latent = model(inputs)
        reconstruction = reconstructed.numpy()
        latent = latent.numpy()
    
    # Reconstruction errors
    recon_errors = np.mean((X_scaled - reconstruction) ** 2, axis=1)
    mse = mean_squared_error(X_scaled, reconstruction)
    
    # ROC/AUC metrics (using reconstruction error as fraud score)
    fpr, tpr, _ = roc_curve(y, recon_errors)
    roc_auc = auc(fpr, tpr)
    
    # Precision-Recall curve
    precision, recall, _ = precision_recall_curve(y, recon_errors)
    pr_auc = auc(recall, precision)
    
    # Save metrics
    metrics = {
        "final_train_loss": train_losses[-1],
        "reconstruction_mse": float(mse),
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "fraud_detection_threshold": float(np.percentile(recon_errors, 95))
    }
    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # ========================
    # Generate Visualizations
    # ========================
    # 1. Training Loss Curve
    plt.figure(figsize=(8, 5))
    plt.plot(train_losses, 'b-', lw=1.5)
    plt.title("Autoencoder Training Loss")
    plt.xlabel("Epoch")
    plt.ylabel("MSE Loss")
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(PLOT_DIR, "training_loss.png"))
    plt.close()
    
    # 2. Reconstruction Error Distribution
    plt.figure(figsize=(8, 5))
    plt.hist(recon_errors, bins=50, color='skyblue', edgecolor='black', alpha=0.8)
    plt.axvline(metrics["fraud_detection_threshold"], color='r', linestyle='--', 
                label=f'95th Percentile: {metrics["fraud_detection_threshold"]:.2f}')
    plt.title("Reconstruction Error Distribution")
    plt.xlabel("Mean Squared Error (MSE)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(PLOT_DIR, "reconstruction_error_dist.png"))
    plt.close()
    
    # 3. ROC Curve
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, 
             label=f'ROC Curve (AUC = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=1, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve - Fraud Detection')
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(PLOT_DIR, "roc_curve.png"))
    plt.close()
    
    # 4. Precision-Recall Curve
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, color='blue', lw=2, 
             label=f'PR Curve (AUC = {pr_auc:.2f})')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve - Fraud Detection')
    plt.legend(loc="upper right")
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(PLOT_DIR, "precision_recall_curve.png"))
    plt.close()
    
    # 5. Latent Space Visualization
    plt.figure(figsize=(8, 6))
    plt.scatter(latent[:, 0], latent[:, 1], c=y, cmap='coolwarm', 
                alpha=0.6, edgecolors='w', s=30)
    plt.colorbar(label='Fraud (1=Fraud)')
    plt.title('Latent Space Representation')
    plt.xlabel('Latent Dimension 1')
    plt.ylabel('Latent Dimension 2')
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(PLOT_DIR, "latent_space.png"))
    plt.close()
    
    print(f"\n✅ Training complete! Metrics and plots saved to:\n{PLOT_DIR}")
    print(f"Key Metrics:\n- Final Loss: {metrics['final_train_loss']:.4f}\n"
          f"- Reconstruction MSE: {metrics['reconstruction_mse']:.4f}\n"
          f"- ROC AUC: {metrics['roc_auc']:.4f}\n"
          f"- PR AUC: {metrics['pr_auc']:.4f}")

# ========================
# Main Execution
# ========================
if __name__ == "__main__":
    train_and_evaluate()
