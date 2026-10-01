plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android {
    namespace = "ua.companion.health"
    compileSdk = 36
    defaultConfig { applicationId = "ua.companion.health"; minSdk = 28; targetSdk = 35; versionCode = 2; versionName = "0.6.1-debug" }
    buildTypes { release { isMinifyEnabled = false } }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
    testOptions { unitTests.isReturnDefaultValues = true }
}
dependencies {
    implementation("androidx.activity:activity-ktx:1.10.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.health.connect:connect-client:1.1.0")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.json:json:20240303")
}
