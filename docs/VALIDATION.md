# Release validation — November 5, 2026

- Local Python 3.12: 24 pytest checks passed, including model, Streamlit interaction and export/replay tests.
- GitHub Actions: initial 22-check release passed on Python 3.11; the subsequent replay additions run through the same workflow.
- Existing Streamlit Community Cloud deployment rebuilt from the existing repository's `main` branch.
- Cloud Python 3.14: normal-shift dashboard and queue/resource charts rendered.
- Live absence scenario: staffing search selected 3/2/2 and reported 156.6 → 283.2 mean completions on validation seeds 200–209 with equal $1,120 wages.
- Live 5/3/2 setting: capacity reference displayed 480/480/480 and all three station names.
- Downloaded an actual live ZIP report and replayed baseline and stress runs locally. Integer completions matched exactly; numeric results matched within 1e-10 relative or 1e-8 absolute tolerance. Platform-level float rounding prevented bitwise equality.
- Cloud dependency refresh briefly loaded mixed pandas modules; a clean runtime reboot restored operation. No persistent application exception remained in the verified live screens.

Screenshots in `docs/screenshots/` capture the live dashboard and shortage staffing result. They are evidence of the tested screens, not a substitute for model validation against real observations.
