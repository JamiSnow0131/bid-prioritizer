"""Simple shared-password gate for the whole app, with an optional 'remember me'
cookie so a returning visitor isn't forced to log in again after closing the
browser/app. Matches the Product Inventory and Sales / Pest Control
Scheduler check_password() pattern.

Note: a fresh CookieManager() (or at least a fresh .get_all()) must be invoked on
every script run, with the same `key`, for Streamlit's component protocol to ever
deliver the real browser cookie value back to Python. Caching the manager object
in session_state (skipping re-invocation) silently freezes it at its first,
empty result forever.
"""

import extra_streamlit_components as stx
import streamlit as st

COOKIE_NAME = "bid_prioritizer_auth"
COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 30  # 30 days


def require_password() -> None:
    if st.session_state.get("authenticated"):
        return

    expected = st.secrets.get("app_password")
    manager = stx.CookieManager(key="auth_cookie_manager")

    if expected and manager.get(COOKIE_NAME) == expected:
        st.session_state["authenticated"] = True
        return

    st.title("Wall Whisperers Bid Prioritizer")
    password = st.text_input("Password", type="password")
    remember = st.checkbox("Remember me on this device for 30 days", value=True)

    if st.button("Log in", type="primary"):
        if expected and password == expected:
            st.session_state["authenticated"] = True
            if remember:
                manager.set(
                    COOKIE_NAME, expected, key="set_auth_cookie", max_age=COOKIE_MAX_AGE_SECONDS
                )
            else:
                st.rerun()
        else:
            st.error("Incorrect password.")

    st.stop()
