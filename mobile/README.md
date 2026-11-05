# FlowForge mobile — offline learning challenges

React Native + Expo SDK 57 client for iPhone, iPad, Android and web. It runs its discrete-event engine locally; no hosted simulation service or account is required. Notebook attempts persist with AsyncStorage. Sharing a notebook sends it only when the learner chooses the share action.

## Run

```sh
npm ci
npm test
npx expo start
# Scan with a compatible Expo Go installation, or use a development build.
npx expo export --platform all
```

The repository's Python/SimPy engine remains the engineering reference. `engine.mjs` implements the same arrival, resource, gamma service and pause/resume outage assumptions with a separate seeded PRNG. Exact samples and means differ from Python. `missions.json` is generated from `flowforge.challenges.MISSIONS`; do not independently change mission rules here.

## Build and publication status

The JavaScript engine and production bundles can be checked without store credentials. They do **not** prove device behavior or App Store acceptance. No signed iOS/Android binary, TestFlight upload, App Store submission or Google Play submission has been completed.

After the owner enrolls in the relevant developer programs and signs in to Expo:

```sh
npx eas-cli login
npx eas-cli build:configure
npx eas-cli build --platform ios --profile production
npx eas-cli submit --platform ios --profile production
```

The account owner must approve signing access and complete legal/payment steps. Confirm ownership and availability of `com.jabuniaj.flowforge` before the first store build. A physical-device accessibility, persistence, sharing, airplane-mode and small-screen pass remains required. Expo cloud builds require an Expo account; paid build usage needs separate approval.

See [the release checklist](../docs/MOBILE_RELEASE.md), [privacy policy](../docs/PRIVACY.md) and [draft store copy](../docs/STORE_LISTING.md).
