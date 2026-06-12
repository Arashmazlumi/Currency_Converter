import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Currency Converter", page_icon="💱", layout="centered")

CURRENCIES = {
    "USD": "🇺🇸 US Dollar",
    "EUR": "🇪🇺 Euro",
    "GBP": "🇬🇧 British Pound",
    "JPY": "🇯🇵 Japanese Yen",
    "TRY": "🇹🇷 Turkish Lira",
    "CNY": "🇨🇳 Chinese Yuan",
    "TMN": "🇮🇷 Iranian Toman",
}

@st.cache_data(ttl=300)
def get_rates(base):
    r = requests.get(f"https://api.frankfurter.app/latest?from={base}", timeout=6)
    data = r.json()
    rates = {k: v for k, v in data["rates"].items() if k in CURRENCIES}
    rates[base] = 1.0
    return rates, data.get("date", "")

# ── Header ──────────────────────────────────────────────────────────
st.title("💱 Currency Converter")
st.caption("Live exchange rates · Refreshed every 5 minutes")

st.warning("⚠️ Due to international sanctions, Iranian Toman (TMN) live rates are unavailable. Please enter the rate manually. You can check the current rate at bonbast.com.")

st.divider()

# ── Inputs ──────────────────────────────────────────────────────────
currency_list = list(CURRENCIES.keys())

col1, col2 = st.columns(2)
with col1:
    from_cur = st.selectbox("From", currency_list, format_func=lambda c: CURRENCIES[c])
with col2:
    to_cur = st.selectbox("To", currency_list, index=6, format_func=lambda c: CURRENCIES[c])

amount = st.number_input("Amount", min_value=0.0, value=100.0, step=1.0)

toman_rate = None
if from_cur == "TMN" or to_cur == "TMN":
    toman_rate = st.number_input(
        "1 USD = ? Toman",
        min_value=1.0, value=176000.0, step=1000.0,
        help="Check bonbast.com for the latest rate"
    )

# ── Convert ─────────────────────────────────────────────────────────
if st.button("Convert", use_container_width=True, type="primary"):
    try:
        with st.spinner("Getting latest rates..."):
            if from_cur == "TMN":
                rates_usd, _ = get_rates("USD")
                toman_to_usd = 1 / toman_rate
                rate = toman_to_usd if to_cur == "USD" else toman_to_usd * rates_usd.get(to_cur, 0) if to_cur != "TMN" else 1.0
                rate_date = datetime.now().strftime("%Y-%m-%d")
            elif to_cur == "TMN":
                rates, rate_date = get_rates(from_cur)
                usd_per_from = rates.get("USD", 1.0) if from_cur != "USD" else 1.0
                rate = usd_per_from * toman_rate
            else:
                rates, rate_date = get_rates(from_cur)
                rate = rates.get(to_cur)

        result = amount * rate

        st.divider()
        st.metric(
            label=f"{CURRENCIES[from_cur]}  →  {CURRENCIES[to_cur]}",
            value=f"{result:,.2f} {to_cur}",
            delta=f"1 {from_cur} = {rate:,.4f} {to_cur}",
        )
        st.caption(f"Rate date: {rate_date} · Fetched at {datetime.now().strftime('%H:%M:%S')}")

        # ── All rates table ─────────────────────────────────────────
        if from_cur != "TMN":
            st.divider()
            st.subheader("All Rates")
            rates, _ = get_rates(from_cur)
            cols = st.columns(3)
            i = 0
            for cur, name in CURRENCIES.items():
                if cur in (from_cur, "TMN"):
                    continue
                val = rates.get(cur)
                if val:
                    display = f"{val:,.2f}" if val > 10 else f"{val:.4f}"
                    cols[i % 3].metric(label=name, value=f"{display} {cur}")
                    i += 1
            if toman_rate:
                usd_rate = rates.get("USD", 1.0) if from_cur != "USD" else 1.0
                cols[i % 3].metric(label=CURRENCIES["TMN"], value=f"{usd_rate * toman_rate:,.0f} TMN")

    except Exception as e:
        st.error(f"Something went wrong: {e}")
