import pandas as pd
from collections import defaultdict

class UserBehaviorTracker:
    def __init__(self):
        self.user_history = defaultdict(list)
        self.last_time = {}

    def compute_features(self, row):
        user = row["sender_account"]
        amount = row["amount"]
        timestamp = row["timestamp"]

        history = self.user_history[user]

        avg = sum(history)/len(history) if history else amount
        amount_dev = abs(amount - avg)

        if user in self.last_time:
            time_diff = (timestamp - self.last_time[user]).total_seconds()
            velocity = 1 / time_diff if time_diff != 0 else 1
        else:
            velocity = 0

        new_ip = 1
        new_device = 1

        return {
            "amount_deviation": amount_dev,
            "velocity": velocity,
            "new_ip": new_ip,
            "new_device": new_device
        }

    def update_profile(self, row):
        user = row["sender_account"]
        self.user_history[user].append(row["amount"])
        self.last_time[user] = row["timestamp"]


def behaviour_risk_score(features):
    score = 0

    if features["amount_deviation"] > 30000:
        score += 2
    if features["velocity"] > 0.5:
        score += 2
    if features["new_ip"] == 1:
        score += 1
    if features["new_device"] == 1:
        score += 1

    return score