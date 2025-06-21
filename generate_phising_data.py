import pandas as pd
import os

# Your custom directory
output_dir = r"D:\The New Data Trio"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "phishing_dataset.csv")

# SMS Samples
data = [
    # 🚨 Phishing examples
    ("Dear user, your account has been suspended. Click here to verify: http://fakebank.com", 1),
    ("You've won a free iPhone! Claim now at http://scamurl.com", 1),
    ("URGENT: Your KYC is pending. Complete at http://kycupdates.com", 1),
    ("Your bank account is under threat. Visit http://secure-update.in to fix it", 1),
    ("Verify your PAN card immediately to avoid deactivation", 1),
    ("Congratulations, you've been selected for a cash prize. Click the link to claim.", 1),
    ("Final notice: Renew your subscription or face account suspension", 1),
    ("Your loan is approved. Send your details to us via this link", 1),
    ("Security alert: Suspicious login detected. Confirm at http://login-fraud.com", 1),
    ("Pay ₹100 to avoid service disruption. Use this UPI link", 1),

    # ✅ Legit (ham) examples
    ("Your OTP for transaction at Amazon is 123456. Do not share with anyone.", 0),
    ("Hi, are we still on for lunch tomorrow?", 0),
    ("Your electricity bill has been paid. Thank you!", 0),
    ("Get 20% off on your next order using code SAVE20", 0),
    ("Call me when you're free.", 0),
    ("Your Uber is arriving now. Driver: Rajesh, Car: Swift, Number: TN09 3210", 0),
    ("Axis Bank: ₹5000 debited from your account ending 1234", 0),
    ("Meeting rescheduled to 3PM. Let me know if that works.", 0),
    ("Parcel shipped. Track your order at Flipkart", 0),
    ("Recharge successful. Enjoy your Jio data pack", 0),
]

# Save as CSV
df = pd.DataFrame(data, columns=["text", "label"])
df.to_csv(output_path, index=False)

print(f"✅ Dataset saved at: {output_path}")
