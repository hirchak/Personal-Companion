package ua.companion.health

object BridgePolicy {
    val types = listOf("sleep", "steps", "exercise")
    val permissions = setOf("android.permission.health.READ_SLEEP", "android.permission.health.READ_STEPS", "android.permission.health.READ_EXERCISE")
    const val maxRecords = 1000
    const val maxBytes = 1000000
    const val exportTtlMillis = 15 * 60 * 1000L
    fun exportExpired(lastWrite:Long,now:Long) = now < lastWrite || now-lastWrite > exportTtlMillis
    fun originClass(origin: String) = if (origin == "com.sec.android.app.shealth") "SOURCE_APP_SAMSUNG_HEALTH" else "OTHER_SOURCE_APP"
    fun knownSleep(stage: Int) = if (stage in 0..7) "SDK_KNOWN" else "SOURCE_UNKNOWN"
    fun status(granted: Boolean, present: Boolean) = if (!granted) "PERMISSION_DENIED" else if (present) "VALUE" else "MISSING"
}
