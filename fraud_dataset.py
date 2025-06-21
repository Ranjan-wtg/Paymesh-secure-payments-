import random
import csv

def generate_txn(hour_range, amount_range, n):
    data = []
    for _ in range(n):
        hour = random.randint(hour_range[0], hour_range[1])
        minute = random.randint(0, 59)
        time_str = f"{hour:02d}:{minute:02d}"
        amount = random.randint(amount_range[0], amount_range[1])
        data.append({"amount": amount, "time": time_str})
    return data


def create_dataset():
    legit_day = generate_txn((9, 17), (100, 1000), 30)        # Normal small txns in day
    high_risk_night = generate_txn((0, 4), (10000, 20000), 20)  # Big txns at night = 🚨
    mid_risk = generate_txn((19, 23), (3000, 8000), 15)         # Mid amount, mid time
    weird_small_night = generate_txn((1, 3), (500, 1000), 10)   # Small but weird hour

    dataset = legit_day + high_risk_night + mid_risk + weird_small_night
    random.shuffle(dataset)

    with open(r"D:\The New Data Trio\fraud_dataset.csv", "w", newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["amount", "time"])
        writer.writeheader()
        for row in dataset:
            writer.writerow(row)

    print("✅ Dataset created at D:\\The New Data Trio\\fraud_dataset.csv")


if __name__ == "__main__":
    create_dataset()
