# Personal Companion Health — debug native bridge

Minimal Kotlin/Health Connect foreground reader. No PWA rewrite, network, cloud, writes or routes.
Only SleepSessionRecord / StepsRecord / ExerciseSessionRecord read permissions. Owner manually
confirms permission UI; denial/revoke is normal. App-private cache/tokens, bounded staging and explicit
cleanup. No values/IDs in logs. Android backup disabled. Main/Rationale/permission-use activities
are exported only for standard launcher/Health Connect UI; no broad services/providers/receivers.

Build from repository root:

```bash
.venv/bin/python scripts/bootstrap_android.py
apps/android-health/gradlew :app:assembleDebug :app:testDebugUnitTest
```

All SDK/JDK/Gradle/Maven caches and debug signing key are under ignored generated/android-tools;
no sudo/Homebrew/global install, certificate changes or release signing. If a needed system component
cannot be obtained project-locally, stop and report it. Wrapper uses project-local Gradle8.13.
Pinned app dependencies: AGP8.9.2, Kotlin2.1.20, Health Connect1.1.0, compileSdk36, minSdk28, target35.
Installed early 0.6.0-debug hardware gate is historical; final 0.6.1-debug rebuild/unit verified.
Later cancellation/expiry/recovery hardware paths NOT_RUN after owner released phone.

[Galaxy runbook](../../docs/M6_GALAXY_HEALTH_GATE.md),
[provenance/checkpoint ADR](../../docs/adr/ADR-006-M6-HEALTH-BRIDGE.md).
