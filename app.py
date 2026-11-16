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
    @import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:ital,wght@1,700&family=Metal+Mania&family=Orbitron:wght@800;900&display=swap');

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

    /* Brand Gradient Hero Title (Matches VILLE-IN-US CARDS Logo Font & Colors) */
    .brand-hero-title {
        display: inline-block;
        font-family: 'Orbitron', 'Russo One', 'Arial Black', sans-serif !important;
        font-size: clamp(1.9rem, 3.6vw, 2.75rem);
        font-weight: 900 !important;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        background: linear-gradient(180deg, #e11d48 12%, #9333ea 52%, #be123c 92%);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        -webkit-text-stroke: 1.5px #c084fc;
        paint-order: stroke fill;
        filter: drop-shadow(0 0 12px rgba(168, 85, 247, 0.55)) drop-shadow(0 0 24px rgba(225, 29, 72, 0.3));
        margin: 2px 0 8px 0;
        line-height: 1.2;
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
# Restricted Underground Vault PIN Gate (PIN: 3127 or Token Handoff)
# ---------------------------------------------------------------------------
if "vault_unlocked" not in st.session_state:
    st.session_state.vault_unlocked = False

if st.query_params.get("vault") == "viu5aba":
    st.session_state.vault_unlocked = True
    st.query_params.clear()

if not st.session_state.vault_unlocked:
    _, col_gate, _ = st.columns([1, 1.3, 1])
    with col_gate:
        st.write("")
        st.write("")
        with st.container(border=True):
            if LOGO_PATH.exists():
                st.image(str(LOGO_PATH), width="stretch")
            st.markdown(
                """
                <div style="text-align:center; padding: 6px 0 10px 0;">
                    <span class="vault-pill">RESTRICTED VAULT ACCESS</span>
                    <h2 class="brand-hero-title" style="font-size:1.75rem;">🔒 THE CIPHER</h2>
                    <p style="color:#94a3b8; font-size:0.9rem; margin-top:4px;">
                        Authorized Ville-Ins Only. Enter 4-Digit Vault PIN:
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            entered_pin = st.text_input(
                "Vault Access PIN",
                type="password",
                max_chars=4,
                placeholder="••••",
                label_visibility="collapsed",
            )
            unlock_clicked = st.button("🔓 UNLOCK THE CIPHER", width="stretch", type="primary")
            if unlock_clicked or entered_pin:
                if entered_pin.strip() == "3127":
                    st.session_state.vault_unlocked = True
                    st.rerun()
                else:
                    st.error("🚨 ACCESS DENIED — Invalid Vault PIN.")
    st.stop()


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
    if "target_roi_pct" not in st.session_state:
        st.session_state.target_roi_pct = 25

    def _step_roi(delta: int) -> None:
        st.session_state.target_roi_pct = max(5, min(100, st.session_state.target_roi_pct + delta))

    target_roi_pct = st.slider(
        "Target ROI %",
        min_value=5,
        max_value=100,
        step=1,
        key="target_roi_pct",
        help="Default: 25%. Drag the slider or use the -1% / +1% buttons below for exact 1% steps.",
    )
    btn_minus, btn_plus = st.columns(2)
    with btn_minus:
        st.button("➖ 1%", on_click=_step_roi, args=(-1,), width="stretch")
    with btn_plus:
        st.button("➕ 1%", on_click=_step_roi, args=(1,), width="stretch")

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
        <div style="margin: 6px 0 10px 0; max-width: 480px;">
            <img src="data:image/png;base64,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" alt="THE CIPHER" style="width:100%; max-width:460px; height:auto; display:block;" />
        </div>
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
