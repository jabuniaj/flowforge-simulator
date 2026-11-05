# Release validation — November 5, 2026

## Student challenge and mobile release, 0.3.0

- 31 local Python tests pass, including the full prediction/decision/reveal loop and shared mission-rule checks.
- Seven offline JavaScript engine tests pass. All three reference plans meet their mission goals within their budgets.
- Expo production JavaScript bundles export for iOS, Android and web. This is not a signed native application build.
- At a 390×844 browser viewport, the mobile client rendered readable mission briefs and touch controls. A 3/2/2 assignment solved mission 01; queue playback advanced through actual simulated snapshots.
- Browser reload retained solved-mission progress and notebook attempts in the mobile client's local storage. This verifies the browser implementation; native-device persistence and sharing still require physical-device checks.
- The public Streamlit challenge room rendered, accepted worker reassignment, showed a solved mission, and played the queue trace through the final snapshot.
- Prior deployment CI passed both Python and mobile build jobs; the final update uses the same workflow.
- No Apple membership, native signing, TestFlight installation, App Store review or Google Play release has been completed. The owner confirmed Apple enrollment is still needed.

Current screenshots: `challenge-room.jpg` shows the live web mission; `mobile-preview.jpg` shows the native client's **web preview**, not a physical iPhone capture.

## Earlier engineering dashboard release

- Local Python 3.12: 24 pytest checks passed, including model, Streamlit interaction and export/replay tests.
- GitHub Actions: initial 22-check release passed on Python 3.11; the subsequent replay additions run through the same workflow.
- Existing Streamlit Community Cloud deployment rebuilt from the existing repository's `main` branch.
- Cloud Python 3.14: normal-shift dashboard and queue/resource charts rendered.
- Live absence scenario: staffing search selected 3/2/2 and reported 156.6 → 283.2 mean completions on validation seeds 200–209 with equal $1,120 wages.
- Live 5/3/2 setting: capacity reference displayed 480/480/480 and all three station names.
- Downloaded an actual live ZIP report and replayed baseline and stress runs locally. Integer completions matched exactly; numeric results matched within 1e-10 relative or 1e-8 absolute tolerance. Platform-level float rounding prevented bitwise equality.
- Cloud dependency refresh briefly loaded mixed pandas modules; a clean runtime reboot restored operation. No persistent application exception remained in the verified live screens.

Screenshots in `docs/screenshots/` capture the live dashboard and shortage staffing result. They are evidence of the tested screens, not a substitute for model validation against real observations.
