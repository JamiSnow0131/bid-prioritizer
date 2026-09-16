# Open items — next session

## Done (2026-09-16)
- Snow Analytics logo + navy (#00113D) header/footer, matching Product
  Inventory and Sales's `branding.py` pattern.
- Shared-password login gate with a 30-day "remember me" cookie, matching
  Product Inventory and Sales's `auth.py` pattern (`extra-streamlit-components`
  CookieManager). Production secret already set on Streamlit Cloud and the
  app made public there by Jamie.

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

## 2. Project Type: dropdown with "Other"
Currently free text. Needs to become a dropdown built from the historical
project types (Tenant Fit-Out, Warehouse, Retail Buildout, Light Industrial,
etc.) plus an "Other" option.

To decide together before building:
- Should Project Type score at all (it doesn't currently — same as
  Competitor Count, it's contextual only in the original model)?
- If yes, what's the scoring rule for "Other" specifically, since by
  definition it has no historical track record yet?

## 3. Criteria Weights: replace sliders with number entry
Clear, no discussion needed — straightforward implementation change:
- Replace the 6 `st.slider(...)` calls in the Criteria Weights tab with
  `st.number_input(...)`
- Keep the existing "Normalize to 100" button behavior (enter raw numbers,
  normalize brings them to sum to 100)

## 4. Criteria Weights tab: simplify the wording
Current intro text is too technical/wordy. Rewrite in plainer language.

## 5. Add Snow Analytics logos to the app
Need the logo file(s) from the user first — ask where they are / get them
supplied, then figure out placement (header, sidebar, favicon?).
