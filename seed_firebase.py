import pandas as pd
import firebase_client

def seed_fraud_accounts():
    print("Loading datasets...")
    try:
        df1 = pd.read_excel('fraud_tracking_report.xlsx')
        fraud_accounts_1 = set(df1['receiver_account'].dropna().unique())
        print(f"Found {len(fraud_accounts_1)} fraud accounts in report.")
    except Exception as e:
        print("Could not load fraud_tracking_report:", e)
        fraud_accounts_1 = set()

    try:
        df2 = pd.read_excel('indian_cities_rupees_dataset.xlsx')
        fraud_txns = df2[df2['is_fraud'] == 1]
        fraud_accounts_2 = set(fraud_txns['receiver_account'].dropna().unique())
        print(f"Found {len(fraud_accounts_2)} fraud receiving accounts in main dataset.")
    except Exception as e:
        print("Could not load dataset:", e)
        fraud_accounts_2 = set()

    all_fraud_accounts = fraud_accounts_1.union(fraud_accounts_2)
    print(f"Total unique fraud accounts to seed: {len(all_fraud_accounts)}")
    
    # Add the explicit sample data from the UI! The user specifically mentioned "spam numbers".
    explicit_data = [
        ("phone", "09876543210"),
        ("phone", "9876543210"),
        ("account", "ACC182189"),
        ("account", "ACC973758"),
        ("phone", "8765432109"),
        ("phone", "7654321098"),
    ]
    
    count = 0
    for etype, evalue in explicit_data:
        print(f"Seeding explicit sample: {etype} - {evalue}")
        firebase_client.save_entity(etype, evalue, "FLAGGED", "Seeded from sample dataset")
        count += 1
        
    accounts_list = list(all_fraud_accounts)[:50]  # First 50 to avoid timeout
    for acc in accounts_list:
        firebase_client.save_entity("account", acc, "FLAGGED", "Seeded from dataset")
        count += 1
        if count % 10 == 0:
            print(f"Seeded {count} entities...")
    
    print(f"Seeding complete! Saved {count} items.")

if __name__ == '__main__':
    seed_fraud_accounts()
