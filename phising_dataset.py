import pandas as pd
import random
import os

random.seed(42)

# ✅ Phishing SMS templates
phishing_templates = [
    "Dear customer, your account has been suspended. Verify now: http://scamurl.com",
    "URGENT: KYC update required. Click: http://kyc-fraud.in",
    "Claim your ₹{amt} reward here: http://fake-rewards.com",
    "Payment failed. Reauthenticate at: http://upi-alerts.net",
    "Suspicious login attempt. Secure account: http://secure-login.com",
    "WIN a free iPhone! Click to claim: http://prize-scam.io",
    "Update PAN immediately to avoid block: http://pan-fake.gov.in",
    "Loan pre-approved! Apply now: http://loantrap.org",
    "Recharge ₹{amt} to activate UPI offer: http://fake-upi.io",
    "Verify your account: http://bank-scam.in"
]

# ✅ Legitimate (ham) SMS templates
ham_templates = [
    "Your OTP is {otp}. Do not share it with anyone.",
    "₹{amt} received via UPI from {name}@ybl",
    "Transaction of ₹{amt} to Amazon was successful.",
    "Your order #{order} has been shipped via Bluedart.",
    "Recharge of ₹{amt} completed. Thank you for using PayTM.",
    "Your Jio plan is now active until {date}.",
    "Account balance: ₹{amt}. No recent transactions.",
    "Reminder: Pay your electricity bill by {date}.",
    "Driver {name} is arriving in 5 mins. Ride: {car}.",
    "Your ticket #{order} to Chennai has been confirmed."
]

def generate_messages(n=2000):
    messages = []
    for _ in range(n // 2):
        amt = random.randint(100, 20000)
        otp = random.randint(100000, 999999)
        order = random.randint(1000, 9999)
        name = random.choice(["raj", "meena", "arjun", "kavi", "priya"])
        car = random.choice(["Swift", "WagonR", "Innova", "i20"])
        date = f"{random.randint(1,28)}/0{random.randint(6,9)}/2025"

        p_msg = random.choice(phishing_templates).format(amt=amt)
        h_msg = random.choice(ham_templates).format(amt=amt, otp=otp, name=name, order=order, date=date, car=car)

        messages.append((p_msg, 1))
        messages.append((h_msg, 0))

    random.shuffle(messages)
    return pd.DataFrame(messages, columns=["text", "label"])

# ✅ Save to your path
output_path = r"D:\The New Data Trio\phishing_svm_dataset.csv"
df = generate_messages(2000)
df.to_csv(output_path, index=False)
print(f"✅ Dataset saved to: {output_path}")
