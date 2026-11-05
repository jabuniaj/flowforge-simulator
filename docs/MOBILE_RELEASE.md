# Mobile release status

## Product

Audience: students learning operations through interactive decisions. FlowForge is an educational warehouse challenge app, not a production dispatch system. Three missions teach staffing allocation, equipment constraints and availability. Learners predict, test, replay queues and keep an experiment notebook.

The existing Streamlit deployment hosts the Python challenge room and free simulator. The `mobile/` client uses native React Native controls and a local event engine. It is not a web page embedded inside a native shell.

## Prepared

- iPhone/iPad/Android Expo application source, app icons and portrait layout.
- Local simulation, seed-controlled trials, budget/team validation and queue playback.
- Persistent device notebook, explicit sharing and no account requirement.
- EAS preview/production configuration and proposed bundle IDs.
- Draft store listing, privacy policy and test checklist.

## Required before submission

1. Owner enrolls in the [Apple Developer Program](https://developer.apple.com/programs/enroll/), completes identity verification, agreements and payment. Apple currently lists $99 USD/year, varying by region.
2. Owner signs into an Expo account and approves the specific build/signing access. Do not store credentials in the repository.
3. Confirm bundle ID ownership and create the App Store Connect app record.
4. Generate a signed production build and distribute through TestFlight.
5. Test on physical iPhone and iPad: airplane-mode simulation, ten runs without UI stalls, kill/relaunch notebook persistence, share sheet, VoiceOver, large text, small-screen controls and safe areas.
6. Capture screenshots from the actual tested devices; provide support/privacy URLs and accurate age-rating/privacy answers.
7. Owner reviews final metadata, then submit and address Apple's review findings. Acceptance and publication cannot be guaranteed.
8. For Google Play, obtain its developer account and satisfy the testing and review requirements shown for that account before submission.

No store enrollment, signed binary, paid build, device validation or submission is represented as complete. A passing bundle export is a packaging check, not a substitute for native testing.

References: [Expo store builds](https://docs.expo.dev/deploy/build-project/), [Apple review guidelines](https://developer.apple.com/app-store/review/guidelines/).
