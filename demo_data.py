"""demo_data.py — Generates a comprehensive, realistic 12-month personal finance case study dataset."""

import os
import json
import random
from datetime import datetime, date, timedelta
import pandas as pd

def generate_12_month_case_study(reference_date: date = None) -> dict:
    """
    Generate 12 full months of realistic financial transactions, budgets, goals, debts, and assets.
    This provides rich real-world patterns: regular salaries, freelance bonuses, fixed living costs,
    seasonal vacation spikes, festive holiday expenses, medical anomalies, and consistent savings.
    """
    if reference_date is None:
        reference_date = date.today()

    # Determine start month (11 months before current month)
    # e.g., if ref is Oct 2026, start is Nov 2025
    cur_year = reference_date.year
    cur_month = reference_date.month

    # Generate months list
    months_list = []
    y, m = cur_year, cur_month
    for _ in range(12):
        months_list.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    months_list.reverse() # chronological order

    transactions = []
    tx_id = 1000

    for (yr, mo) in months_list:
        # Salary on 1st of month
        tx_id += 1
        transactions.append({
            "id": f"tx_{tx_id}",
            "date": f"{yr:04d}-{mo:02d}-01",
            "type": "Income",
            "category": "Salary",
            "account": "Bank Account",
            "transfer_to": "",
            "amount": 4200.0,
            "note": "Primary Tech Salary",
            "description": "Monthly direct deposit from employer",
            "source": "Direct Deposit"
        })

        # Freelance Income in specific months (e.g. month 3, 7, 10)
        if mo in [3, 7, 10]:
            tx_id += 1
            freelance_amt = 950.0 if mo == 3 else (1400.0 if mo == 7 else 1100.0)
            transactions.append({
                "id": f"tx_{tx_id}",
                "date": f"{yr:04d}-{mo:02d}-14",
                "type": "Income",
                "category": "Freelance",
                "account": "Bank Account",
                "transfer_to": "",
                "amount": freelance_amt,
                "note": "Client Consulting & UI Design",
                "description": "Contract design sprint milestone payout",
                "source": "Stripe Transfer"
            })

        # Quarterly Investment Dividend in Mar, Jun, Sep, Dec
        if mo in [3, 6, 9, 12]:
            tx_id += 1
            transactions.append({
                "id": f"tx_{tx_id}",
                "date": f"{yr:04d}-{mo:02d}-20",
                "type": "Income",
                "category": "Investment",
                "account": "Bank Account",
                "transfer_to": "",
                "amount": round(145.0 + (mo * 3.5), 2),
                "note": "Quarterly Index ETF Dividend",
                "description": "Dividend reinvestment distribution",
                "source": "Brokerage"
            })

        # Essential Fixed Needs: Rent on 2nd
        tx_id += 1
        transactions.append({
            "id": f"tx_{tx_id}",
            "date": f"{yr:04d}-{mo:02d}-02",
            "type": "Expense",
            "category": "Rent",
            "account": "Bank Account",
            "transfer_to": "",
            "amount": 1400.0,
            "note": "Apartment Monthly Rent",
            "description": "Residential lease transfer",
            "source": "ACH Bank Transfer"
        })

        # Utilities on 5th
        tx_id += 1
        util_amt = 210.0 if mo in [12, 1, 2, 7, 8] else 165.0 # higher in winter/summer peak heating/AC
        transactions.append({
            "id": f"tx_{tx_id}",
            "date": f"{yr:04d}-{mo:02d}-05",
            "type": "Expense",
            "category": "Utilities",
            "account": "Credit Card",
            "transfer_to": "",
            "amount": float(util_amt),
            "note": "Electricity, Gas & Water Bill",
            "description": "City utility council automatic debit",
            "source": "Autopay"
        })

        # Internet & Phone on 8th
        tx_id += 1
        transactions.append({
            "id": f"tx_{tx_id}",
            "date": f"{yr:04d}-{mo:02d}-08",
            "type": "Expense",
            "category": "Utilities",
            "account": "Credit Card",
            "transfer_to": "",
            "amount": 85.0,
            "note": "Fiber High-Speed Internet & Mobile",
            "description": "Telecom monthly package",
            "source": "Credit Card"
        })

        # Health Insurance on 10th
        tx_id += 1
        transactions.append({
            "id": f"tx_{tx_id}",
            "date": f"{yr:04d}-{mo:02d}-10",
            "type": "Expense",
            "category": "Health",
            "account": "Bank Account",
            "transfer_to": "",
            "amount": 120.0,
            "note": "Health & Dental Premium",
            "description": "Monthly supplemental medical coverage",
            "source": "Bank Debit"
        })

        # Student Loan EMI on 5th
        tx_id += 1
        transactions.append({
            "id": f"tx_{tx_id}",
            "date": f"{yr:04d}-{mo:02d}-05",
            "type": "Expense",
            "category": "Other",
            "account": "Bank Account",
            "transfer_to": "",
            "amount": 380.0,
            "note": "Student Loan Monthly EMI",
            "description": "Education debt principal + interest",
            "source": "Autopay"
        })

        # Subscriptions on 12th
        tx_id += 1
        transactions.append({
            "id": f"tx_{tx_id}",
            "date": f"{yr:04d}-{mo:02d}-12",
            "type": "Expense",
            "category": "Subscriptions",
            "account": "Credit Card",
            "transfer_to": "",
            "amount": 34.0,
            "note": "Netflix 4K & Spotify Family",
            "description": "Digital streaming services",
            "source": "Card"
        })

        # Gym Membership on 15th
        tx_id += 1
        transactions.append({
            "id": f"tx_{tx_id}",
            "date": f"{yr:04d}-{mo:02d}-15",
            "type": "Expense",
            "category": "Health",
            "account": "Credit Card",
            "transfer_to": "",
            "amount": 45.0,
            "note": "Fitness Club Membership",
            "description": "Monthly health club gym fee",
            "source": "Card"
        })

        # Weekly Groceries (4 trips per month)
        grocery_days = [4, 11, 18, 25]
        for day in grocery_days:
            tx_id += 1
            g_amt = round(85.0 + ((day * 7 + mo * 3) % 40), 2)
            transactions.append({
                "id": f"tx_{tx_id}",
                "date": f"{yr:04d}-{mo:02d}-{day:02d}",
                "type": "Expense",
                "category": "Food & Dining",
                "account": "Credit Card",
                "transfer_to": "",
                "amount": float(g_amt),
                "note": "Supermarket Weekly Groceries",
                "description": "Fresh produce, pantry & essentials",
                "source": "Grocery Store POS"
            })

        # Dining & Weekend Social (3-4 meals per month)
        dining_days = [7, 14, 21, 28]
        for day in dining_days:
            tx_id += 1
            d_amt = round(35.0 + ((day * 9 + mo * 5) % 55), 2)
            transactions.append({
                "id": f"tx_{tx_id}",
                "date": f"{yr:04d}-{mo:02d}-{day:02d}",
                "type": "Expense",
                "category": "Food & Dining",
                "account": "Credit Card",
                "transfer_to": "",
                "amount": float(d_amt),
                "note": "Weekend Bistro & Cafe Takeout",
                "description": "Social dining and takeout",
                "source": "Card"
            })

        # Commute & Transit (fuel/metro)
        for day in [6, 20]:
            tx_id += 1
            t_amt = 65.0 if day == 6 else 75.0
            transactions.append({
                "id": f"tx_{tx_id}",
                "date": f"{yr:04d}-{mo:02d}-{day:02d}",
                "type": "Expense",
                "category": "Transport",
                "account": "Credit Card",
                "transfer_to": "",
                "amount": float(t_amt),
                "note": "Metro Card Reload & Fuel",
                "description": "Daily urban transit refill",
                "source": "Transit Kiosk"
            })

        # Monthly Regular Savings Transfer (to High Yield Savings)
        tx_id += 1
        transactions.append({
            "id": f"tx_{tx_id}",
            "date": f"{yr:04d}-{mo:02d}-03",
            "type": "Transfer",
            "category": "Investment",
            "account": "Bank Account",
            "transfer_to": "Savings",
            "amount": 600.0,
            "note": "Automated Emergency Fund Transfer",
            "description": "Transferred to High Yield Savings Account",
            "source": "Internal Transfer"
        })

        # Regular Shopping / Clothes / Home
        tx_id += 1
        transactions.append({
            "id": f"tx_{tx_id}",
            "date": f"{yr:04d}-{mo:02d}-17",
            "type": "Expense",
            "category": "Shopping",
            "account": "Credit Card",
            "transfer_to": "",
            "amount": float(round(120.0 + ((mo * 17) % 80), 2)),
            "note": "Apparel & Household Goods",
            "description": "Amazon & local departmental store",
            "source": "Online"
        })

        # ── REALISTIC SEASONAL SPIKES & ANOMALIES ─────────────────────────
        # July: Summer Holiday Vacation Trip (Big Travel Spike)
        if mo == 7:
            tx_id += 1
            transactions.append({
                "id": f"tx_{tx_id}",
                "date": f"{yr:04d}-07-16",
                "type": "Expense",
                "category": "Travel",
                "account": "Credit Card",
                "transfer_to": "",
                "amount": 1150.0,
                "note": "Summer Vacation Flights & Resort",
                "description": "Annual summer holiday airline tickets and lodging",
                "source": "Airline Portal"
            })
            tx_id += 1
            transactions.append({
                "id": f"tx_{tx_id}",
                "date": f"{yr:04d}-07-22",
                "type": "Expense",
                "category": "Entertainment",
                "account": "Credit Card",
                "transfer_to": "",
                "amount": 280.0,
                "note": "Vacation Excursions & Guided Tour",
                "description": "Island tour and scuba activity pass",
                "source": "POS"
            })

        # December: Festive Season & Holiday Gifts (Shopping & Dining Spike)
        if mo == 12:
            tx_id += 1
            transactions.append({
                "id": f"tx_{tx_id}",
                "date": f"{yr:04d}-12-22",
                "type": "Expense",
                "category": "Shopping",
                "account": "Credit Card",
                "transfer_to": "",
                "amount": 540.0,
                "note": "Holiday Gifts for Family & Friends",
                "description": "Festive season gift shopping",
                "source": "Retail Store"
            })
            tx_id += 1
            transactions.append({
                "id": f"tx_{tx_id}",
                "date": f"{yr:04d}-12-24",
                "type": "Expense",
                "category": "Food & Dining",
                "account": "Credit Card",
                "transfer_to": "",
                "amount": 175.0,
                "note": "Holiday Family Dinner",
                "description": "Christmas eve dinner party",
                "source": "Restaurant POS"
            })

        # April: Emergency Dental / Medical Procedure (Health Anomaly)
        if mo == 4:
            tx_id += 1
            transactions.append({
                "id": f"tx_{tx_id}",
                "date": f"{yr:04d}-04-18",
                "type": "Expense",
                "category": "Health",
                "account": "Bank Account",
                "transfer_to": "",
                "amount": 420.0,
                "note": "Emergency Dental Procedure & Crown",
                "description": "Out-of-pocket dental surgery copay",
                "source": "Clinic POS"
            })

        # September: Professional Education / Certification (Self Improvement)
        if mo == 9:
            tx_id += 1
            transactions.append({
                "id": f"tx_{tx_id}",
                "date": f"{yr:04d}-09-11",
                "type": "Expense",
                "category": "Education",
                "account": "Credit Card",
                "transfer_to": "",
                "amount": 320.0,
                "note": "Cloud Architecture Professional Exam & Course",
                "description": "AWS / GCP Certification voucher and prep bundle",
                "source": "Online"
            })

    # Realistic Budgets
    budgets = {
        "Food & Dining": 480.0,
        "Rent": 1400.0,
        "Transport": 180.0,
        "Shopping": 250.0,
        "Entertainment": 150.0,
        "Utilities": 250.0,
        "Health": 180.0,
        "Subscriptions": 50.0,
        "Education": 100.0,
        "Travel": 300.0,
        "Other": 400.0,
    }

    # Realistic Goals
    goals = [
        {
            "id": "g_01",
            "name": "Emergency Fund (6 Months Expenses)",
            "target": 15000.0,
            "current": 11800.0,
            "target_date": f"{cur_year + 1}-06-30",
            "emoji": "🛡️",
            "notes": "Six full months of living runway in high-yield liquid savings."
        },
        {
            "id": "g_02",
            "name": "Japan Cultural Trip & Bullet Train",
            "target": 4500.0,
            "current": 2900.0,
            "target_date": f"{cur_year + 1}-04-15",
            "emoji": "✈️",
            "notes": "Flight tickets, 14-day JR rail pass, and accommodations in Tokyo & Kyoto."
        },
        {
            "id": "g_03",
            "name": "Apple M3 MacBook Pro Workstation",
            "target": 2200.0,
            "current": 2200.0,
            "target_date": f"{cur_year}-09-15",
            "emoji": "💻",
            "notes": "100% funded and purchased for freelance work and development! 🎉"
        }
    ]

    # Realistic Debts
    debts = [
        {
            "id": "d_01",
            "name": "Federal Student Education Loan",
            "principal": 18000.0,
            "remaining": 5400.0,
            "interest_rate": 4.8,
            "emi": 380.0,
            "due_day": 5,
            "payments_made": 33,
            "created_at": f"{cur_year - 3}-01-15"
        },
        {
            "id": "d_02",
            "name": "Travel Rewards Credit Card",
            "principal": 1200.0,
            "remaining": 420.0,
            "interest_rate": 16.5,
            "emi": 150.0,
            "due_day": 18,
            "payments_made": 5,
            "created_at": f"{cur_year}-05-10"
        }
    ]

    # Realistic Assets & Net Worth
    assets = {
        "Checking Account (Operational Cash)": 3850.0,
        "High-Yield Liquid Savings": 11800.0,
        "Retirement & Index Funds (S&P 500)": 24500.0,
        "Vehicle Equity (Resale Value)": 9500.0,
    }

    # Recurring templates
    recurring = [
        {
            "id": "rec_01",
            "type": "Expense",
            "category": "Rent",
            "account": "Bank Account",
            "transfer_to": "",
            "amount": 1400.0,
            "note": "Apartment Lease Rent",
            "recurrence": "Monthly",
            "start_date": f"{cur_year}-01-01",
            "last_generated": f"{cur_year}-{cur_month:02d}-02"
        },
        {
            "id": "rec_02",
            "type": "Expense",
            "category": "Subscriptions",
            "account": "Credit Card",
            "transfer_to": "",
            "amount": 34.0,
            "note": "Netflix & Spotify Subscription",
            "recurrence": "Monthly",
            "start_date": f"{cur_year}-01-01",
            "last_generated": f"{cur_year}-{cur_month:02d}-12"
        },
        {
            "id": "rec_03",
            "type": "Expense",
            "category": "Health",
            "account": "Credit Card",
            "transfer_to": "",
            "amount": 45.0,
            "note": "Gym & Fitness Membership",
            "recurrence": "Monthly",
            "start_date": f"{cur_year}-01-01",
            "last_generated": f"{cur_year}-{cur_month:02d}-15"
        }
    ]

    return {
        "transactions": transactions,
        "budgets": budgets,
        "goals": goals,
        "debts": debts,
        "assets": assets,
        "recurring": recurring
    }


def seed_local_data_files():
    """Seed data directory with realistic case study data so files are never empty."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(root_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    study = generate_12_month_case_study()

    # 1. transactions.csv
    df = pd.DataFrame(study["transactions"])
    df.to_csv(os.path.join(data_dir, "transactions.csv"), index=False)

    # 2. budgets.json
    with open(os.path.join(data_dir, "budgets.json"), "w", encoding="utf-8") as f:
        json.dump(study["budgets"], f, indent=2)

    # 3. goals.json
    with open(os.path.join(data_dir, "goals.json"), "w", encoding="utf-8") as f:
        json.dump(study["goals"], f, indent=2)

    # 4. debts.json
    with open(os.path.join(data_dir, "debts.json"), "w", encoding="utf-8") as f:
        json.dump(study["debts"], f, indent=2)

    # 5. assets.json
    with open(os.path.join(data_dir, "assets.json"), "w", encoding="utf-8") as f:
        json.dump(study["assets"], f, indent=2)

    # 6. recurring.json
    with open(os.path.join(data_dir, "recurring.json"), "w", encoding="utf-8") as f:
        json.dump(study["recurring"], f, indent=2)


if __name__ == "__main__":
    seed_local_data_files()
    print("Successfully generated and seeded 12-month case study data!")
