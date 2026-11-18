import base64
import hmac
import os
from pathlib import Path
import re
import time
import pandas as pd
import requests
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
    """Calculate count, 30-day median, 30-day mean (average), 25th-percentile floor, high, and low."""
    if not sales_list:
        return {"count": 0, "median": 0.0, "mean": 0.0, "floor_25": 0.0, "high": 0.0, "low": 0.0}
    series = pd.Series(sales_list, dtype=float)
    return {
        "count": int(series.count()),
        "median": float(series.median()),
        "mean": float(series.mean()),
        "floor_25": float(series.quantile(0.25)),
        "high": float(series.max()),
        "low": float(series.min()),
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


def get_secret_key(env_name: str) -> str:
    """Read an API key from environment variable or Streamlit secrets without hardcoding in source."""
    val = os.environ.get(env_name, "").strip()
    if val:
        return val
    try:
        return str(st.secrets.get(env_name, "")).strip()
    except Exception:
        return ""

JUNK_TITLE_PATTERNS = re.compile(
    r"\b(lot\s+of|card\s+lot|player\s+lot|team\s+lot|box\s+break|case\s+break|"
    r"pick\s+your|you\s+pick|u\s+pick|digital\s+card|reprint|custom\s+card|novelty)\b",
    re.IGNORECASE,
)

INSERT_AND_OTHER_SET_WORDS = [
    "draft",
    "flashback",
    "emergent",
    "portals",
    "prizm break",
    "fireworks",
    "hype",
    "prizmatic",
    "instant impact",
    "premier jersey",
    "rookie gear",
    "variation",
    "select",
    "mosaic",
    "optic",
    "donruss",
    "rookies & stars",
    "rookies and stars",
    "chronicles",
    "contenders",
    "illusions",
    "zenith",
    "score",
    "prestige",
    "absolute",
]

AUTO_PATTERN = re.compile(r"\b(auto|autograph|autographs|signed|on-card\s+auto|au)\b", re.IGNORECASE)


def classify_sale_condition(item: dict) -> str:
    """Classify a sale record from The Card API into Raw, PSA 10, PSA 9, BGS 9.5, SGC 10, or Other Slab."""
    grader = str(item.get("grader") or "").strip().upper()
    grade_raw = str(item.get("grade") or "").strip()
    title = str(item.get("title") or "").upper()

    if grade_raw.endswith(".0"):
        grade_raw = grade_raw[:-2]

    if grader == "PSA" and grade_raw == "10":
        return "PSA 10"
    if grader == "PSA" and grade_raw == "9":
        return "PSA 9"
    if grader in ("BGS", "BVG", "BECKETT") and grade_raw == "9.5":
        return "BGS 9.5"
    if grader == "SGC" and grade_raw == "10":
        return "SGC 10"
    if grader and grade_raw:
        return f"{grader} {grade_raw}"

    # Fallback title inspection (handles emojis/words between grader & grade, e.g. 'PSA 💎 MINT 10')
    if re.search(r"\bPSA\b[^\d]{0,18}\b10\b", title):
        return "PSA 10"
    if re.search(r"\bPSA\b[^\d]{0,18}\b9\b(?!\.5)", title):
        return "PSA 9"
    if re.search(r"\b(?:BGS|BECKETT|BVG)\b[^\d]{0,18}\b9\.5\b", title):
        return "BGS 9.5"
    if re.search(r"\bSGC\b[^\d]{0,18}\b10\b", title):
        return "SGC 10"
    if re.search(r"\b(?:PSA|BGS|BECKETT|SGC|CGC)\b[^\d]{0,15}\b\d+(?:\.\d+)?\b", title):
        return "Other Slab"

    return "Raw"


@st.cache_data(ttl=1800, show_spinner=False)
def _raw_cardapi_sales(query_clean: str, api_key: str, limit: int) -> dict:
    """Cached raw HTTP call to The Card API so toggling UI filters uses 0 extra quota."""
    resp = requests.get(
        "https://thecardapi.com/api/v1/market/sales",
        params={"q": query_clean, "limit": limit},
        headers={"x-market-api-key": api_key.strip(), "accept": "application/json"},
        timeout=15,
    )
    if resp.status_code != 200:
        return {"ok": False, "error": f"API returned HTTP {resp.status_code}: {resp.text[:200]}", "payload": {}}
    return {"ok": True, "error": "", "payload": resp.json()}


def fetch_live_cardapi_comps(
    query_str: str,
    api_key: str,
    exclude_inserts: bool = True,
    auto_filter: str = "All",
    include_best_offer_ask: bool = True,
    limit: int = 100,
) -> dict:
    """Query The Card API (/api/v1/market/sales) and return structured records with photos."""
    records: list[dict] = []

    if not query_str.strip():
        return {"ok": False, "error": "Enter a card search query.", "records": records, "total_matched": 0}

    try:
        raw_res = _raw_cardapi_sales(query_str.strip().lower(), api_key.strip(), limit)
        if not raw_res["ok"]:
            return {
                "ok": False,
                "error": raw_res["error"],
                "records": records,
                "total_matched": 0,
            }

        payload = raw_res["payload"]
        raw_items = payload.get("data", [])
        total_matched = (payload.get("pagination") or {}).get("total", len(raw_items))

        # Parse required search tokens so every word typed must appear in the listing title
        raw_tokens = [t.strip().lower() for t in query_str.split() if t.strip()]
        required_tokens = [t.lstrip("#") for t in raw_tokens if not t.startswith("-")]
        excluded_tokens = [t[1:] for t in raw_tokens if t.startswith("-") and len(t) > 1]

        for item in raw_items:
            title = str(item.get("title") or "")
            title_lower = title.lower()
            if JUNK_TITLE_PATTERNS.search(title):
                continue
            if any(ex in title_lower for ex in excluded_tokens):
                continue

            # Auto-block inserts, variations, and other sets unless the user searched for them
            if exclude_inserts:
                blocked_by_insert = False
                for w in INSERT_AND_OTHER_SET_WORDS:
                    if w in title_lower and not any(w in req for req in required_tokens):
                        blocked_by_insert = True
                        break
                if blocked_by_insert:
                    continue

            # Check Auto vs Non-Auto filter (both title regex and structured features list)
            features_list = [str(f).lower() for f in (item.get("features") or [])]
            is_auto = bool(AUTO_PATTERN.search(title)) or any("auto" in f for f in features_list)
            if auto_filter == "Non-Auto Only" and is_auto:
                continue
            if auto_filter == "Autographs Only" and not is_auto:
                continue

            if not all(tok in title_lower for tok in required_tokens):
                continue

            price_val = item.get("price") if item.get("price") is not None else item.get("price_usd")
            listing_type_raw = str(item.get("listing_type") or "")
            if price_val is None and include_best_offer_ask and listing_type_raw == "best_offer":
                price_val = item.get("original_price")

            try:
                price = float(price_val)
            except (TypeError, ValueError):
                continue
            if price <= 0:
                continue

            cond = classify_sale_condition(item)
            ship_val = item.get("shipping_price")
            ship_price = float(ship_val) if ship_val is not None else 0.0
            img_url = str(item.get("thumbnail_url") or item.get("image_url") or "")

            type_label = listing_type_raw.replace("_", " ").title()
            if listing_type_raw == "best_offer" and item.get("price") is None:
                type_label = "Best Offer (Ask)"

            records.append(
                {
                    "Include": True,
                    "Photo": img_url,
                    "Condition": cond,
                    "Sold Price ($)": price,
                    "Sale Date": str(item.get("sale_date") or ""),
                    "Card #": str(item.get("card_number") or ""),
                    "Type": type_label,
                    "Source": f"TheCardAPI ({item.get('platform') or 'eBay'})",
                    "Listing Title": title,
                    "Link": str(item.get("listing_url") or ""),
                    "_item_id": str(item.get("id") or title),
                }
            )

        return {
            "ok": True,
            "error": "",
            "records": records,
            "total_matched": total_matched,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
            "records": records,
            "total_matched": 0,
        }


@st.cache_data(ttl=1800, show_spinner=False)
def _raw_compsniper_house(slug: str, query_clean: str, api_key: str) -> list[dict]:
    """Cached raw HTTP call per CompSniper graded auction house so UI filter toggles cost 0 credits."""
    resp = requests.get(
        f"https://api.compsniper.com/v1/{slug}/sold",
        params={"keyword": query_clean},
        headers={"Authorization": f"Bearer {api_key.strip()}", "Accept": "application/json"},
        timeout=20,
    )
    if resp.status_code != 200:
        return []
    return resp.json().get("items", [])


def fetch_live_graded_auctions(
    query_str: str,
    api_key: str,
    exclude_inserts: bool = True,
    auto_filter: str = "All",
) -> dict:
    """Query CompSniper Graded Card Auction Houses (Goldin, Fanatics Collect, MySlabs, Pristine)."""
    records: list[dict] = []
    if not query_str.strip() or not api_key.strip():
        return {"ok": False, "error": "", "records": records}

    q_clean = query_str.strip().lower()
    raw_tokens = [t.strip().lower() for t in query_str.split() if t.strip()]
    required_tokens = [t.lstrip("#") for t in raw_tokens if not t.startswith("-")]
    excluded_tokens = [t[1:] for t in raw_tokens if t.startswith("-") and len(t) > 1]

    houses = [
        ("goldin", "Goldin Auctions"),
        ("fanatics", "Fanatics Collect"),
        ("myslabs", "MySlabs"),
        ("pristine", "Pristine Auction"),
    ]
    for slug, label in houses:
        try:
            items = _raw_compsniper_house(slug, q_clean, api_key.strip())
            for item in items:
                title = str(item.get("title") or "")
                title_lower = title.lower()
                if JUNK_TITLE_PATTERNS.search(title):
                    continue
                if any(ex in title_lower for ex in excluded_tokens):
                    continue
                if exclude_inserts:
                    if any(w in title_lower and not any(w in req for req in required_tokens) for w in INSERT_AND_OTHER_SET_WORDS):
                        continue
                is_auto = bool(AUTO_PATTERN.search(title))
                if auto_filter == "Non-Auto Only" and is_auto:
                    continue
                if auto_filter == "Autographs Only" and not is_auto:
                    continue
                if not all(tok in title_lower for tok in required_tokens):
                    continue

                try:
                    price = float(item.get("price") or 0)
                except (TypeError, ValueError):
                    continue
                if price <= 0:
                    continue

                grader = str(item.get("gradingService") or "").upper()
                grade = str(item.get("grade") or "")
                cond = classify_sale_condition({"title": title, "grader": grader, "grade": grade})
                sold_at = str(item.get("soldAt") or "")[:10]
                cert_num = str(item.get("certNumber") or "")
                card_num_match = re.search(r"#\s*([A-Za-z0-9-]+)", title)
                card_num = card_num_match.group(1) if card_num_match else (f"Cert #{cert_num}" if cert_num else "")

                records.append(
                    {
                        "Include": True,
                        "Photo": str(item.get("imageUrl") or ""),
                        "Condition": cond,
                        "Sold Price ($)": price,
                        "Sale Date": sold_at,
                        "Card #": card_num,
                        "Type": str(item.get("saleType") or "Auction"),
                        "Source": label,
                        "Listing Title": title,
                        "Link": str(item.get("url") or (f"https://www.psacard.com/cert/{cert_num}" if cert_num else "")),
                        "_item_id": f"{slug}_{item.get('saleId') or title}",
                    }
                )
        except Exception:
            continue

    return {"ok": True, "error": "", "records": records}


@st.cache_data(ttl=900, show_spinner=False)
def lookup_psa_cert(cert_num: str, psa_token: str, cs_key: str) -> dict:
    """Query PSA Public API GetByCertNumber and cross-check recent marketplace sales for that Cert #."""
    clean_cert = re.sub(r"\D", "", cert_num or "")
    if not clean_cert:
        return {"ok": False, "error": "Enter a numeric PSA Cert #."}

    psa_data = None
    psa_msg = ""
    if psa_token.strip():
        try:
            r = requests.get(
                f"https://api.psacard.com/publicapi/cert/GetByCertNumber/{clean_cert}",
                headers={
                    "Authorization": f"bearer {psa_token.strip()}",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                },
                timeout=15,
            )
            if r.status_code == 200:
                body = r.json()
                psa_data = body.get("PSACert") or body
            else:
                psa_msg = r.json().get("Message", f"HTTP {r.status_code}")
        except Exception as exc:
            psa_msg = str(exc)

    market_hits: list[dict] = []
    if cs_key.strip():
        try:
            r_eb = requests.get(
                "https://api.compsniper.com/v1/scrape",
                params={"keyword": f"PSA {clean_cert}", "sold": "true", "ebaySite": "ebay.com"},
                headers={"Authorization": f"Bearer {cs_key.strip()}"},
                timeout=15,
            )
            if r_eb.status_code == 200:
                for it in r_eb.json().get("items", [])[:3]:
                    market_hits.append(
                        {
                            "title": it.get("title"),
                            "price": it.get("soldPrice"),
                            "date": it.get("endedAt"),
                            "source": "eBay Sold",
                            "image": it.get("thumbnailUrl"),
                        }
                    )
        except Exception:
            pass

    return {
        "ok": True,
        "cert": clean_cert,
        "psa_data": psa_data,
        "psa_msg": psa_msg,
        "market_hits": market_hits,
        "cert_url": f"https://www.psacard.com/cert/{clean_cert}",
    }


@st.cache_data(ttl=1800, show_spinner=False)
def _raw_compsniper_scrape(query_clean: str, api_key: str) -> dict:
    """Cached raw HTTP call to CompSniper /v1/scrape so toggling UI filters uses 0 extra credits."""
    url = "https://api.compsniper.com/v1/scrape"
    params = {"keyword": query_clean, "sold": "true", "ebaySite": "ebay.com"}
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Accept": "application/json"}

    resp = None
    for attempt in range(3):
        resp = requests.get(url, params=params, headers=headers, timeout=25)
        if resp.status_code in (429, 503) and attempt < 2:
            retry_wait = int(resp.headers.get("Retry-After", "2") or 2)
            time.sleep(min(retry_wait, 5))
            continue
        break

    if resp is None or resp.status_code != 200:
        code = resp.status_code if resp is not None else "N/A"
        body = resp.text[:200] if resp is not None else ""
        return {"ok": False, "error": f"CompSniper HTTP {code}: {body}", "payload": {}}
    return {"ok": True, "error": "", "payload": resp.json()}


def fetch_live_compsniper_comps(
    query_str: str,
    api_key: str,
    exclude_inserts: bool = True,
    auto_filter: str = "All",
    include_best_offer: bool = True,
) -> dict:
    """Query CompSniper API (/v1/scrape?sold=true) for up to 240 sold eBay comps with true Best Offer prices."""
    records: list[dict] = []
    if not query_str.strip():
        return {"ok": False, "error": "Enter a card search query.", "records": records, "total_matched": 0}
    if not api_key.strip():
        return {"ok": False, "error": "Missing COMPSNIPER_API_KEY in secrets/environment.", "records": records, "total_matched": 0}

    try:
        raw_res = _raw_compsniper_scrape(query_str.strip().lower(), api_key.strip())
        if not raw_res["ok"]:
            return {"ok": False, "error": raw_res["error"], "records": records, "total_matched": 0}

        payload = raw_res["payload"]
        raw_items = payload.get("items", [])
        total_matched = payload.get("totalResults") or payload.get("totalItems") or len(raw_items)

        raw_tokens = [t.strip().lower() for t in query_str.split() if t.strip()]
        required_tokens = [t.lstrip("#") for t in raw_tokens if not t.startswith("-")]
        excluded_tokens = [t[1:] for t in raw_tokens if t.startswith("-") and len(t) > 1]

        for item in raw_items:
            title = str(item.get("title") or "")
            title_lower = title.lower()
            if JUNK_TITLE_PATTERNS.search(title):
                continue
            if any(ex in title_lower for ex in excluded_tokens):
                continue

            if exclude_inserts:
                blocked_by_insert = False
                for w in INSERT_AND_OTHER_SET_WORDS:
                    if w in title_lower and not any(w in req for req in required_tokens):
                        blocked_by_insert = True
                        break
                if blocked_by_insert:
                    continue

            is_auto = bool(AUTO_PATTERN.search(title))
            if auto_filter == "Non-Auto Only" and is_auto:
                continue
            if auto_filter == "Autographs Only" and not is_auto:
                continue

            if not all(tok in title_lower for tok in required_tokens):
                continue

            try:
                price = float(item.get("soldPrice") or 0)
            except (TypeError, ValueError):
                continue
            if price <= 0:
                continue

            cond = classify_sale_condition({"title": title})
            img_url = str(item.get("thumbnailUrl") or item.get("fullResThumbnailUrl") or "")

            buy_fmt = str(item.get("buyingFormat") or "")
            if item.get("bestOfferAccepted"):
                if not include_best_offer:
                    continue
                type_label = "Best Offer (Accepted)"
            elif buy_fmt == "auction":
                type_label = f"Auction ({item.get('bidCount') or 0} bids)"
            elif buy_fmt == "buyItNow":
                type_label = "Buy It Now"
            else:
                type_label = "Sold"

            card_num_match = re.search(r"#\s*([A-Za-z0-9-]+)", title)
            card_num = card_num_match.group(1) if card_num_match else ""

            records.append(
                {
                    "Include": True,
                    "Photo": img_url,
                    "Condition": cond,
                    "Sold Price ($)": price,
                    "Sale Date": str(item.get("endedAt") or ""),
                    "Card #": card_num,
                    "Type": type_label,
                    "Source": "CompSniper (eBay)",
                    "Listing Title": title,
                    "Link": str(item.get("url") or ""),
                    "_item_id": str(item.get("itemId") or title),
                }
            )

        return {
            "ok": True,
            "error": "",
            "records": records,
            "total_matched": total_matched,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
            "records": records,
            "total_matched": 0,
        }


@st.cache_data(ttl=6600, show_spinner=False)
def get_ebay_token(app_id: str, cert_id: str) -> str:
    """OAuth client-credentials token for eBay Browse API (valid ~2h)."""
    import base64

    cred = base64.b64encode(f"{app_id}:{cert_id}".encode()).decode()
    r = requests.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        headers={"Authorization": f"Basic {cred}", "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"},
        timeout=20,
    )
    if r.status_code != 200:
        raise RuntimeError(f"eBay auth failed (HTTP {r.status_code}). Check EBAY_APP_ID / EBAY_CERT_ID secrets.")
    return r.json()["access_token"]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_ebay_active_listings(query: str, app_id: str, cert_id: str, sort: str, buy_type: str) -> dict:
    """Active eBay listings via the Browse API (asking prices, not sold)."""
    if not query.strip():
        return {"ok": False, "error": "Enter a search.", "records": []}
    if not app_id or not cert_id:
        return {"ok": False, "error": "Missing EBAY_APP_ID / EBAY_CERT_ID in secrets.", "records": []}
    try:
        token = get_ebay_token(app_id, cert_id)
        params = {"q": query.strip(), "limit": 100, "category_ids": "261328"}
        if sort.startswith("Price"):
            params["sort"] = "price"
        elif sort == "Newly Listed":
            params["sort"] = "newlyListed"
        filters = []
        if buy_type == "Buy It Now only":
            filters.append("buyingOptions:{FIXED_PRICE}")
        elif buy_type == "Auction only":
            filters.append("buyingOptions:{AUCTION}")
        if filters:
            params["filter"] = ",".join(filters)
        r = requests.get(
            "https://api.ebay.com/buy/browse/v1/item_summary/search",
            headers={"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"},
            params=params,
            timeout=20,
        )
        if r.status_code != 200:
            return {"ok": False, "error": f"eBay Browse HTTP {r.status_code}: {r.text[:150]}", "records": []}
        records = []
        for it in r.json().get("itemSummaries", []):
            try:
                price = float(it["price"]["value"])
            except (KeyError, TypeError, ValueError):
                continue
            ship = None
            opts = it.get("shippingOptions") or []
            if opts:
                try:
                    ship = float(opts[0]["shippingCost"]["value"])
                except (KeyError, TypeError, ValueError):
                    ship = None
            records.append(
                {
                    "Photo": (it.get("thumbnailImages") or [{}])[0].get("imageUrl") or (it.get("image") or {}).get("imageUrl", ""),
                    "Price ($)": price,
                    "Ship ($)": ship,
                    "Type": "/".join(it.get("buyingOptions") or []),
                    "Title": it.get("title", ""),
                    "Link": it.get("itemWebUrl", ""),
                }
            )
        return {"ok": True, "error": "", "records": records}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "records": []}


# ---------------------------------------------------------------------------
# Restricted Underground Vault PIN Gate (Server-side secret in VAULT_PIN)
# ---------------------------------------------------------------------------
if "vault_unlocked" not in st.session_state:
    st.session_state.vault_unlocked = False

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
                    <div style="margin: 6px auto 8px auto; max-width: 340px;"><img src="data:image/png;base64,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" alt="THE CIPHER" style="width:100%; max-width:340px; height:auto; display:block; margin:0 auto;" /></div>
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
            import streamlit.components.v1 as components

            components.html(
                """
                <script>
                (function() {
                    try {
                        const doc = window.parent.document;
                        function applyNumericPin() {
                            doc.querySelectorAll('input[type="password"]').forEach((el) => {
                                el.setAttribute('inputmode', 'numeric');
                                el.setAttribute('pattern', '[0-9]*');
                                el.setAttribute('autocomplete', 'one-time-code');
                                el.style.textAlign = 'center';
                                el.style.fontSize = '1.35rem';
                                el.style.letterSpacing = '0.45em';
                            });
                        }
                        applyNumericPin();
                        setTimeout(applyNumericPin, 150);
                        setTimeout(applyNumericPin, 500);
                    } catch (e) {}
                })();
                </script>
                """,
                height=0,
                width=0,
            )
            unlock_clicked = st.button("🔓 UNLOCK THE CIPHER", width="stretch", type="primary")
            if unlock_clicked or entered_pin:
                vault_pin = get_secret_key("VAULT_PIN")
                if not vault_pin:
                    st.error("🚨 Vault PIN is not configured in server secrets (`VAULT_PIN`).")
                elif hmac.compare_digest(entered_pin.strip(), vault_pin):
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
        st.session_state.target_roi_pct = 10

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

    valuation_anchor_mode = st.radio(
        "Primary Valuation Anchor",
        options=["30-Day Median (Spec Default)", "30-Day Average (Mean)"],
        index=0,
        help="Median picks the exact middle sale price (ignores extreme outliers). Average (Mean) adds all sales and divides by count (moves immediately whenever high/low sales are unchecked).",
    )
    anchor_key = "mean" if "Average" in valuation_anchor_mode else "median"
    anchor_label = "Average" if anchor_key == "mean" else "Median"

    st.divider()
    st.subheader("2. Data Source Mode")
    data_mode = st.radio(
        "30-Day Comps Source",
        options=[
            "Live Sold Comps",
            "eBay Live Listings (Buy Side)",
            "Deal Finder",
            "Manual / Paste Comps",
        ],
        index=0,
    )

    st.divider()
    st.subheader("3. PSA Cert # Slab Scanner")
    psa_cert_input = st.text_input(
        "Verify PSA Cert # (e.g. 100855050)",
        placeholder="Enter 8-9 digit Cert #...",
        help="Checks PSA's Public API and cross-searches recent eBay/Auction sales for that exact slab.",
    )
    if psa_cert_input.strip():
        cert_res = lookup_psa_cert(
            psa_cert_input.strip(),
            get_secret_key("PSA_API_TOKEN"),
            get_secret_key("COMPSNIPER_API_KEY"),
        )
        if not cert_res["ok"]:
            st.warning(cert_res["error"])
        else:
            st.markdown(f"🔗 **[Open Official PSA Cert #{cert_res['cert']} Page ↗]({cert_res['cert_url']})**")
            if cert_res["psa_data"]:
                p = cert_res["psa_data"]
                st.success(
                    f"**{p.get('Year', '')} {p.get('Brand', '')} #{p.get('CardNumber', '')}**\n\n"
                    f"Subject: **{p.get('Subject', '')}** ({p.get('Variety', '')})\n\n"
                    f"Grade: **PSA {p.get('CardGrade', '')}** | Pop: **{p.get('TotalPopulation', 'N/A')}** "
                    f"(Higher: {p.get('PopulationHigher', 0)})"
                )
            elif cert_res["psa_msg"]:
                st.caption(f"ℹ️ PSA API Status: {cert_res['psa_msg']}")
            if cert_res["market_hits"]:
                for mh in cert_res["market_hits"]:
                    st.caption(f"💰 **{mh['source']}:** \\${mh['price']} ({mh['date']}) — {mh['title']}")

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

# ---------------------------------------------------------------------------
# Shared Comp + Listing Helpers (used by Comps, Buy Side & Deal Finder modes)
# ---------------------------------------------------------------------------
def gather_merged_comps(
    query: str,
    cs_key: str,
    tca_key: str,
    exclude_inserts: bool,
    auto_filter: str,
    include_bo: bool,
    include_auctions: bool,
) -> tuple[list[dict], list[str]]:
    """Merge CompSniper (eBay) + graded auction houses + The Card API, de-duplicated by item id."""
    merged: list[dict] = []
    seen: set[str] = set()
    errors: list[str] = []

    def _add(recs: list[dict]) -> None:
        for r in recs:
            item_id = r.get("_item_id") or r["Listing Title"]
            if item_id not in seen:
                seen.add(item_id)
                merged.append(r)

    cs_res = fetch_live_compsniper_comps(
        query, cs_key, exclude_inserts=exclude_inserts, auto_filter=auto_filter, include_best_offer=include_bo
    )
    if cs_res["ok"]:
        _add(cs_res["records"])
    elif cs_res["error"]:
        errors.append(f"CompSniper: {cs_res['error']}")

    if include_auctions:
        auc_res = fetch_live_graded_auctions(query, cs_key, exclude_inserts=exclude_inserts, auto_filter=auto_filter)
        if auc_res["ok"]:
            _add(auc_res["records"])

    tca_res = fetch_live_cardapi_comps(
        query,
        tca_key,
        exclude_inserts=exclude_inserts,
        auto_filter=auto_filter,
        include_best_offer_ask=include_bo,
        limit=100,
    )
    if tca_res["ok"]:
        _add(tca_res["records"])
    elif tca_res["error"]:
        errors.append(f"The Card API: {tca_res['error']}")

    merged.sort(key=lambda r: r.get("Sale Date", ""), reverse=True)
    return merged, errors


def title_passes_filters(title: str, query: str, exclude_inserts: bool, auto_filter: str) -> bool:
    """Same relevance rules used on sold comps, applied to active listing titles."""
    t = title.lower()
    if JUNK_TITLE_PATTERNS.search(title):
        return False
    raw_tokens = [x.strip().lower() for x in query.split() if x.strip()]
    required = [x.lstrip("#") for x in raw_tokens if not x.startswith("-")]
    excluded = [x[1:] for x in raw_tokens if x.startswith("-") and len(x) > 1]
    if any(ex in t for ex in excluded):
        return False
    if not all(tok in t for tok in required):
        return False
    if exclude_inserts:
        for w in INSERT_AND_OTHER_SET_WORDS:
            if w in t and not any(w in req for req in required):
                return False
    is_auto = bool(AUTO_PATTERN.search(title))
    if auto_filter == "Non-Auto Only" and is_auto:
        return False
    if auto_filter == "Autographs Only" and not is_auto:
        return False
    return True


def compute_ceilings(sales: dict, cond: str) -> dict:
    """Max all-in buy ceilings for a listing of a given grade, from the 30-day comps."""
    if cond == "Raw":
        raw = compute_comp_stats(sales.get("Raw", []))
        p10 = compute_comp_stats(sales.get("PSA 10", []))
        a = evaluate_standard_path(raw[anchor_key], raw["floor_25"], target_roi_decimal, include_grading=False)
        b = evaluate_standard_path(p10[anchor_key], p10["floor_25"], target_roi_decimal, include_grading=True)
        p9 = compute_comp_stats(sales.get("PSA 9", []))
        cap9 = None
        if p9["count"] and p10["count"]:
            cap9 = evaluate_psa9_bailout(p9[anchor_key], b["max_buy"])["breakeven_buy_cap"]
        return {
            "A": a["max_buy"] if raw["count"] else None,
            "B": b["max_buy"] if p10["count"] else None,
            "cap9": cap9,
            "n": raw["count"],
            "n_b": p10["count"],
        }
    st_ = compute_comp_stats(sales.get(cond, []))
    c = evaluate_standard_path(st_[anchor_key], st_["floor_25"], target_roi_decimal, include_grading=False)
    return {"A": c["max_buy"] if st_["count"] else None, "B": None, "cap9": None, "n": st_["count"], "n_b": 0}


def build_deal_rows(
    query: str,
    exclude_inserts: bool,
    auto_filter: str,
    include_bo: bool,
    include_auctions: bool,
    sort: str,
    buy_type: str,
) -> dict:
    """Check active eBay listings first (free 5,000/day); only pull CompSniper comps if matching listings exist."""
    el = fetch_ebay_active_listings(
        query, get_secret_key("EBAY_APP_ID"), get_secret_key("EBAY_CERT_ID"), sort, buy_type
    )
    if not el["ok"]:
        return {"ok": False, "error": el["error"], "rows": [], "sales": {}, "errors": []}

    filtered_listings = [
        l for l in el["records"] if title_passes_filters(l["Title"], query, exclude_inserts, auto_filter)
    ]
    if not filtered_listings:
        return {"ok": True, "error": "", "rows": [], "sales": {}, "errors": []}

    cs_key = get_secret_key("COMPSNIPER_API_KEY")
    tca_key = get_secret_key("THECARDAPI_KEY")
    recs, errors = gather_merged_comps(query, cs_key, tca_key, exclude_inserts, auto_filter, include_bo, include_auctions)
    sales: dict[str, list[float]] = {}
    for r in recs:
        if r.get("Include", True):
            sales.setdefault(r["Condition"], []).append(float(r["Sold Price ($)"]))

    ceil_cache: dict[str, dict] = {}
    rows: list[dict] = []
    for l in filtered_listings:
        cond = classify_sale_condition({"title": l["Title"]})
        if cond not in ceil_cache:
            ceil_cache[cond] = compute_ceilings(sales, cond)
        c = ceil_cache[cond]
        total = l["Price ($)"] + (l["Ship ($)"] or 0.0)
        ceil_a, ceil_b, cap9 = c["A"], c["B"], c.get("cap9")
        thin = " ⚠️ thin comps" if (c["n"] < 3 and c["A"] is not None) else ""
        if ceil_a is None and ceil_b is None:
            verdict = "⚠️ No comps"
            room = None
        elif cond == "Raw":
            # Path B is only "safe" if a PSA 9 outcome still breaks even (your bailout rule).
            safe_b = min(ceil_b, cap9) if (ceil_b is not None and cap9 is not None) else None
            if ceil_a is not None and total <= ceil_a:
                verdict = "✅ Path A Deal" + thin
            elif safe_b is not None and total <= safe_b:
                verdict = "🎯 Path B Deal (PSA 9 safe)" + thin
            elif ceil_b is not None and total <= ceil_b:
                verdict = "🎲 Path B — needs PSA 10"
            else:
                verdict = "❌ Over ceiling"
            safe_ceils = [x for x in (ceil_a, safe_b) if x is not None]
            room = (max(safe_ceils) if safe_ceils else ceil_b) - total
        else:
            verdict = ("✅ Slab Deal" + thin) if total <= ceil_a else "❌ Over ceiling"
            room = ceil_a - total
        rows.append(
            {
                "Photo": l["Photo"],
                "Verdict": verdict,
                "Grade": cond,
                "All-In ($)": round(total, 2),
                "Price ($)": l["Price ($)"],
                "Ship ($)": l["Ship ($)"],
                "Ceiling A/Slab ($)": None if ceil_a is None else round(ceil_a, 2),
                "Ceiling B ($)": None if ceil_b is None else round(ceil_b, 2),
                "PSA 9 Safe Cap ($)": None if cap9 is None else round(cap9, 2),
                "Room ($)": None if room is None else round(room, 2),
                "Type": l["Type"],
                "Search": query,
                "Title": l["Title"],
                "Link": l["Link"],
            }
        )
    return {"ok": True, "error": "", "rows": rows, "sales": sales, "errors": errors}


DEAL_TABLE_CONFIG = {
    "Photo": st.column_config.ImageColumn("Card Photo", width="small"),
    "All-In ($)": st.column_config.NumberColumn("All-In (Price+Ship)", format="$%.2f"),
    "Price ($)": st.column_config.NumberColumn("Price", format="$%.2f"),
    "Ship ($)": st.column_config.NumberColumn("Shipping", format="$%.2f"),
    "Ceiling A/Slab ($)": st.column_config.NumberColumn("Max Buy (Path A / Slab)", format="$%.2f"),
    "Ceiling B ($)": st.column_config.NumberColumn("Max Buy (Path B, needs PSA 10)", format="$%.2f"),
    "PSA 9 Safe Cap ($)": st.column_config.NumberColumn("PSA 9 Safe Cap", format="$%.2f"),
    "Room ($)": st.column_config.NumberColumn("Room Under Ceiling", format="$%.2f"),
    "Link": st.column_config.LinkColumn("eBay Listing", display_text="View ↗"),
    "Title": st.column_config.TextColumn("Title", width="large"),
}


def render_marketplace_links(query: str) -> None:
    """1-click external search links for active asking prices on COMC, Mercari, Fanatics Collect, and MySlabs."""
    from urllib.parse import quote_plus

    q_clean = query.strip()
    if not q_clean:
        return
    enc = quote_plus(q_clean)
    st.caption("🌐 **1-Click Cross-Check Active Listings:**")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.link_button("COMC ↗", f"https://www.comc.com/Cards,sr,={enc}", use_container_width=True)
    with m2:
        st.link_button("Mercari ↗", f"https://www.mercari.com/search/?keyword={enc}", use_container_width=True)
    with m3:
        st.link_button("Fanatics Collect ↗", f"https://www.fanaticscollect.com/marketplace?q={enc}", use_container_width=True)
    with m4:
        st.link_button("MySlabs ↗", f"https://www.myslabs.com/search/all/?q={enc}", use_container_width=True)


def identify_card_from_photo(front_bytes: bytes, back_bytes: bytes | None, api_key: str) -> dict:
    """Use Gemini 2.5 Flash Vision API to identify card details and build a concise CompSniper search string."""
    import json

    parts = [
        {
            "text": (
                "You are a sports & trading card expert. Inspect the card image(s) (front, and optional back for card #) "
                "and return ONLY valid JSON with these exact keys:\n"
                '{"search_query": "<concise search: Year Brand/Set Player Parallel CardNumber, e.g. 2023 Prizm Bijan Robinson Silver 305>", '
                '"condition": "<one of: Raw, PSA 10, PSA 9, BGS 9.5, SGC 10>", '
                '"is_auto": <true or false>, '
                '"cert_number": "<numeric slab cert number if graded and visible, else empty string>", '
                '"notes": "<1 short sentence describing what you see, including parallel/serial/auto cues>"}\n'
                "Keep search_query short (5-7 words max, no punctuation like #). Only include 'Silver' or another parallel if clearly visible."
            )
        },
        {
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(front_bytes).decode("ascii"),
            }
        },
    ]
    if back_bytes:
        parts.append(
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(back_bytes).decode("ascii"),
                }
            }
        )

    try:
        resp = None
        for model_name in ("gemini-3-flash-preview", "gemini-flash-latest"):
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key.strip()}",
                json={
                    "contents": [{"parts": parts}],
                    "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1},
                },
                timeout=30,
            )
            if resp.status_code == 200:
                break
        if resp is None or resp.status_code != 200:
            code = resp.status_code if resp is not None else "N/A"
            body = resp.text[:200] if resp is not None else ""
            return {"ok": False, "error": f"Gemini API HTTP {code}: {body}"}
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
        return {"ok": True, "data": parsed}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def render_card_scanner(
    target_query_key: str,
    target_grade_key: str | None = None,
    target_auto_key: str | None = None,
) -> None:
    """Phone camera / photo upload card & slab scanner with confirm-before-comping safeguard."""
    scan_state_key = f"scan_res_{target_query_key}"
    confirm_input_key = f"scan_confirm_{target_query_key}"

    with st.expander("📷 Scan Card or Slab (Phone Camera / Photo)", expanded=False):
        gem_key = get_secret_key("GEMINI_API_KEY")
        if not gem_key:
            st.info(
                "🔑 **Add a free `GEMINI_API_KEY` to Secrets to enable Photo Scanning:**\n\n"
                "1. Grab a free API key at **https://aistudio.google.com/apikey**\n"
                "2. Add `GEMINI_API_KEY = \"your_key_here\"` to `.streamlit/secrets.toml` (and Streamlit Cloud → Settings → Secrets)."
            )
            return

        src_mode = st.radio(
            "Photo Source",
            ["Take Photo (Phone Camera)", "Upload Photo(s)"],
            horizontal=True,
            key=f"scan_src_{target_query_key}",
        )
        front_file = None
        back_file = None
        if src_mode == "Take Photo (Phone Camera)":
            front_file = st.camera_input("Snap Front of Card (or Slab Label)", key=f"cam_f_{target_query_key}")
            back_file = st.file_uploader("Optional: Upload Back Photo (for Card #)", type=["jpg", "jpeg", "png", "webp"], key=f"cam_b_{target_query_key}")
        else:
            uc1, uc2 = st.columns(2)
            with uc1:
                front_file = st.file_uploader("Front of Card / Slab", type=["jpg", "jpeg", "png", "webp"], key=f"up_f_{target_query_key}")
            with uc2:
                back_file = st.file_uploader("Optional: Back of Card (for Card #)", type=["jpg", "jpeg", "png", "webp"], key=f"up_b_{target_query_key}")

        if front_file is not None and st.button("🔍 Identify Card from Photo", key=f"scan_go_{target_query_key}", type="primary"):
            with st.spinner("Reading card details with Vision AI..."):
                res = identify_card_from_photo(
                    front_file.getvalue(),
                    back_file.getvalue() if back_file is not None else None,
                    gem_key,
                )
            if res["ok"]:
                st.session_state[scan_state_key] = res["data"]
                st.session_state[confirm_input_key] = str(res["data"].get("search_query") or "")
            else:
                st.error(res["error"])

        if scan_state_key in st.session_state:
            d = st.session_state[scan_state_key]
            cond_det = str(d.get("condition") or "Raw")
            if cond_det not in ("Raw", "PSA 10", "PSA 9", "BGS 9.5", "SGC 10"):
                cond_det = "Raw"
            auto_det = "Autographs Only" if d.get("is_auto") else "Non-Auto Only"
            cert_det = str(d.get("cert_number") or "").strip()

            st.success(f"**Detected:** `{cond_det}` | `{auto_det}`" + (f" | Cert `#{cert_det}`" if cert_det else "") + f"\n\n_{d.get('notes', '')}_")
            confirmed_q = st.text_input("Confirm or Tweak Search Before Running Comps", key=confirm_input_key)

            def _apply_scan() -> None:
                upd = {target_query_key: st.session_state.get(confirm_input_key, "").strip()}
                if target_grade_key:
                    upd[target_grade_key] = cond_det
                if target_auto_key:
                    upd[target_auto_key] = auto_det
                st.session_state.update(upd)

            st.button(
                "✅ Use This Search & Pull Comps",
                key=f"scan_apply_{target_query_key}",
                type="primary",
                on_click=_apply_scan,
            )


live_records: list[dict] = []

# ---------------------------------------------------------------------------
# Custom Ville-In-Us Branded SVG Section Headers (Replaces Generic Emojis)
# ---------------------------------------------------------------------------
SVG_GRAD_DEFS = """
<defs>
    <linearGradient id="viuIconGrad" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#c81e3a" />
        <stop offset="55%" stop-color="#7e22ce" />
        <stop offset="100%" stop-color="#4c1d95" />
    </linearGradient>
</defs>
"""

ICON_TIER1 = f"""
<svg width="28" height="28" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
    {SVG_GRAD_DEFS}
    <polygon points="8,2 28,2 34,8 34,28 28,34 8,34 2,28 2,8" fill="#09070f" stroke="#9333ea" stroke-width="2.5"/>
    <polygon points="10,6 26,6 30,10 30,26 26,30 10,30 6,26 6,10" fill="url(#viuIconGrad)" stroke="#d8b4fe" stroke-width="1.2"/>
    <circle cx="18" cy="18" r="5" fill="#09070f" stroke="#f43f5e" stroke-width="2"/>
    <line x1="18" y1="8" x2="18" y2="13" stroke="#f8fafc" stroke-width="2"/>
    <line x1="18" y1="23" x2="18" y2="28" stroke="#f8fafc" stroke-width="2"/>
    <line x1="8" y1="18" x2="13" y2="18" stroke="#f8fafc" stroke-width="2"/>
    <line x1="23" y1="18" x2="28" y2="18" stroke="#f8fafc" stroke-width="2"/>
</svg>
"""

ICON_PATH_A = f"""
<svg width="34" height="34" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
    {SVG_GRAD_DEFS}
    <!-- Beveled Villain Shield Frame -->
    <polygon points="3,5 37,5 33,35 7,35" fill="#09070f" stroke="#8b3dff" stroke-width="3" stroke-linejoin="miter"/>
    <polygon points="3,5 37,5 33,35 7,35" fill="none" stroke="#d8b4fe" stroke-width="1" stroke-linejoin="miter"/>
    <!-- Raw Card Silhouette + Sharp Heist Flip Slash Arrows -->
    <rect x="12" y="9" width="16" height="22" rx="1" fill="url(#viuIconGrad)" stroke="#e9d5ff" stroke-width="1.3"/>
    <path d="M 8,17 L 15,11 L 15,15 L 25,15 L 25,18 L 12,18 Z" fill="#ffffff"/>
    <path d="M 32,23 L 25,29 L 25,25 L 15,25 L 15,22 L 28,22 Z" fill="#f43f5e"/>
</svg>
"""

ICON_PATH_B = f"""
<svg width="34" height="34" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
    {SVG_GRAD_DEFS}
    <!-- Beveled Villain Shield Frame -->
    <polygon points="3,5 37,5 33,35 7,35" fill="#09070f" stroke="#8b3dff" stroke-width="3" stroke-linejoin="miter"/>
    <polygon points="3,5 37,5 33,35 7,35" fill="none" stroke="#d8b4fe" stroke-width="1" stroke-linejoin="miter"/>
    <!-- Graded Slab Silhouette with Top Flip Label & "10" -->
    <rect x="10" y="7" width="20" height="26" rx="1.5" fill="url(#viuIconGrad)" stroke="#e9d5ff" stroke-width="1.4"/>
    <rect x="12" y="9" width="16" height="5" fill="#09070f" stroke="#f43f5e" stroke-width="1"/>
    <text x="20" y="27" text-anchor="middle" font-family="'Orbitron', 'Arial Black', sans-serif" font-size="11" font-weight="900" fill="#ffffff" stroke="#d8b4fe" stroke-width="0.4">10</text>
</svg>
"""

ICON_BAILOUT_9 = f"""
<svg width="30" height="30" viewBox="0 0 38 38" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
    {SVG_GRAD_DEFS}
    <!-- Angular Vault Armor Shield -->
    <polygon points="19,2 34,8 31,25 19,36 7,25 4,8" fill="#09070f" stroke="#8b3dff" stroke-width="3" stroke-linejoin="miter"/>
    <polygon points="19,5 31,10 28,24 19,33 10,24 7,10" fill="url(#viuIconGrad)" stroke="#e9d5ff" stroke-width="1.2" stroke-linejoin="miter"/>
    <text x="19" y="24" text-anchor="middle" font-family="'Orbitron', 'Arial Black', sans-serif" font-size="14" font-weight="900" fill="#ffffff">9</text>
</svg>
"""

ICON_PATH_C = f"""
<svg width="34" height="34" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
    {SVG_GRAD_DEFS}
    <polygon points="3,5 37,5 33,35 7,35" fill="#09070f" stroke="#8b3dff" stroke-width="3" stroke-linejoin="miter"/>
    <polygon points="3,5 37,5 33,35 7,35" fill="none" stroke="#d8b4fe" stroke-width="1" stroke-linejoin="miter"/>
    <rect x="9" y="9" width="15" height="21" rx="1" fill="#2e1065" stroke="#c084fc" stroke-width="1.2"/>
    <rect x="16" y="7" width="15" height="21" rx="1" fill="url(#viuIconGrad)" stroke="#ffffff" stroke-width="1.3"/>
    <rect x="18" y="9" width="11" height="4" fill="#09070f" stroke="#f43f5e" stroke-width="0.9"/>
</svg>
"""


def brand_heading(icon_svg: str, title_text: str, size_rem: float = 1.28, icon_px: int = 34) -> str:
    b64_svg = base64.b64encode(icon_svg.strip().encode("utf-8")).decode("ascii")
    return (
        f'<div style="display:flex; align-items:center; gap:12px; margin: 2px 0 6px 0;">'
        f'<img src="data:image/svg+xml;base64,{b64_svg}" width="{icon_px}" height="{icon_px}" style="flex-shrink:0; display:block;" />'
        f'<span style="font-family:\'Orbitron\',\'Chakra Petch\',sans-serif; font-size:{size_rem}rem; '
        f'font-weight:900; letter-spacing:0.05em; color:#f8fafc; text-transform:uppercase;">'
        f'{title_text}</span></div>'
    )


# Select Card & Listing Condition
if data_mode == "Live Sold Comps":
    if "comps_query" not in st.session_state:
        st.session_state.comps_query = ""

    render_card_scanner("comps_query", target_auto_key="comps_auto")

    qc1, qc2 = st.columns([3.4, 1.1])
    with qc1:
        selected_card_title = st.text_input(
            "Search Any Card (Include Card # like '305' for Exact Base/Parallel Match)",
            placeholder="e.g. 2023 Prizm Bijan Robinson Silver 305",
            key="comps_query",
            help="Tip: Keep keywords short (year + set + player + parallel + card #) so cheap inserts don't mix in. Starts blank to save API tokens.",
        )
    with qc2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        st.button(
            "⚡ Bijan Silver #305",
            key="load_bijan_comps",
            use_container_width=True,
            on_click=lambda: st.session_state.update({"comps_query": "2023 Prizm Bijan Robinson Silver 305"}),
        )
    detected_condition = "Raw"

    fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns([1.1, 1.0, 1.2, 1.0, 1.3])
    with fcol1:
        auto_filter_mode = st.selectbox(
            "Autograph Filter",
            options=["Non-Auto Only", "Autographs Only", "All"],
            index=0,
            key="comps_auto",
            help="Separates True Silver Non-Autos from True Silver Autographs that share the same card #.",
        )
    with fcol2:
        comps_grade_filter = st.selectbox(
            "Grade Filter",
            options=["All", "Raw Only", "Slabs Only"],
            index=0,
            help="Filter the sales table to Raw only, Slabs only, or All.",
        )
    with fcol3:
        exclude_inserts_flag = st.checkbox(
            "Block Inserts & Other Sets",
            value=True,
            help="Automatically filters out Flashback, Emergent, Variation, Relic/Jersey, Select, Mosaic, and Draft Picks.",
        )
    with fcol4:
        include_bo_flag = st.checkbox(
            "Include Best Offer",
            value=True,
            help="CompSniper returns the actual accepted Best Offer price; The Card API uses the listed ask when hidden.",
        )
    with fcol5:
        include_auctions_flag = st.checkbox(
            "Include Graded Auctions",
            value=False,
            help="Off by default to save CompSniper credits (1 call vs 5 calls). Turn ON to add Goldin, Fanatics, MySlabs & Pristine.",
        )

    card_sales_data = {"Raw": [], "PSA 10": [], "PSA 9": [], "BGS 9.5": [], "SGC 10": []}

    if not selected_card_title.strip():
        st.info("🔎 Enter a card above and press **Enter** (or click **⚡ Bijan Silver #305**) to pull live comps. Blank by default so opening the app uses zero API tokens.")
    else:
        cs_key = get_secret_key("COMPSNIPER_API_KEY")
        tca_key = get_secret_key("THECARDAPI_KEY")

        with st.spinner(f"Pulling live verified sold comps & card photos for '{selected_card_title}'..."):
            merged_records, errors = gather_merged_comps(
                selected_card_title,
                cs_key,
                tca_key,
                exclude_inserts_flag,
                auto_filter_mode,
                include_bo_flag,
                include_auctions_flag,
            )
        live_records = merged_records
        if comps_grade_filter == "Raw Only":
            live_records = [r for r in live_records if r.get("Condition") == "Raw"]
        elif comps_grade_filter == "Slabs Only":
            live_records = [r for r in live_records if r.get("Condition") != "Raw"]

        if errors and not live_records:
            st.error(" | ".join(errors))
        elif not live_records:
            st.warning("No matching sales found with the current filters. Try broadening your search or toggling the Autograph Filter.")
        else:
            if errors:
                st.caption(f"⚠️ Partial source warning: {' | '.join(errors)}")

            # Placeholder above the photo/filter section so 30-Day Comp Summary renders on top
            # while still reflecting live checkbox/grade edits from st.data_editor below.
            summary_placeholder = st.container()

            with st.expander(
                f"🖼️ Visual Card Photos & Comp Filter ({len(live_records)} Verified Sales Matched — Uncheck Any Wrong Card)",
                expanded=True,
            ):
                # Visual Card Photo Strip (Top 6 Sales with Images)
                photo_records = [r for r in live_records if r.get("Photo")][:6]
                if photo_records:
                    st.caption("📸 **Recent Sold Card Photos (Visual Verification):**")
                    pcols = st.columns(len(photo_records))
                    for idx, rec in enumerate(photo_records):
                        with pcols[idx]:
                            st.image(rec["Photo"], width="stretch")
                            st.markdown(
                                f"<div style='font-size:0.76rem; line-height:1.25; text-align:center;'>"
                                f"<b style='color:#4ade80;'>\\${rec['Sold Price ($)']:,.2f}</b> &bull; "
                                f"<span style='color:#c084fc;font-weight:700;'>{rec['Condition']}</span><br/>"
                                f"<span style='color:#94a3b8;'>{rec['Sale Date']} ({rec.get('Source', '')})</span></div>",
                                unsafe_allow_html=True,
                            )

                st.caption("☑️ **Uncheck `Include` on any outlier, or click `Grade` to re-assign a mislabeled card:**")
                display_records = [{k: v for k, v in r.items() if k != "_item_id"} for r in live_records]
                df_editor = pd.DataFrame(display_records)
                edited_df = st.data_editor(
                    df_editor,
                    width="stretch",
                    hide_index=True,
                    disabled=["Photo", "Sold Price ($)", "Sale Date", "Card #", "Source", "Type", "Listing Title", "Link"],
                    column_config={
                        "Include": st.column_config.CheckboxColumn("Include ✅", default=True),
                        "Photo": st.column_config.ImageColumn("Card Photo", width="small"),
                        "Condition": st.column_config.SelectboxColumn(
                            "Grade (Editable)",
                            options=["Raw", "PSA 10", "PSA 9", "BGS 9.5", "SGC 10", "Other Slab"],
                            required=True,
                        ),
                        "Sold Price ($)": st.column_config.NumberColumn("Sold Price", format="$%.2f"),
                        "Sale Date": st.column_config.TextColumn("Date Sold"),
                        "Card #": st.column_config.TextColumn("Card #"),
                        "Source": st.column_config.TextColumn("API Source"),
                        "Type": st.column_config.TextColumn("Sale Type"),
                        "Listing Title": st.column_config.TextColumn("Listing Title", width="large"),
                        "Link": st.column_config.LinkColumn("eBay Listing", display_text="View ↗"),
                    },
                    key=f"comp_editor_v3_{data_mode}_{selected_card_title}_{auto_filter_mode}_{exclude_inserts_flag}_{include_bo_flag}",
                )

                for _, row in edited_df.iterrows():
                    if row["Include"] and row["Condition"] in card_sales_data:
                        card_sales_data[row["Condition"]].append(float(row["Sold Price ($)"]))

                r_c = len(card_sales_data["Raw"])
                r_avg = pd.Series(card_sales_data["Raw"], dtype=float).mean() if r_c else 0.0
                r_med = pd.Series(card_sales_data["Raw"], dtype=float).median() if r_c else 0.0
                p10_c = len(card_sales_data["PSA 10"])
                p10_avg = pd.Series(card_sales_data["PSA 10"], dtype=float).mean() if p10_c else 0.0
                p10_med = pd.Series(card_sales_data["PSA 10"], dtype=float).median() if p10_c else 0.0
                st.info(
                    f"📊 **Live Checked Selection Stats:** "
                    f"**Raw ({r_c} checked):** Average `${r_avg:,.2f}` | Median `${r_med:,.2f}` &nbsp;&bull;&nbsp; "
                    f"**PSA 10 ({p10_c} checked):** Average `${p10_avg:,.2f}` | Median `${p10_med:,.2f}`"
                )

            with summary_placeholder:
                st.markdown(
                    brand_heading(ICON_TIER1, "30-Day Comp Summary (Checked Sales)", size_rem=1.22, icon_px=28),
                    unsafe_allow_html=True,
                )
                summary_rows = []
                for cond_name in ["Raw", "PSA 10", "PSA 9", "BGS 9.5", "SGC 10"]:
                    vals = card_sales_data.get(cond_name, [])
                    if vals:
                        s_ = compute_comp_stats(vals)
                        summary_rows.append(
                            {
                                "Grade": cond_name,
                                "Sales": s_["count"],
                                "30-Day High": s_["high"],
                                "Average": s_["mean"],
                                "Median": s_["median"],
                                "25th-Pct Floor": s_["floor_25"],
                                "30-Day Low": s_["low"],
                            }
                        )
                if summary_rows:
                    st.dataframe(
                        pd.DataFrame(summary_rows),
                        width="stretch",
                        hide_index=True,
                        column_config={
                            k: st.column_config.NumberColumn(k, format="$%.2f")
                            for k in ["30-Day High", "Average", "Median", "25th-Pct Floor", "30-Day Low"]
                        },
                    )
                    st.caption(
                        "💡 Valuation, Path A / Path B buy ceilings and the PSA 9 bailout live under "
                        "**eBay Live Listings (Buy Side)** in the sidebar."
                    )

elif data_mode == "Manual / Paste Comps":
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

def render_tier1(card_sales_data: dict, detected_condition: str, selected_card_title: str) -> None:
    # ---------------------------------------------------------------------------
    # TIER 1 — Default Clean Snapshot (Always Visible)
    # ---------------------------------------------------------------------------
    st.markdown(
        brand_heading(ICON_TIER1, "Tier 1 — Valuation & Buy Ceiling Snapshot", size_rem=1.22, icon_px=28),
        unsafe_allow_html=True,
    )

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
            median_price=raw_stats[anchor_key],
            floor_price=raw_stats["floor_25"],
            target_roi_decimal=target_roi_decimal,
            include_grading=False,
        )
        path_b = evaluate_standard_path(
            median_price=psa10_stats[anchor_key],
            floor_price=psa10_stats["floor_25"],
            target_roi_decimal=target_roi_decimal,
            include_grading=True,
        )
        bailout_9 = evaluate_psa9_bailout(
            psa9_median=psa9_stats[anchor_key],
            path_b_max_buy=path_b["max_buy"],
        )

        col_path_a, col_path_b = st.columns(2)

        # --- PATH A SUMMARY BLOCK ---
        with col_path_a:
            with st.container(border=True):
                st.markdown(
                    brand_heading(ICON_PATH_A, "PATH A — RAW-TO-RAW FLIP"),
                    unsafe_allow_html=True,
                )
                st.caption("Buy Raw -> Sell Raw (Bypasses $47 PSA grading fee)")

                m1, m2 = st.columns(2)
                m1.metric(f"30-Day Raw {anchor_label}", f"${path_a['median']:,.2f}")
                m2.metric("25th-Pct Conservative Floor", f"${path_a['floor_25']:,.2f}")

                m3, m4 = st.columns(2)
                m3.metric("Net Payout (After Fees/Ship)", f"${path_a['net_payout']:,.2f}")
                m4.metric(
                    f"Max All-In Buy ({target_roi_pct}% ROI)",
                    f"${path_a['max_buy']:,.2f}",
                    delta=f"+${path_a['expected_profit']:,.2f} Est. Net Profit",
                )

                # TIER 2 — Clickable Arithmetic Breakdown (Path A)
                with st.expander("➕ Click to Open Tier 2 — Arithmetic Breakdown & Floor Stress Test (Path A)"):
                    st.markdown("#### 0. 30-Day Raw Sales Range (High / Average / Median / Floor / Low)")
                    st.markdown(
                        f"""
                        - **30-Day High Sale:** **\\${raw_stats['high']:,.2f}**
                        - **30-Day Average (Mean):** **\\${raw_stats['mean']:,.2f}**
                        - **30-Day Median (Middle Sale):** **\\${raw_stats['median']:,.2f}** ({raw_stats['count']} sales)
                        - **25th-Percentile Conservative Floor:** **\\${path_a['floor_25']:,.2f}**
                        - **30-Day Low Sale:** **\\${raw_stats['low']:,.2f}**
                        """
                    )
                    st.markdown("#### 1. Net Payout & Max Buy Price Math")
                    st.markdown(
                        f"""
                        - **30-Day Raw {anchor_label} Anchor:** \\${path_a['median']:,.2f} ({raw_stats['count']} sales)
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
                st.markdown(
                    brand_heading(ICON_PATH_B, "PATH B — RAW-TO-PSA 10 GRADE"),
                    unsafe_allow_html=True,
                )
                st.caption("Buy Raw -> Grade with PSA ($47.00 all-in) -> Sell PSA 10")

                b1, b2 = st.columns(2)
                b1.metric(f"30-Day PSA 10 {anchor_label}", f"${path_b['median']:,.2f}")
                b2.metric("25th-Pct Conservative Floor", f"${path_b['floor_25']:,.2f}")

                b3, b4 = st.columns(2)
                b3.metric("Net Payout (After Fees/Ship/PSA)", f"${path_b['net_payout']:,.2f}")
                b4.metric(
                    f"Max All-In Buy ({target_roi_pct}% ROI)",
                    f"${path_b['max_buy']:,.2f}",
                    delta=f"+${path_b['expected_profit']:,.2f} Est. Net Profit",
                )

                st.divider()
                st.markdown(
                    brand_heading(ICON_BAILOUT_9, "PSA 9 BAILOUT CHECK", size_rem=1.08, icon_px=30),
                    unsafe_allow_html=True,
                )
                bail_col1, bail_col2, bail_col3 = st.columns(3)
                bail_col1.metric(f"30-Day PSA 9 {anchor_label}", f"${bailout_9['psa9_median']:,.2f}")
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
                with st.expander("➕ Click to Open Tier 2 — Arithmetic Breakdown & Floor Stress Test (Path B)"):
                    st.markdown("#### 0. 30-Day Graded Sales Range (PSA 10 & PSA 9 High / Avg / Median / Low)")
                    st.markdown(
                        f"""
                        - **PSA 10 ({psa10_stats['count']} sales):** High **\\${psa10_stats['high']:,.2f}** &nbsp;|&nbsp; Avg **\\${psa10_stats['mean']:,.2f}** &nbsp;|&nbsp; Median **\\${psa10_stats['median']:,.2f}** &nbsp;|&nbsp; 25th-Pct Floor **\\${path_b['floor_25']:,.2f}** &nbsp;|&nbsp; Low **\\${psa10_stats['low']:,.2f}**
                        - **PSA 9 ({psa9_stats['count']} sales):** High **\\${psa9_stats['high']:,.2f}** &nbsp;|&nbsp; Avg **\\${psa9_stats['mean']:,.2f}** &nbsp;|&nbsp; Median **\\${psa9_stats['median']:,.2f}** &nbsp;|&nbsp; 25th-Pct Floor **\\${psa9_stats['floor_25']:,.2f}** &nbsp;|&nbsp; Low **\\${psa9_stats['low']:,.2f}**
                        """
                    )
                    st.markdown("#### 1. PSA 10 Net Payout & Max Buy Price Math")
                    st.markdown(
                        f"""
                        - **30-Day PSA 10 {anchor_label} Anchor:** \\${path_b['median']:,.2f} ({psa10_stats['count']} sales)
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
            median_price=slab_stats[anchor_key],
            floor_price=slab_stats["floor_25"],
            target_roi_decimal=target_roi_decimal,
            include_grading=False,
        )

        with st.container(border=True):
            st.markdown(
                brand_heading(ICON_PATH_C, f"PATH C — SLAB-TO-SLAB FLIP ({detected_condition})"),
                unsafe_allow_html=True,
            )
            st.caption(f"Buy {detected_condition} Slab -> Sell {detected_condition} Slab (Grading cost bypassed: $0.00)")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric(f"30-Day {detected_condition} {anchor_label}", f"${path_c['median']:,.2f}")
            c2.metric("25th-Pct Conservative Floor", f"${path_c['floor_25']:,.2f}")
            c3.metric("Net Payout (After Fees/Ship)", f"${path_c['net_payout']:,.2f}")
            c4.metric(
                f"Max All-In Buy ({target_roi_pct}% ROI)",
                f"${path_c['max_buy']:,.2f}",
                delta=f"+${path_c['expected_profit']:,.2f} Est. Net Profit",
            )

            # TIER 2 — Clickable Arithmetic Breakdown (Path C)
            with st.expander(f"➕ Click to Open Tier 2 — Arithmetic Breakdown & Floor Stress Test (Path C: {detected_condition})"):
                st.markdown(f"#### 0. 30-Day {detected_condition} Sales Range (High / Average / Median / Floor / Low)")
                st.markdown(
                    f"""
                    - **30-Day High Sale:** **\\${slab_stats['high']:,.2f}**
                    - **30-Day Average (Mean):** **\\${slab_stats['mean']:,.2f}**
                    - **30-Day Median (Middle Sale):** **\\${slab_stats['median']:,.2f}** ({slab_stats['count']} sales)
                    - **25th-Percentile Conservative Floor:** **\\${path_c['floor_25']:,.2f}**
                    - **30-Day Low Sale:** **\\${slab_stats['low']:,.2f}**
                    """
                )
                st.markdown("#### 1. Net Payout & Max Buy Price Math")
                st.markdown(
                    f"""
                    - **30-Day {detected_condition} {anchor_label} Anchor:** \\${path_c['median']:,.2f} ({slab_stats['count']} sales)
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


# ---------------------------------------------------------------------------
# MODE ROUTING — Comps summary / Manual valuation / Buy Side / Deal Finder
# ---------------------------------------------------------------------------
if data_mode == "Live Sold Comps":
    pass

elif data_mode == "Manual / Paste Comps":
    render_tier1(card_sales_data, detected_condition, selected_card_title)

elif data_mode == "eBay Live Listings (Buy Side)":
    st.markdown(
        brand_heading(ICON_PATH_A, "Buy Side — Live Listings vs. Your Buy Ceiling", size_rem=1.22, icon_px=30),
        unsafe_allow_html=True,
    )
    st.caption(
        "Pulls the 30-day sold comps for your search automatically, then scores every active eBay listing "
        "against your Path A / Path B / Slab buy ceilings."
    )
    if "buy_query" not in st.session_state:
        st.session_state.buy_query = ""

    render_card_scanner("buy_query", target_grade_key="buy_grade", target_auto_key="buy_auto")

    bq1, bq2, bq3 = st.columns([2.1, 1.0, 0.9])
    with bq1:
        buy_query = st.text_input(
            "Search Card",
            placeholder="e.g. 2023 Prizm Bijan Robinson Silver 305",
            key="buy_query",
            help="Starts blank to save API tokens. Type a card and press Enter, or click Bijan Silver #305.",
        )
    with bq2:
        buy_grade = st.selectbox(
            "Valuation Grade (drives Tier 1)",
            options=["Raw", "PSA 10", "PSA 9", "BGS 9.5", "SGC 10"],
            index=0,
            key="buy_grade",
        )
    with bq3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        st.button(
            "⚡ Bijan Silver #305",
            key="load_bijan_buy",
            use_container_width=True,
            on_click=lambda: st.session_state.update({"buy_query": "2023 Prizm Bijan Robinson Silver 305"}),
        )

    bf1, bf2, bf3, bf4 = st.columns(4)
    with bf1:
        buy_auto = st.selectbox("Autograph Filter", ["Non-Auto Only", "Autographs Only", "All"], key="buy_auto")
    with bf2:
        buy_sort = st.selectbox("Sort", ["Price + Shipping: Lowest First", "Newly Listed", "Best Match"], key="buy_sort")
    with bf3:
        buy_type = st.selectbox("Listing Type", ["All", "Buy It Now only", "Auction only"], key="buy_type")
    with bf4:
        buy_show = st.selectbox(
            "Show",
            ["Matching Grade Only", "All Grades", "Deals Only"],
            key="buy_show",
        )
    bc1, bc2 = st.columns(2)
    with bc1:
        buy_excl = st.checkbox("Block Inserts, Variations & Other Sets", value=True, key="buy_excl")
    with bc2:
        buy_auctions = st.checkbox(
            "Include Graded Auctions (Goldin, Fanatics, MySlabs)",
            value=False,
            key="buy_auctions",
            help="Off by default to save CompSniper credits (1 call vs 5 calls). Toggle ON when checking raw-to-slab or slab comps.",
        )

    if not buy_query.strip():
        st.info("🔎 Enter a card above and press **Enter** (or click **⚡ Bijan Silver #305**) to load Tier 1 buy ceilings & live eBay listings. Blank by default so opening the app uses zero API tokens.")
    else:
        render_marketplace_links(buy_query)
        with st.spinner("Pulling 30-day comps + live eBay listings..."):
            deal_res = build_deal_rows(buy_query, buy_excl, buy_auto, True, buy_auctions, buy_sort, buy_type)

        for e_ in deal_res["errors"]:
            st.caption(f"⚠️ {e_}")

        render_tier1(deal_res["sales"], buy_grade, buy_query)

        st.markdown(
            brand_heading(ICON_PATH_B, "Live eBay Listings", size_rem=1.22, icon_px=30),
            unsafe_allow_html=True,
        )
        if not deal_res["ok"]:
            st.error(deal_res["error"])
        elif not deal_res["rows"]:
            st.warning("No active listings matched your filters.")
        else:
            buy_df = pd.DataFrame(deal_res["rows"])
            if buy_show == "Matching Grade Only":
                buy_df = buy_df[buy_df["Grade"] == buy_grade]
            elif buy_show == "Deals Only":
                buy_df = buy_df[buy_df["Verdict"].str.startswith(("✅", "🎯"))]
            deal_count = int(buy_df["Verdict"].str.startswith(("✅", "🎯")).sum()) if len(buy_df) else 0
            st.caption(f"{len(buy_df)} listings shown • {deal_count} at or under your buy ceiling")
            st.dataframe(
                buy_df.drop(columns=["Search"]),
                width="stretch",
                hide_index=True,
                column_config=DEAL_TABLE_CONFIG,
            )

elif data_mode == "Deal Finder":
    st.markdown(
        brand_heading(ICON_PATH_C, "Deal Finder — Listings At / Under Your Buy Ceiling", size_rem=1.22, icon_px=30),
        unsafe_allow_html=True,
    )
    st.caption(
        "One card search per line (max 8). The Cipher pulls 30-day comps and live eBay listings for each, "
        "then shows only listings priced at or under your Path A / Path B / Slab ceiling."
    )
    watchlist_text = st.text_area(
        "Watchlist (one search per line)",
        value="2023 Prizm Bijan Robinson Silver 305",
        height=120,
        key="df_watchlist",
    )
    dfc1, dfc2, dfc3 = st.columns(3)
    with dfc1:
        df_auto = st.selectbox("Autograph Filter", ["Non-Auto Only", "Autographs Only", "All"], key="df_auto")
    with dfc2:
        df_grades = st.selectbox("Grades", ["All", "Raw only", "Slabs only"], key="df_grades")
    with dfc3:
        df_type = st.selectbox("Listing Type", ["All", "Buy It Now only", "Auction only"], key="df_type")
    dc1, dc2, dc3 = st.columns(3)
    with dc1:
        df_excl = st.checkbox("Block Inserts, Variations & Other Sets", value=True, key="df_excl")
    with dc2:
        df_auctions = st.checkbox(
            "Include Graded Auctions (Goldin, Fanatics, MySlabs)",
            value=True,
            key="df_auctions",
            help="ON by default in Deal Finder so it searches everything (eBay + Graded Auction Houses).",
        )
    with dc3:
        df_deals_only = st.checkbox("Deals only (hide listings over ceiling)", value=True, key="df_deals_only")

    if st.button("🔎 Run Deal Finder", type="primary"):
        queries = [q.strip() for q in watchlist_text.splitlines() if q.strip()][:8]
        all_rows: list[dict] = []
        all_sales: dict[str, dict] = {}
        scan_errors: list[str] = []
        prog = st.progress(0.0, text="Scanning...")
        for i_, q_ in enumerate(queries):
            prog.progress(i_ / max(len(queries), 1), text=f"Scanning: {q_}")
            res_ = build_deal_rows(q_, df_excl, df_auto, True, df_auctions, "Price + Shipping: Lowest First", df_type)
            all_sales[q_] = res_.get("sales", {})
            if res_["ok"]:
                all_rows.extend(res_["rows"])
            else:
                scan_errors.append(f"{q_}: {res_['error']}")
        prog.empty()
        st.session_state["deal_finder_rows"] = all_rows
        st.session_state["deal_finder_sales"] = all_sales
        st.session_state["deal_finder_errors"] = scan_errors

    if "deal_finder_rows" in st.session_state:
        for e_ in st.session_state.get("deal_finder_errors", []):
            st.error(e_)
        sales_map = st.session_state.get("deal_finder_sales", {})
        if sales_map:
            t1_col1, t1_col2 = st.columns([2.2, 1])
            with t1_col1:
                t1_card = st.selectbox("Tier 1 Buy Ceiling Card", options=list(sales_map.keys()), key="df_t1_card")
            with t1_col2:
                t1_grade = st.selectbox(
                    "Valuation Grade",
                    options=["Raw", "PSA 10", "PSA 9", "BGS 9.5", "SGC 10"],
                    index=0,
                    key="df_t1_grade",
                )
            render_tier1(sales_map[t1_card], t1_grade, t1_card)
            render_marketplace_links(t1_card)
            st.markdown(
                brand_heading(ICON_PATH_B, "Deal Finder Results", size_rem=1.22, icon_px=30),
                unsafe_allow_html=True,
            )
        rows_ = st.session_state["deal_finder_rows"]
        if rows_:
            dfinder = pd.DataFrame(rows_)
            if df_grades == "Raw only":
                dfinder = dfinder[dfinder["Grade"] == "Raw"]
            elif df_grades == "Slabs only":
                dfinder = dfinder[dfinder["Grade"] != "Raw"]
            if df_deals_only:
                dfinder = dfinder[dfinder["Verdict"].str.startswith(("✅", "🎯"))]
            dfinder = dfinder.sort_values("Room ($)", ascending=False, na_position="last")
            st.caption(f"{len(dfinder)} listings shown")
            if dfinder.empty:
                st.info("No listings at or under your ceiling right now. Try again later or widen the filters.")
            else:
                st.dataframe(dfinder, width="stretch", hide_index=True, column_config=DEAL_TABLE_CONFIG)
        else:
            st.info("No active listings found for that watchlist.")
