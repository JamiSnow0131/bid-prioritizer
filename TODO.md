# Open items — next session

## Done (2026-09-16)
- Snow Analytics logo + navy (#00113D) header/footer, matching Product
  Inventory and Sales's `branding.py` pattern.
- Shared-password login gate with a 30-day "remember me" cookie, matching
  Product Inventory and Sales's `auth.py` pattern (`extra-streamlit-components`
  CookieManager). Production secret already set on Streamlit Cloud and the
  app made public there by Jamie.
- Title simplified to "Bid Prioritizer" everywhere (on-page heading, icon
  removed, browser tab title, login screen).
- Project Type is now a dropdown (7 historical types + "Other"), with a
  conditional "Specify Other Project Type" field. Still doesn't affect
  scoring (see item 1 below for the related open question).
- Criteria Weights tab uses number_input instead of sliders. Normalize-to-100
  button behavior unchanged.

## Known limitation (found 2026-09-16, not fixed — pre-existing pattern)
Because "Specify Other Project Type" and "Specialist Type" both live inside
`st.form`, their `disabled=...` state only updates on the *next* rerun, which
only happens on submit. So the first time someone picks "Other" (or
"Specialist? Yes"), they can't type into the detail field until after
submitting once with it blank. This already existed for Specialist Type
before today; now it also applies to the new Other-project-type field. Not
fixed since it wasn't asked for — flag if Jamie wants both addressed
(likely fix: move those fields outside the form, or use a session_state
callback on the driving selectbox).

## 1. Competitor Count needs to affect scoring
Right now `competitor_count` is captured but not scored (it wasn't scored in
the original spreadsheet either — informational only). Also need a way to
flag "unknown" (not every bid will have this at entry time).

To decide together before building:
- Does more competitors always hurt the score, or does it depend on client/project fit?
- What multiplier curve (e.g. 1 competitor vs. 5+)?
- What does "unknown" default to — treated as average risk, or excluded from
  scoring entirely like a missing crew number?
- Does this need its own weight slot, or does it modify an existing criterion?
- Now that Project Type is a dropdown too: should Project Type itself start
  scoring, and if so what's the rule for "Other" (no historical track record)?

## 2. Criteria Weights tab: simplify the wording
Current intro text is too technical/wordy. Rewrite in plainer language.
