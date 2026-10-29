# Lemons Dealership Simulation — browser-based prototype

A multi-team, instructor-paced teaching game built with Streamlit and Supabase. Teams choose vehicle inventories over seven rounds, decide whether to relocate after round 2, and experience independent inspections in State B from round 4 onward.

## Setup (no local installation)

1. Upload `app.py`, `requirements.txt`, `schema.sql`, `.gitignore`, and this README to your **public GitHub repository**. Never upload credentials.
2. Create a free project at https://supabase.com, then open **SQL Editor**, paste `schema.sql`, and run it.
3. In Supabase's API settings, copy the **Project URL** and **service_role / secret key**. This key is highly privileged. Never put it in GitHub or give it to students.
4. Visit https://share.streamlit.io, choose **Create app** / **Deploy from GitHub**, select your repository and `app.py` as the entry point.
5. In Streamlit Community Cloud **App settings → Secrets**, add:

   ```toml
   SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
   SUPABASE_KEY = "YOUR_SUPABASE_SERVICE_ROLE_OR_SECRET_KEY"
   INSTRUCTOR_PASSWORD = "CHOOSE_A_LONG_UNIQUE_PASSWORD"
   TEAM_JOIN_CODE = "CHOOSE_A_CLASS_JOIN_CODE"
   ```

6. Deploy, then open the app and choose **Instructor**. Share the app link and join code with teams (not your instructor password).

## Game flow

Stages: Round 1 → Round 2 → Relocation → Round 3 → Regulation announcement → Round 4 → Round 5 → Round 6 → Round 7. Instructor advances a stage after all active teams have submitted. Inspections and fines are generated **on submission**, saved once, and revealed to students only after the instructor advances. Instructor can inspect all outcomes immediately. The regulation announcement is its own stage. Teams that relocated are in State B; those that stayed are in State A.

- Every round: $20,000 fixed purchasing budget, up to available customers.
- Reliable: $7,500 purchase, $17,500 sale; disclosed lemon: $2,500 purchase, $5,000 sale; undisclosed lemon: $2,500 purchase, $7,500 sale.
- Starting customers: 10. Each undisclosed lemon sold reduces next round's customers by one; minimum 2. Relocation after round 2 costs $20,000 and resets round 3 customers to 10.
- State B only, rounds 4–7: each dealership has its own 20% inspection draw per round. If inspected, fine = $10,000 × undisclosed lemons sold.
- Instructor report is downloadable as CSV.

## Prototype cautions

- The app uses server-side Supabase credentials in Streamlit secrets, not browser code. Student records are accessed only through the app. Teams authenticate with a join code and their own PIN; use **fictional dealership names**, not student names.
- This is a classroom prototype, not a hardened authentication system or approved research-data platform. Check institutional policies before collecting identifiable student data or using data for research.
- The instructor's advance action is manual. Do not advance until all teams have submitted; otherwise unfinished teams miss that stage. There is no reset button; for a new class, use a fresh Supabase project or carefully clear tables and reset the stage.
- Free hosting may sleep or hit usage limits. Run a multi-device pilot before class.
- The instructor can stop the activity after any completed round; teams should not be told the total number of available rounds.
