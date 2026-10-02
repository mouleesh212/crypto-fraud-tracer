import os
import requests
import pandas as pd
import streamlit as st


# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------

API_KEY = st.secrets["ETHERSCAN_API_KEY"]
API_URL = "https://api.etherscan.io/v2/api"


# -------------------------------------------------
# FETCH ETHEREUM TRANSACTIONS
# -------------------------------------------------

def fetch_transactions(address: str) -> list[dict]:

    if not API_KEY:
        raise RuntimeError(
            "ETHERSCAN_API_KEY environment variable "
            "set செய்யப்படவில்லை."
        )

    params = {
        "chainid": "1",
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": "0",
        "endblock": "999999999",
        "page": "1",
        "offset": "100",
        "sort": "desc",
        "apikey": API_KEY,
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    # API error handling
    if (
        data.get("status") == "0"
        and data.get("message") != "No transactions found"
    ):
        raise RuntimeError(
            data.get("result", "API request failed")
        )

    result = data.get("result", [])

    if isinstance(result, list):
        return result

    return []


# -------------------------------------------------
# STREAMLIT USER INTERFACE
# -------------------------------------------------

st.set_page_config(
    page_title="Crypto Wallet Tracer",
    page_icon="🔎",
    layout="wide"
)

st.title("🔎 Crypto Wallet Transaction Tracer")

st.caption(
    "Educational prototype — "
    "results are investigative leads, not proof of fraud."
)


# -------------------------------------------------
# WALLET INPUT
# -------------------------------------------------

address = st.text_input(
    "Enter Ethereum Wallet Address",
    placeholder="0x..."
)


# -------------------------------------------------
# TRACE BUTTON
# -------------------------------------------------

if st.button("🔍 Trace Wallet"):

    # Basic Ethereum address validation
    if not address.startswith("0x") or len(address) != 42:

        st.error(
            "சரியான Ethereum wallet address உள்ளிடு. "
            "அது 0x-ல் தொடங்கி 42 characters இருக்க வேண்டும்."
        )

    else:

        try:

            with st.spinner(
                "Blockchain transactions எடுக்கிறேன்..."
            ):

                transactions = fetch_transactions(address)


            # -----------------------------------------
            # NO TRANSACTIONS
            # -----------------------------------------

            if not transactions:

                st.info(
                    "இந்த wallet address-க்கு "
                    "transactions கிடைக்கவில்லை."
                )

            else:

                # -------------------------------------
                # CREATE DATAFRAME
                # -------------------------------------

                df = pd.DataFrame(transactions)


                # Convert Wei → ETH
                df["value_eth"] = (
                    pd.to_numeric(
                        df["value"],
                        errors="coerce"
                    ) / 10**18
                )


                # Convert Unix timestamp → UTC time
                df["time_utc"] = pd.to_datetime(
                    pd.to_numeric(
                        df["timeStamp"],
                        errors="coerce"
                    ),
                    unit="s",
                    utc=True
                )


                # -------------------------------------
                # SUMMARY
                # -------------------------------------

                st.success(
                    f"{len(df)} transactions found."
                )


                col1, col2, col3 = st.columns(3)


                with col1:
                    st.metric(
                        "Transactions",
                        len(df)
                    )


                with col2:
                    st.metric(
                        "Total ETH",
                        f"{df['value_eth'].sum():.6f}"
                    )


                with col3:
                    st.metric(
                        "Unique Destinations",
                        df["to"].nunique()
                    )


                # -------------------------------------
                # TRANSACTION TABLE
                # -------------------------------------

                st.subheader(
                    "📋 Transaction Details"
                )


                display_columns = [
                    "time_utc",
                    "from",
                    "to",
                    "value_eth",
                    "hash"
                ]


                st.dataframe(
                    df[display_columns],
                    use_container_width=True
                )


                # -------------------------------------
                # FUND FLOW
                # -------------------------------------

                st.subheader(
                    "💰 Fund Flow"
                )


                edges = (
                    df.groupby(
                        ["from", "to"]
                    )
                    .size()
                    .reset_index(
                        name="transactions"
                    )
                )


                st.dataframe(
                    edges,
                    use_container_width=True
                )


                # -------------------------------------
                # CSV REPORT
                # -------------------------------------

                csv = df.to_csv(
                    index=False
                ).encode("utf-8")


                st.download_button(
                    label="⬇️ Download CSV Report",
                    data=csv,
                    file_name="wallet_trace.csv",
                    mime="text/csv"
                )


        except Exception as exc:

            st.error(
                f"Error: {exc}"
            )
