"""Authentication module — simple access code gate."""

import streamlit as st

# Valid access codes. Update this when you sell on Gumroad.
# Format: "code" -> "user_name" (for tracking)
VALID_CODES = {
    "demo2024": "Demo user",
    "ledger-pro-trial": "Trial user",
}


def check_access():
    """Returns True if user is authenticated, False otherwise."""
    if "authenticated" in st.session_state:
        return st.session_state.authenticated

    st.set_page_config(page_title="Ledger Scanner", page_icon="🔎", layout="centered")
    st.title("🔎 Ledger Scanner")
    st.markdown("---")

    with st.container():
        st.subheader("Enter your access code")
        st.caption("Got Ledger Scanner via Gumroad? Check your email for your access code.")

        code = st.text_input("Access code", type="password", placeholder="Enter code here")

        if st.button("Unlock", type="primary", use_container_width=True):
            if code in VALID_CODES:
                st.session_state.authenticated = True
                st.session_state.user_name = VALID_CODES[code]
                st.success("Access granted! ✓")
                st.rerun()
            else:
                st.error("❌ Invalid access code. Try again or email support.")

        st.divider()
        st.markdown("""
        ### Don't have an access code?

        **Get Ledger Scanner for $19/month**
        - Forensic testing for any GL export
        - 14 automated tests
        - Professional Excel reports
        - Works with 100+ countries

        [Buy on Gumroad](https://gumroad.com/your-store) (coming soon)
        """)

    return False
