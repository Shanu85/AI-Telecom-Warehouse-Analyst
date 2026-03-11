schema={
    "trai_subscribers": """
        CREATE TABLE IF NOT EXISTS trai_subscribers (
            month VARCHAR,
            state VARCHAR,
            city VARCHAR,
            operator VARCHAR,
            wireless_subs BIGINT,
            wireline_subs BIGINT,
            market_share_perc DOUBLE,
            mom_growth_perc DOUBLE
        )
    """,
    "operator_revenue": """
        CREATE TABLE IF NOT EXISTS operator_revenue (
            month VARCHAR,
            state VARCHAR,
            city VARCHAR,
            operator VARCHAR,
            revenue_crore DOUBLE,
            ARPU DOUBLE,
            data_revenue_perc DOUBLE,
            voice_revenue_perc DOUBLE 
        )
    """,
    "tower_qos": """
        CREATE TABLE IF NOT EXISTS tower_qos (
            month VARCHAR,
            state VARCHAR,
            city VARCHAR,
            operator VARCHAR,
            call_drop_rate DOUBLE,
            avg_data_speed_mbps DOUBLE,
            tower_uptime_perc DOUBLE,
            latency_ms DOUBLE,
            complaints_per_1k DOUBLE
        )
    """,
    "service_provider_billing": """
        CREATE TABLE IF NOT EXISTS service_provider_billing (
            month VARCHAR,
            vendor_id VARCHAR, --e.g. 'V0001'
            vendor_name VARCHAR,
            state VARCHAR,
            base_payout DOUBLE,
            penalty_amount DOUBLE,
            reward_amount DOUBLE,
            net_payout DOUBLE,
            performance_score DOUBLE,
            sla_breaches INTEGER,
            work_orders_completed INTEGER
        )
    """,
    "telco_churn": """
        CREATE TABLE IF NOT EXISTS telco_churn (
            customer_id VARCHAR, --e.g. 'C000001'
            state VARCHAR,
            operator VARCHAR,
            plan_type VARCHAR, --'Prepaid' or 'Postpaid'
            tenure_months INTEGER,
            monthly_charge DOUBLE,
            total_charges DOUBLE,
            internet_service VARCHAR, -- 'Fiber', '4G', '3G', 'No Service'
            num_complaints INTEGER,
            churn INTEGER -- 1 = churned, 0 = retained
        )
    """
}

# ─────────────────────────────────────────────────────────────
# COLUMN DESCRIPTIONS (used by LLM for richer prompt context)
# Plain English descriptions passed to the LLM so it can
# generate accurate SQL without guessing column semantics.
# ─────────────────────────────────────────────────────────────
schema_descriptions = {
    "trai_subscribers": {
        "_table_description": (
            "Monthly city-level subscriber counts for each telecom operator across Indian states. "
            "Use this table for market share analysis, subscriber growth trends, and operator comparisons by geography."
        ),
        "month": "Reporting month in YYYY-MM format. Use for time-series and trend queries.",
        "state": "Indian state name e.g. 'Maharashtra', 'Karnataka'. Always use ILIKE for filtering.",
        "city": "City within the state e.g. 'Mumbai', 'Bengaluru'. 10 cities per state.",
        "operator": "Telecom operator name. Values: 'Jio', 'Airtel', 'Vi', 'BSNL', 'MTNL'.",
        "wireless_subs": "Count of active mobile/wireless subscribers. Main volume metric.",
        "wireline_subs": "Count of active broadband or landline subscribers. Much smaller than wireless.",
        "market_share_perc": "Operator's share of total wireless subscribers in that city and month (0-100%). Sum across operators ≈ 100.",
        "mom_growth_perc": "Month-over-month % change in wireless subscribers. Negative means subscriber loss.",
    },
    "operator_revenue": {
        "_table_description": (
            "Monthly city-level revenue and ARPU metrics per telecom operator. "
            "Use for revenue analysis, ARPU comparisons, and understanding monetisation across geographies."
        ),
        "month": "Reporting month in YYYY-MM format.",
        "state": "Indian state name.",
        "city": "City within the state.",
        "operator": "Telecom operator. Values: 'Jio', 'Airtel', 'Vi', 'BSNL', 'MTNL'.",
        "revenue_crore": "Total revenue in Indian Crore rupees (1 Crore = 10 million INR). Main revenue metric.",
        "ARPU": "Average Revenue Per User in INR per month. Airtel typically highest (~210), BSNL lowest (~90).",
        "data_revenue_perc": "Percentage of revenue earned from mobile data services (55-80% range).",
        "voice_revenue_perc": "Percentage of revenue earned from voice/call services (15-35% range).",
    },
    "tower_qos": {
        "_table_description": (
            "Monthly city-level network Quality of Service (QoS) metrics per operator. "
            "Use for network performance analysis, identifying weak coverage areas, and comparing service quality."
        ),
        "month": "Reporting month in YYYY-MM format.",
        "state": "Indian state name. Rural states (Bihar, Assam, Jharkhand etc.) have worse QoS.",
        "city": "City within the state.",
        "operator": "Telecom operator. Values: 'Jio', 'Airtel', 'Vi', 'BSNL', 'MTNL'.",
        "call_drop_rate": "% of voice calls dropped mid-conversation. Lower is better. TRAI benchmark < 1.5%. BSNL/Vi tend to be higher.",
        "avg_data_speed_mbps": "Average 4G/5G download speed in Mbps. Higher is better. Airtel leads (~32 Mbps), BSNL lowest (~8 Mbps).",
        "tower_uptime_perc": "% of time network towers are operational. Ideal is > 99%. Values below 97% indicate serious issues.",
        "latency_ms": "Network round-trip latency in milliseconds. Lower is better. High latency hurts video calls and gaming.",
        "complaints_per_1k": "Customer complaints per 1000 subscribers. Higher values indicate poor user experience.",
    },
    "service_provider_billing": {
        "_table_description": (
            "Monthly billing records for vendors/service providers contracted by the telecom operator. "
            "Tracks payouts, penalties, rewards, and performance scores. "
            "Mirrors real-world R4G vendor billing used at Jio. "
            "Use for vendor performance analysis, penalty audits, and payout reconciliation."
        ),
        "month": "Reporting month in YYYY-MM format.",
        "vendor_id": "Unique vendor identifier e.g. 'V0001'. Foreign key to vendor master.",
        "vendor_name": "Full company name of the service provider e.g. 'TechServ Solutions Pvt Ltd'.",
        "state": "State where the vendor operates and delivers services.",
        "base_payout": "Agreed contractual base payment in INR before any penalty or reward adjustment.",
        "penalty_amount": "Amount deducted from base_payout due to SLA violations or performance_score < 80. Can be 0.",
        "reward_amount": "Bonus added when performance_score > 90. Can be 0 if score is between 80-90.",
        "net_payout": "Final payment disbursed = base_payout - penalty_amount + reward_amount. Use this for financial analysis.",
        "performance_score": "Overall vendor performance score 0-100. Score > 90 earns reward; score < 80 triggers penalty.",
        "sla_breaches": "Count of Service Level Agreement violations in the month. Directly causes penalty_amount.",
        "work_orders_completed": "Number of field tasks (installation, maintenance, repair) completed by the vendor.",
    },
    "telco_churn": {
        "_table_description": (
            "Individual customer-level churn dataset. Each row is one customer. "
            "Use for churn analysis, customer segmentation, and identifying at-risk customer profiles. "
            "Can be joined with tower_qos on state+operator to correlate network quality with churn."
        ),
        "customer_id": "Unique customer identifier e.g. 'C000001'. Primary key.",
        "state": "Indian state where the customer resides. Join with other tables on this column.",
        "operator": "Operator the customer is subscribed to. Values: 'Jio', 'Airtel', 'Vi', 'BSNL', 'MTNL'.",
        "plan_type": "Subscription type: 'Prepaid' (pay-as-you-go) or 'Postpaid' (monthly billing).",
        "tenure_months": "How many months the customer has been with the operator. Short tenure = higher churn risk.",
        "monthly_charge": "Monthly bill in INR. Higher charges increase churn risk.",
        "total_charges": "Total amount paid = monthly_charge x tenure_months approximately.",
        "internet_service": "Type of internet: 'Fiber' (fastest), '4G', '3G', or 'No Service'.",
        "num_complaints": "Total complaints the customer has raised. More complaints = higher churn likelihood.",
        "churn": "Target variable: 1 = customer left the operator, 0 = customer is still active",
    },
}
