import os 
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np 
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import random
from data.raw.details import STATE_CITIES,STATES,OPERATORS,OPERATOR_SHARE_BASE,STATE_WEIGHT

random.seed(42)
np.random.seed(42)

MONTHS         = 24          # months of history
START_MONTH    = "2023-01"   # YYYY-MM
VENDORS_PER_STATE = 100      # service providers per state → ~52,800 billing rows
OUTPUT_DIR     = "data/raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# will generate Monthly dates start from START_MONTH for next # of MONTHS
def get_months():
    start = datetime.strptime(START_MONTH, "%Y-%m")
    return [(start + relativedelta(months=i)).strftime("%Y-%m") for i in range(MONTHS)]

# ['2023-01', '2023-02', '2023-03', '2023-04', '2023-05' .... , '2024-12']
MONTH_LIST = get_months()


# ─────────────────────────────────────────────
# TABLE 1: trai_subscribers
# Rows: 22 states x 10 cities × 5 operators × 24 months = 26,400
# ─────────────────────────────────────────────

def generate_trai_subscribers():
    rows=[]
    for month_idx,month in enumerate(MONTH_LIST):
        for state in STATES:
            state_weight=STATE_WEIGHT.get(state,1)
            cities=STATE_CITIES.get(state,[state])
            for city in cities:
                city_weight=np.random.uniform(0.5,2.0)
                total_city_subs_base=int(state_weight*city_weight*np.random.randint(500_000,2_000_000))

                op_shares={} # will capture change in opeator share with time
                for op in OPERATORS:
                    base_op_share_perc=OPERATOR_SHARE_BASE[op]
                    trend=0
                    if op=='Vi' : trend = -0.15*month_idx # shrinks over time
                    if op == "Jio": trend = +0.10*month_idx # grows over time
                    if op == "BSNL":  trend = -0.05*month_idx # slowly shrinks
                    
                    # Adds a small random fluctuation of ±1.5% each month
                    noisy_share = max(1, base_op_share_perc + trend + np.random.uniform(-1.5, 1.5)) 

                    op_shares[op] = noisy_share
                
                total_share = sum(op_shares.values())

                for op in OPERATORS:
                    share_perc=round(op_shares[op]*100.0/total_share,2)
                    wireless_subs=int(total_city_subs_base*share_perc/100)
                    wireline_subs=int(wireless_subs*np.random.uniform(0.01,0.05))
                
                    rows.append({
                        "month":            month,
                        "state":            state,
                        "city":             city,
                        "operator":         op,
                        "wireless_subs":    wireless_subs,
                        "wireline_subs":    wireline_subs,
                        "market_share_perc": share_perc,
                        "mom_growth_perc":   round(np.random.uniform(-2.5, 4.0) + (0.1 if op=="Jio" else -0.05 if op=="Vi" else 0), 2)
                    })
    df=pd.DataFrame(rows)
    df.to_csv(f"{OUTPUT_DIR}/trai_subscribers.csv",index=False)

    print(f"✅ trai_subscribers.csv → {len(df)} rows")
    return df

# ─────────────────────────────────────────────
# TABLE 2: operator_revenue
# Rows: 5 operators × 22 states x 10 cities × 24 months = 26,400
# ─────────────────────────────────────────────

def generate_operator_revenue():
    rows = []
    # ARPU -> average revenue per user
    ARPU_BASE = {"Jio": 185, "Airtel": 210, "Vi": 155, "BSNL": 90, "MTNL": 95}

    for month in MONTH_LIST:
        for state in STATES:
            cities = STATE_CITIES.get(state, [state])
            for city in cities:
                for op in OPERATORS:
                    city_arpu=ARPU_BASE[op]+np.random.uniform(-15,15)
                    city_weight = np.random.uniform(0.5, 2.0)
                    state_weight=STATE_WEIGHT.get(state,1)

                    total_city_subs_base=state_weight*city_weight*500_000*OPERATOR_SHARE_BASE[op] / 100
                    revenue_crore = round((city_arpu * total_city_subs_base) / 1e7, 2)

                    rows.append({
                        "month":             month,
                        "state":             state,
                        "city":              city,
                        "operator":          op,
                        "revenue_crore":     revenue_crore,
                        "ARPU":              round(city_arpu, 2),
                        "data_revenue_perc":  round(np.random.uniform(55, 80), 2),
                        "voice_revenue_perc": round(np.random.uniform(15, 35), 2),
                    })
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUTPUT_DIR}/operator_revenue.csv", index=False)
    print(f"✅ operator_revenue.csv → {len(df)} rows")
    return df


# ─────────────────────────────────────────────
# TABLE 3: tower_qos (quality of service)
# Rows: 22 states x 10 cities × 5 operators × 24 months = 26,400
# ─────────────────────────────────────────────

def generate_tower_qos():
    rows=[]
    QOS_BASE = {
        "Jio":    {"call_drop": 0.8,  "data_speed": 28, "uptime": 99.2},
        "Airtel": {"call_drop": 0.7,  "data_speed": 32, "uptime": 99.4},
        "Vi":     {"call_drop": 1.4,  "data_speed": 18, "uptime": 98.1},
        "BSNL":   {"call_drop": 2.8,  "data_speed": 8,  "uptime": 96.5},
        "MTNL":   {"call_drop": 2.5,  "data_speed": 9,  "uptime": 96.8},
    }

    RURAL_STATES = {"Bihar", "Jharkhand", "Assam", "Odisha", "Uttarakhand", "Himachal Pradesh"}

    for month in MONTH_LIST:
        for state in STATES:
            cities=STATE_CITIES.get(state,[state])
            rural_penalty = 1.3 if state in RURAL_STATES else 1.0

            for city in cities:
                for op in OPERATORS:
                    city_base=QOS_BASE[op]

                    rows.append({
                        "month":               month,
                        "state":               state,
                        "city":                city,
                        "operator":            op,
                        "call_drop_rate":      round(city_base["call_drop"] * rural_penalty + np.random.uniform(-0.2, 0.4), 2),
                        "avg_data_speed_mbps": round(city_base["data_speed"] / rural_penalty + np.random.uniform(-2, 3), 2),
                        "tower_uptime_perc":    round(min(99.9, city_base["uptime"] - (rural_penalty - 1) * 2 + np.random.uniform(-0.3, 0.3)), 2),
                        "latency_ms":          round(np.random.uniform(20, 80) * rural_penalty, 1),
                        "complaints_per_1k":   round(np.random.uniform(0.5, 5.0) * rural_penalty, 2),
                    })
    
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUTPUT_DIR}/tower_qos.csv", index=False)
    print(f"✅ tower_qos.csv → {len(df)} rows")
    return df

# ─────────────────────────────────────────────
# TABLE 4: service_provider_billing 
# service_providers: field contractors and infrastructure companies that do physical work on the ground
# Rows: ~52,800 (100 vendors × 22 states × 24 months)
# Mirrors Jio's R4G vendor billing structure
# ─────────────────────────────────────────────

def generate_service_provider_billing():
    rows=[]

    # Generate vendor master
    vendor_ids = [f"V{str(i).zfill(4)}" for i in range(1, VENDORS_PER_STATE * len(STATES) + 1)]
    vendor_names = [
        f"{random.choice(['TechServ', 'InfraBuild', 'NetCon', 'TowerLink', 'FibreMax', 'ConnectPro', 'GridNet', 'SignalTech'])} "
        f"{random.choice(['Solutions', 'Services', 'Pvt Ltd', 'Enterprises', 'Group', 'Corp'])}"
        for _ in vendor_ids
    ]

    # Assign each vendor to a state
    # vendor_id index % len(state) => i%22
    vendor_state_map = {}
    for i, vid in enumerate(vendor_ids):
        vendor_state_map[vid] = STATES[i % len(STATES)]
    
    for month in MONTH_LIST:
        for vid,vname in zip(vendor_ids,vendor_names):
            state=vendor_state_map[vid]
            base_payout=np.random.uniform(5_00_000,50_00_000)  # ₹5L to ₹50L

            # Performance score drives penalty/reward
            performance_score=np.random.uniform(60,100)
            penalty_rate=max(0,(80-performance_score)/100*0.15)  # up to 15% penalty
            reward_rate=max(0,(performance_score-90)/100*0.10)  # up to 10% reward

            penalty_amt=round(base_payout*penalty_rate,2)
            reward_amt=round(base_payout*reward_rate,2)
            net_payout=round(base_payout-penalty_amt+reward_amt,2)

            rows.append({
                "month": month,
                "vendor_id": vid,
                "vendor_name": vname,
                "state": state,
                "base_payout":round(base_payout, 2),
                "penalty_amount": penalty_amt,
                "reward_amount": reward_amt,
                "net_payout": net_payout,
                "performance_score": round(performance_score, 2),
                "sla_breaches": int(max(0, (80 - performance_score) / 5)),
                "work_orders_completed": int(np.random.uniform(50, 500)),
            })
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUTPUT_DIR}/service_provider_billing.csv", index=False)
    print(f"✅ service_provider_billing.csv → {len(df)} rows")
    return df
    

# ─────────────────────────────────────────────
# TABLE 5: telco_churn (customer cancelling/leaving their current operator)
# 1 = customer left the operator, 0 = customer stayed
# Rows: ~10,000 customers
# ─────────────────────────────────────────────

def generate_telco_churn(n_customers=50_000):
    rows = []
    plan_types    = ["Prepaid", "Postpaid"]
    internet_types = ["Fiber", "4G", "3G", "No Service"]

    for i in range(n_customers):
        state    = random.choice(STATES)
        operator = random.choices(OPERATORS, weights=[35, 30, 18, 12, 5])[0]
        tenure   = int(np.random.exponential(24))  # months, how long a customer has been with their operator 
        plan     = random.choice(plan_types)

        monthly_charge = np.random.uniform(99, 999)
        if operator in ["BSNL", "MTNL"]: monthly_charge *= 0.6

        # Churn probability: Vi > BSNL > others; short tenure → higher churn
        churn_prob = 0.10
        if operator == "Vi":   churn_prob += 0.15
        if operator == "BSNL": churn_prob += 0.10
        if tenure < 6:         churn_prob += 0.20
        if monthly_charge > 700: churn_prob += 0.05
        churn_prob = min(churn_prob, 0.95)

        rows.append({
            "customer_id": f"C{str(i).zfill(6)}",
            "state": state,
            "operator": operator,
            "plan_type": plan,
            "tenure_months": tenure,
            "monthly_charge": round(monthly_charge, 2),
            "total_charges": round(monthly_charge * tenure, 2),
            "internet_service": random.choice(internet_types),
            "num_complaints": int(np.random.poisson(1.5)),
            "churn": int(np.random.random() < churn_prob),
        })

    df = pd.DataFrame(rows)
    df.to_csv(f"{OUTPUT_DIR}/telco_churn.csv", index=False)
    print(f"✅ telco_churn.csv → {len(df)} rows")
    return df



