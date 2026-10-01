package ua.companion.health
import org.junit.Assert.*
import org.junit.Test
class BridgePolicyTest {
    @Test fun onlyThreeReads() { assertEquals(3,BridgePolicy.permissions.size);assertTrue(BridgePolicy.permissions.all { it.startsWith("android.permission.health.READ_") });assertEquals(listOf("sleep","steps","exercise"),BridgePolicy.types) }
    @Test fun absentIsNotZero() { assertEquals("PERMISSION_DENIED",BridgePolicy.status(false,false));assertEquals("MISSING",BridgePolicy.status(true,false));assertEquals("VALUE",BridgePolicy.status(true,true)) }
    @Test fun unknownStagesStayUnknown() { assertEquals("SOURCE_UNKNOWN",BridgePolicy.knownSleep(999));assertEquals("SDK_KNOWN",BridgePolicy.knownSleep(2)) }
    @Test fun originDoesNotClaimWatch() { assertEquals("SOURCE_APP_SAMSUNG_HEALTH",BridgePolicy.originClass("com.sec.android.app.shealth"));assertEquals("OTHER_SOURCE_APP",BridgePolicy.originClass("synthetic.source")) }
    @Test fun stagedCopyExpiresWithoutBackgroundReads() { assertFalse(BridgePolicy.exportExpired(1000,2000));assertTrue(BridgePolicy.exportExpired(1000,1000+BridgePolicy.exportTtlMillis+1));assertTrue(BridgePolicy.exportExpired(2000,1000)) }
    @Test fun bounded() { assertEquals(1000,BridgePolicy.maxRecords);assertEquals(1000000,BridgePolicy.maxBytes) }
}
