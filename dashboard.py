import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_excel("realtime_fraud_results.xlsx")

counts = df["decision"].value_counts()

plt.figure()
counts.plot(kind="bar")
plt.title("Fraud Detection Summary")
plt.xlabel("Decision")
plt.ylabel("Count")
plt.show()