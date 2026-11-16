from pathlib import Path
import re
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="The Cipher | Ville-In-Us Cards",
    page_icon="🟣",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Ville-In-Us Cards Brand Theme ("The Underground Vault" - Crimson & Violet)
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Main Underground Vault Background with Subtle Radial Crimson/Purple Glow */
    .stApp {
        background:
            radial-gradient(circle at 50% 10%, rgba(255, 29, 88, 0.14) 0%, rgba(147, 51, 234, 0.14) 32%, rgba(9, 9, 14, 0.98) 70%),
            #09090e !important;
        color: #f8fafc;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0b14 0%, #120f1d 100%) !important;
        border-right: 1px solid rgba(168, 85, 247, 0.25);
    }

    /* Underground Vault Pill Badge */
    .vault-pill {
        display: inline-block;
        padding: 5px 16px;
        border-radius: 9999px;
        background: rgba(20, 18, 32, 0.9);
        border: 1px solid rgba(168, 85, 247, 0.35);
        color: #cbd5e1;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        margin-bottom: 10px;
        box-shadow: 0 0 18px rgba(168, 85, 247, 0.15);
    }

    /* Brand Gradient Hero Title (Matches villeinuscards.com) */
    .brand-hero-title {
        font-size: 2.5rem;
        font-weight: 900;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        background: linear-gradient(90deg, #ff1e56 0%, #e11d74 45%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 4px 0;
        line-height: 1.15;
    }

    .brand-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 1.2rem;
    }

    /* Metadata Status Strip */
    .comp-metadata-bar {
        background: rgba(19, 19, 29, 0.88);
        border: 1px solid rgba(168, 85, 247, 0.3);
        border-left: 4px solid #e11d74;
        border-radius: 10px;
        padding: 12px 18px;
        margin-bottom: 18px;
        font-size: 0.92rem;
        color: #e2e8f0;
    }

    /* Vault Container Cards (Path A, Path B, Path C) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(19, 19, 28, 0.92) !important;
        border: 1px solid rgba(168, 85, 247, 0.28) !important;
        border-radius: 14px !important;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.45), 0 0 20px rgba(147, 51, 234, 0.08) !important;
        padding: 6px !important;
    }

    /* Metric Value Typography */
    div[data-testid="stMetricValue"] {
        font-weight: 800 !important;
        color: #ffffff !important;
    }

    div[data-testid="stMetricLabel"] {
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.75rem !important;
        color: #a1a1aa !important;
    }

    /* Tier 2 Clickable Expander Styling - High-Visibility Neon Border */
    details[data-testid="stExpander"] {
        background: linear-gradient(90deg, rgba(255, 30, 86, 0.10) 0%, rgba(168, 85, 247, 0.14) 100%) !important;
        border: 1px solid rgba(192, 38, 211, 0.45) !important;
        border-radius: 10px !important;
        margin-top: 10px !important;
    }

    details[data-testid="stExpander"] summary {
        font-weight: 700 !important;
        color: #f5d0fe !important;
    }

    details[data-testid="stExpander"] summary:hover {
        color: #ffffff !important;
    }

    /* Ensure Dark Inputs/Selectboxes/Text on Mobile & Cloud */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    textarea {
        background-color: #13131d !important;
        color: #f8fafc !important;
        border-color: rgba(168, 85, 247, 0.35) !important;
    }
    p, li, label, span {
        color: #f1f5f9;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Fixed Friction Constants from PROJECT_SPEC.md
EBAY_FEE_RATE = 0.1325          # 13.25% eBay Final Value Fee
OUTBOUND_SHIPPING = 4.50        # $4.50 Ground Advantage bubble mailer + supplies
PSA_GRADING_COST = 47.00        # $39.99 Value tier + ~$7.01 amortized shipping/prep

LOGO_PATH = (
    Path(__file__).parent / "logo.png"
    if (Path(__file__).parent / "logo.png").exists()
    else Path(__file__).parent / "assets" / "logo.png"
)

# ---------------------------------------------------------------------------
# Sandbox 30-Day Settled Sales Data (Panini Prizm True Silver Autos)
# ---------------------------------------------------------------------------
SANDBOX_CARDS = {
    "2023 Panini Prizm Bijan Robinson True Silver Auto #305": {
        "Raw": [145.00, 152.50, 160.00, 165.00, 168.00, 170.00, 172.50, 175.00, 178.00, 180.00, 185.00, 190.00, 195.00, 210.00],
        "PSA 10": [380.00, 395.00, 410.00, 425.00, 440.00, 465.00],
        "PSA 9": [195.00, 205.00, 210.00, 215.00, 220.00, 225.00, 235.00, 240.00],
        "BGS 9.5": [265.00, 275.00, 285.00, 290.00, 310.00],
        "SGC 10": [290.00, 305.00, 315.00, 325.00],
    },
    "2022 Panini Prizm Drake London True Silver Auto #309": {
        "Raw": [85.00, 90.00, 92.50, 95.00, 98.00, 100.00, 105.00, 108.00, 110.00, 115.00, 120.00, 125.00],
        "PSA 10": [240.00, 255.00, 265.00, 275.00, 285.00, 300.00, 310.00],
        "PSA 9": [125.00, 130.00, 135.00, 140.00, 145.00, 150.00, 155.00],
        "BGS 9.5": [175.00, 185.00, 190.00, 200.00],
        "SGC 10": [195.00, 205.00, 215.00, 225.00],
    },
    "2024 Panini Prizm Michael Penix Jr. True Silver Auto #341": {
        "Raw": [165.00, 175.00, 180.00, 185.00, 190.00, 195.00, 200.00, 205.00, 210.00, 220.00, 225.00, 235.00, 245.00],
        "PSA 10": [430.00, 450.00, 465.00, 480.00, 500.00, 525.00],
        "PSA 9": [220.00, 230.00, 240.00, 245.00, 255.00, 265.00],
        "BGS 9.5": [310.00, 325.00, 340.00, 355.00],
        "SGC 10": [340.00, 355.00, 370.00, 385.00],
    },
    "2021 Panini Prizm Kyle Pitts True Silver Auto #334": {
        "Raw": [58.00, 62.00, 65.00, 68.00, 70.00, 72.00, 75.00, 78.00, 80.00, 85.00, 90.00],
        "PSA 10": [165.00, 175.00, 180.00, 185.00, 195.00, 205.00],
        "PSA 9": [85.00, 88.00, 92.00, 95.00, 100.00, 105.00, 110.00],
        "BGS 9.5": [120.00, 125.00, 132.00, 140.00],
        "SGC 10": [130.00, 138.00, 145.00, 150.00],
    },
}


# ---------------------------------------------------------------------------
# Core Valuation & Friction Helper Functions
# ---------------------------------------------------------------------------
def compute_comp_stats(sales_list: list[float]) -> dict:
    """Calculate count, 30-day median, and 25th-percentile conservative floor."""
    if not sales_list:
        return {"count": 0, "median": 0.0, "floor_25": 0.0}
    series = pd.Series(sales_list, dtype=float)
    return {
        "count": int(series.count()),
        "median": float(series.median()),
        "floor_25": float(series.quantile(0.25)),
    }


def evaluate_standard_path(
    median_price: float,
    floor_price: float,
    target_roi_decimal: float,
    include_grading: bool = False,
) -> dict:
    """
    Evaluate Path A (Raw-to-Raw), Path B (Raw-to-PSA 10), or Path C (Slab-to-Slab).
    Formula from Spec:
      Net Payout = (30-Day Median * (1 - 0.1325)) - 4.50 [- 47.00 if Path B]
      Max All-In Buy Price = Net Payout / (1 + Target ROI)
    """
    grading_cost = PSA_GRADING_COST if include_grading else 0.0

    # Primary Median Valuation Math
    ebay_fee_median = median_price * EBAY_FEE_RATE
    net_payout_median = (median_price * (1.0 - EBAY_FEE_RATE)) - OUTBOUND_SHIPPING - grading_cost
    max_buy_price = net_payout_median / (1.0 + target_roi_decimal)
    expected_profit_at_max_buy = net_payout_median - max_buy_price

    # Downside Stress Test (25th-Percentile Floor) Math
    ebay_fee_floor = floor_price * EBAY_FEE_RATE
    net_payout_floor = (floor_price * (1.0 - EBAY_FEE_RATE)) - OUTBOUND_SHIPPING - grading_cost
    floor_stress_profit_loss = net_payout_floor - max_buy_price

    return {
        "median": median_price,
        "floor_25": floor_price,
        "ebay_fee_median": ebay_fee_median,
        "shipping_cost": OUTBOUND_SHIPPING,
        "grading_cost": grading_cost,
        "net_payout": net_payout_median,
        "max_buy": max_buy_price,
        "expected_profit": expected_profit_at_max_buy,
        "ebay_fee_floor": ebay_fee_floor,
        "net_payout_floor": net_payout_floor,
        "floor_profit_loss": floor_stress_profit_loss,
    }


def evaluate_psa9_bailout(psa9_median: float, path_b_max_buy: float) -> dict:
    """
    PSA 9 Bailout Check (Path B only):
      Deduct 13.25% fees, $4.50 mailer, and $47.00 PSA cost from 30-day PSA 9 Median.
      Display exact Net Profit/Loss if bought at Path B Max Buy and graded a PSA 9,
      plus zero-risk breakeven buy cap (= PSA 9 Net Payout).
    """
    ebay_fee_psa9 = psa9_median * EBAY_FEE_RATE
    psa9_net_payout = (psa9_median * (1.0 - EBAY_FEE_RATE)) - OUTBOUND_SHIPPING - PSA_GRADING_COST
    bailout_profit_loss = psa9_net_payout - path_b_max_buy
    breakeven_buy_cap = psa9_net_payout

    return {
        "psa9_median": psa9_median,
        "ebay_fee_psa9": ebay_fee_psa9,
        "psa9_net_payout": psa9_net_payout,
        "bailout_profit_loss": bailout_profit_loss,
        "breakeven_buy_cap": breakeven_buy_cap,
    }


def parse_price_list(raw_text: str) -> list[float]:
    """Parse comma, space, or newline separated dollar prices into a float list."""
    cleaned = raw_text.replace("$", "")
    matches = re.findall(r"\d+(?:\.\d+)?", cleaned)
    return [float(m) for m in matches if float(m) > 0]


# ---------------------------------------------------------------------------
# Sidebar Controls — Brand Logo, Margin Control & Data Source Mode
# ---------------------------------------------------------------------------
with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width="stretch")
    else:
        st.title("🟣 THE CIPHER")

    st.caption("THE UNDERGROUND VAULT • COMP & HEIST CALCULATOR")
    st.divider()

    st.subheader("1. Margin Control")
    target_roi_pct = st.slider(
        "Target ROI %",
        min_value=5,
        max_value=100,
        value=25,
        step=1,
        help="Default: 25%. Adjusts Max All-In Buy Price across all paths on the fly.",
    )
    target_roi_decimal = target_roi_pct / 100.0

    st.divider()
    st.subheader("2. Data Source Mode")
    data_mode = st.radio(
        "30-Day Comps Source",
        options=[
            "Sandbox Targets (Falcons Prizm)",
            "Manual / Paste Comps (130point / eBay)",
            "eBay API (Pending Account Approval)",
        ],
        index=0,
    )

    st.divider()
    st.subheader("Fixed Friction Rules")
    st.markdown(
        f"""
        - **eBay Final Value Fee:** {EBAY_FEE_RATE * 100:.2f}%
        - **Outbound Shipping & Supplies:** \\${OUTBOUND_SHIPPING:.2f}
        - **PSA All-In Grading (Path B):** \\${PSA_GRADING_COST:.2f}
        """
    )

# ---------------------------------------------------------------------------
# Main Header & Input Section (Matches villeinuscards.com Aesthetic)
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div>
        <span class="vault-pill">THE UNDERGROUND VAULT • LOUISVILLE, KY • COMP &amp; HEIST CALCULATOR</span>
        <h1 class="brand-hero-title">THE CIPHER — VILLE-IN-US CARDS</h1>
        <p class="brand-subtitle">
            30-Day Comp Intel &amp; Max Buy Targets built for <b>The Ville-Ins</b>.
            30-Day Median Anchors, 25th-Percentile Floor Stress Tests, and Zero-Risk PSA 9 Bailout Math.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if data_mode == "eBay API (Pending Account Approval)":
    st.info(
        "⏳ **eBay Developer API Status: Holding Pattern**\n\n"
        "Once your eBay Developer account is approved, drop your **App ID (Client ID)** and "
        "**Cert ID (Client Secret)** below and The Cipher will pull 30-day settled comps automatically. "
        "In the meantime, switch the sidebar to **Sandbox Targets** or **Manual / Paste Comps** to run deals right now!"
    )
    col_key1, col_key2 = st.columns(2)
    with col_key1:
        st.text_input("eBay App ID (Client ID)", placeholder="Pending eBay approval...", disabled=True)
    with col_key2:
        st.text_input("eBay Cert ID (Client Secret)", type="password", placeholder="Pending eBay approval...", disabled=True)
    st.stop()

# Select Card & Listing Condition
if data_mode == "Sandbox Targets (Falcons Prizm)":
    col_card, col_cond = st.columns([2.2, 1])
    with col_card:
        selected_card_title = st.selectbox(
            "Select Target Card (Panini Prizm True Silver Auto Sandbox — Sample Comps)",
            options=list(SANDBOX_CARDS.keys()),
        )
    with col_cond:
        detected_condition = st.selectbox(
            "Listing Condition (Auto-Routes Evaluation Path)",
            options=["Raw", "PSA 10", "PSA 9", "BGS 9.5", "SGC 10"],
            index=0,
        )
    card_sales_data = SANDBOX_CARDS[selected_card_title]

else:
    # Manual / Paste Comps Mode so user can use the tool immediately before eBay API arrives
    col_card, col_cond = st.columns([2.2, 1])
    with col_card:
        selected_card_title = st.text_input(
            "Card Title / Listing Name",
            value="2023 Panini Prizm Bijan Robinson True Silver Auto #305",
        )
    with col_cond:
        detected_condition = st.selectbox(
            "Listing Condition (Auto-Routes Evaluation Path)",
            options=["Raw", "PSA 10", "PSA 9", "BGS 9.5", "SGC 10"],
            index=0,
        )

    st.markdown("##### Paste 30-Day Settled Sold Prices (comma or space separated)")
    if detected_condition == "Raw":
        mcol1, mcol2, mcol3 = st.columns(3)
        with mcol1:
            raw_input_str = st.text_area(
                "30-Day Raw Sold Prices ($)",
                value="155, 165, 170, 175, 180, 185, 195",
                height=90,
            )
        with mcol2:
            psa10_input_str = st.text_area(
                "30-Day PSA 10 Sold Prices ($)",
                value="390, 410, 425, 440, 460",
                height=90,
            )
        with mcol3:
            psa9_input_str = st.text_area(
                "30-Day PSA 9 Sold Prices ($)",
                value="200, 210, 215, 225, 235",
                height=90,
            )
        card_sales_data = {
            "Raw": parse_price_list(raw_input_str),
            "PSA 10": parse_price_list(psa10_input_str),
            "PSA 9": parse_price_list(psa9_input_str),
        }
    else:
        slab_input_str = st.text_area(
            f"30-Day {detected_condition} Sold Prices ($)",
            value="390, 410, 425, 440, 460",
            height=90,
        )
        card_sales_data = {
            detected_condition: parse_price_list(slab_input_str),
        }

# ---------------------------------------------------------------------------
# TIER 1 — Default Clean Snapshot (Always Visible)
# ---------------------------------------------------------------------------
st.subheader("⚡ Tier 1 — Valuation & Buy Ceiling Snapshot")

if detected_condition == "Raw":
    raw_stats = compute_comp_stats(card_sales_data.get("Raw", []))
    psa10_stats = compute_comp_stats(card_sales_data.get("PSA 10", []))
    psa9_stats = compute_comp_stats(card_sales_data.get("PSA 9", []))

    # Header Metadata Banner
    st.markdown(
        f"""
        <div class="comp-metadata-bar">
            <b>TARGET CARD:</b> {selected_card_title}<br>
            <b>DETECTED CONDITION:</b> <span style="color:#f43f5e;font-weight:700;">RAW (UN-GRADED)</span> &nbsp;&bull;&nbsp;
            <b>30-DAY LIQUIDITY:</b> <span style="color:#c084fc;font-weight:700;">{raw_stats['count']} raw sales | {psa10_stats['count']} PSA 10 sales | {psa9_stats['count']} PSA 9 sales</span> &nbsp;&bull;&nbsp;
            <b>TARGET ROI:</b> <span style="color:#4ade80;font-weight:700;">{target_roi_pct}%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    path_a = evaluate_standard_path(
        median_price=raw_stats["median"],
        floor_price=raw_stats["floor_25"],
        target_roi_decimal=target_roi_decimal,
        include_grading=False,
    )
    path_b = evaluate_standard_path(
        median_price=psa10_stats["median"],
        floor_price=psa10_stats["floor_25"],
        target_roi_decimal=target_roi_decimal,
        include_grading=True,
    )
    bailout_9 = evaluate_psa9_bailout(
        psa9_median=psa9_stats["median"],
        path_b_max_buy=path_b["max_buy"],
    )

    col_path_a, col_path_b = st.columns(2)

    # --- PATH A SUMMARY BLOCK ---
    with col_path_a:
        with st.container(border=True):
            st.markdown("### 🔄 PATH A — RAW-TO-RAW FLIP")
            st.caption("Buy Raw -> Sell Raw (Bypasses $47 PSA grading fee)")

            m1, m2 = st.columns(2)
            m1.metric("30-Day Raw Median", f"${path_a['median']:,.2f}")
            m2.metric("25th-Pct Conservative Floor", f"${path_a['floor_25']:,.2f}")

            m3, m4 = st.columns(2)
            m3.metric("Net Payout (After Fees/Ship)", f"${path_a['net_payout']:,.2f}")
            m4.metric(
                f"Max All-In Buy ({target_roi_pct}% ROI)",
                f"${path_a['max_buy']:,.2f}",
                delta=f"+${path_a['expected_profit']:,.2f} Est. Net Profit",
            )

            # TIER 2 — Clickable Arithmetic Breakdown (Path A)
            with st.expander("🔍 Click to Open Tier 2 — Arithmetic Breakdown & Floor Stress Test (Path A)"):
                st.markdown("#### 1. Net Payout & Max Buy Price Math")
                st.markdown(
                    f"""
                    - **30-Day Raw Median Anchor:** \\${path_a['median']:,.2f} ({raw_stats['count']} sales)
                    - **Less eBay Final Value Fee (13.25%):** -\\${path_a['ebay_fee_median']:,.2f}
                    - **Less Outbound Bubble Mailer & Supplies:** -\\${path_a['shipping_cost']:,.2f}
                    - **Equals Net Payout:** **\\${path_a['net_payout']:,.2f}**
                    - **ROI Divisor (`1 + {target_roi_decimal:.2f}`):** \\${path_a['net_payout']:,.2f} / {1 + target_roi_decimal:.2f} = **\\${path_a['max_buy']:,.2f} Max All-In Buy**
                    """
                )
                st.markdown("#### 2. 25th-Percentile Floor Stress Test")
                floor_status = "PROFIT" if path_a["floor_profit_loss"] >= 0 else "LOSS"
                st.markdown(
                    f"""
                    *If you buy at the Max All-In Buy (\\${path_a['max_buy']:,.2f}) and are forced to exit at the 25th-percentile floor (\\${path_a['floor_25']:,.2f}):*
                    - **Floor Sale Price:** \\${path_a['floor_25']:,.2f}
                    - **Less eBay Fee (13.25%) & Shipping (\\$4.50):** -\\${path_a['ebay_fee_floor'] + path_a['shipping_cost']:,.2f}
                    - **Floor Net Payout:** \\${path_a['net_payout_floor']:,.2f}
                    - **Worst-Case Net {floor_status}:** **\\${path_a['floor_profit_loss']:+,.2f}**
                    """
                )

    # --- PATH B SUMMARY BLOCK ---
    with col_path_b:
        with st.container(border=True):
            st.markdown("### 💎 PATH B — RAW-TO-PSA 10 GRADE")
            st.caption("Buy Raw -> Grade with PSA ($47.00 all-in) -> Sell PSA 10")

            b1, b2 = st.columns(2)
            b1.metric("30-Day PSA 10 Median", f"${path_b['median']:,.2f}")
            b2.metric("25th-Pct Conservative Floor", f"${path_b['floor_25']:,.2f}")

            b3, b4 = st.columns(2)
            b3.metric("Net Payout (After Fees/Ship/PSA)", f"${path_b['net_payout']:,.2f}")
            b4.metric(
                f"Max All-In Buy ({target_roi_pct}% ROI)",
                f"${path_b['max_buy']:,.2f}",
                delta=f"+${path_b['expected_profit']:,.2f} Est. Net Profit",
            )

            st.divider()
            st.markdown("#### 🛡️ PSA 9 BAILOUT CHECK")
            bail_col1, bail_col2, bail_col3 = st.columns(3)
            bail_col1.metric("30-Day PSA 9 Median", f"${bailout_9['psa9_median']:,.2f}")
            bail_col2.metric(
                "PSA 9 Net Profit / Loss",
                f"${bailout_9['bailout_profit_loss']:+,.2f}",
                delta="If bought at Path B Max Buy",
                delta_color="normal" if bailout_9["bailout_profit_loss"] >= 0 else "inverse",
            )
            bail_col3.metric(
                "Zero-Risk Breakeven Buy Cap",
                f"${bailout_9['breakeven_buy_cap']:,.2f}",
                help="Max price you can pay for the Raw card so that even a PSA 9 grade breaks 100% even after all PSA & eBay fees.",
            )

            # TIER 2 — Clickable Arithmetic Breakdown (Path B)
            with st.expander("🔍 Click to Open Tier 2 — Arithmetic Breakdown & Floor Stress Test (Path B)"):
                st.markdown("#### 1. PSA 10 Net Payout & Max Buy Price Math")
                st.markdown(
                    f"""
                    - **30-Day PSA 10 Median Anchor:** \\${path_b['median']:,.2f} ({psa10_stats['count']} sales)
                    - **Less eBay Final Value Fee (13.25%):** -\\${path_b['ebay_fee_median']:,.2f}
                    - **Less Outbound Bubble Mailer & Supplies:** -\\${path_b['shipping_cost']:,.2f}
                    - **Less PSA All-In Grading Cost:** -\\${path_b['grading_cost']:,.2f} (\\$39.99 Value + \\$7.01 insured ship/prep)
                    - **Equals Net Payout:** **\\${path_b['net_payout']:,.2f}**
                    - **ROI Divisor (`1 + {target_roi_decimal:.2f}`):** \\${path_b['net_payout']:,.2f} / {1 + target_roi_decimal:.2f} = **\\${path_b['max_buy']:,.2f} Max All-In Buy**
                    """
                )
                st.markdown("#### 2. PSA 9 Bailout Arithmetic")
                st.markdown(
                    f"""
                    - **30-Day PSA 9 Median:** \\${bailout_9['psa9_median']:,.2f} ({psa9_stats['count']} sales)
                    - **Less eBay Fee (13.25%):** -\\${bailout_9['ebay_fee_psa9']:,.2f}
                    - **Less Mailer (\\$4.50) & PSA Grading (\\$47.00):** -\\$51.50
                    - **PSA 9 Net Payout (Zero-Risk Breakeven Buy Cap):** **\\${bailout_9['breakeven_buy_cap']:,.2f}**
                    - **Net Result if Bought at Path B Max Buy (\\${path_b['max_buy']:,.2f}):** **\\${bailout_9['bailout_profit_loss']:+,.2f}**
                    """
                )
                st.markdown("#### 3. 25th-Percentile PSA 10 Floor Stress Test")
                floor_b_status = "PROFIT" if path_b["floor_profit_loss"] >= 0 else "LOSS"
                st.markdown(
                    f"""
                    *If you buy at Path B Max Buy (\\${path_b['max_buy']:,.2f}), hit a PSA 10, and are forced to exit at the 25th-percentile PSA 10 floor (\\${path_b['floor_25']:,.2f}):*
                    - **PSA 10 Floor Net Payout:** \\${path_b['net_payout_floor']:,.2f}
                    - **Worst-Case PSA 10 Net {floor_b_status}:** **\\${path_b['floor_profit_loss']:+,.2f}**
                    """
                )

else:
    # --- PATH C — ANY-GRADE SLAB-TO-SLAB FLIP ---
    slab_sales = card_sales_data.get(detected_condition, [])
    slab_stats = compute_comp_stats(slab_sales)

    st.markdown(
        f"""
        <div class="comp-metadata-bar">
            <b>TARGET CARD:</b> {selected_card_title}<br>
            <b>DETECTED CONDITION / GRADE:</b> <span style="color:#f43f5e;font-weight:700;">{detected_condition} (GRADED SLAB)</span> &nbsp;&bull;&nbsp;
            <b>30-DAY LIQUIDITY:</b> <span style="color:#c084fc;font-weight:700;">{slab_stats['count']} {detected_condition} sales</span> &nbsp;&bull;&nbsp;
            <b>TARGET ROI:</b> <span style="color:#4ade80;font-weight:700;">{target_roi_pct}%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    path_c = evaluate_standard_path(
        median_price=slab_stats["median"],
        floor_price=slab_stats["floor_25"],
        target_roi_decimal=target_roi_decimal,
        include_grading=False,
    )

    with st.container(border=True):
        st.markdown(f"### 🏆 PATH C — SLAB-TO-SLAB FLIP ({detected_condition})")
        st.caption(f"Buy {detected_condition} Slab -> Sell {detected_condition} Slab (Grading cost bypassed: $0.00)")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"30-Day {detected_condition} Median", f"${path_c['median']:,.2f}")
        c2.metric("25th-Pct Conservative Floor", f"${path_c['floor_25']:,.2f}")
        c3.metric("Net Payout (After Fees/Ship)", f"${path_c['net_payout']:,.2f}")
        c4.metric(
            f"Max All-In Buy ({target_roi_pct}% ROI)",
            f"${path_c['max_buy']:,.2f}",
            delta=f"+${path_c['expected_profit']:,.2f} Est. Net Profit",
        )

        # TIER 2 — Clickable Arithmetic Breakdown (Path C)
        with st.expander(f"🔍 Click to Open Tier 2 — Arithmetic Breakdown & Floor Stress Test (Path C: {detected_condition})"):
            st.markdown("#### 1. Net Payout & Max Buy Price Math")
            st.markdown(
                f"""
                - **30-Day {detected_condition} Median Anchor:** \\${path_c['median']:,.2f} ({slab_stats['count']} sales)
                - **Less eBay Final Value Fee (13.25%):** -\\${path_c['ebay_fee_median']:,.2f}
                - **Less Outbound Bubble Mailer & Supplies:** -\\${path_c['shipping_cost']:,.2f}
                - **Grading Cost:** \\$0.00 (Already slabbed)
                - **Equals Net Payout:** **\\${path_c['net_payout']:,.2f}**
                - **ROI Divisor (`1 + {target_roi_decimal:.2f}`):** \\${path_c['net_payout']:,.2f} / {1 + target_roi_decimal:.2f} = **\\${path_c['max_buy']:,.2f} Max All-In Buy**
                """
            )
            st.markdown("#### 2. 25th-Percentile Floor Stress Test")
            floor_c_status = "PROFIT" if path_c["floor_profit_loss"] >= 0 else "LOSS"
            st.markdown(
                f"""
                *If you buy at the Max All-In Buy (\\${path_c['max_buy']:,.2f}) and are forced to exit at the 25th-percentile floor (\\${path_c['floor_25']:,.2f}):*
                - **Floor Sale Price:** \\${path_c['floor_25']:,.2f}
                - **Less eBay Fee (13.25%) & Shipping (\\$4.50):** -\\${path_c['ebay_fee_floor'] + path_c['shipping_cost']:,.2f}
                - **Floor Net Payout:** \\${path_c['net_payout_floor']:,.2f}
                - **Worst-Case Net {floor_c_status}:** **\\${path_c['floor_profit_loss']:+,.2f}**
                """
            )
