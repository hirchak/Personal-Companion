package ua.companion.health
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
class BridgeCacheTest {
    private fun record(id:String="SYNTHETIC-id",status:String="VALUE") = JSONObject().put("source_id",id).put("origin","synthetic.origin").put("type","steps").put("status",status).put("fields",JSONObject().put("count",42))
    @Test fun repeatAndUpdateUseStableSourceId() { val r=JSONObject();BridgeCache.upsert(r,record());BridgeCache.upsert(r,record());assertEquals(1,r.length());BridgeCache.upsert(r,record().put("fields",JSONObject().put("count",99)));assertEquals(99,r.getJSONObject("SYNTHETIC-id").getJSONObject("fields").getInt("count")) }
    @Test fun deletionRetainsOnlyIdentityAndOrigin() { val r=JSONObject();BridgeCache.upsert(r,record());BridgeCache.delete(r,"steps","SYNTHETIC-id");assertEquals("SOURCE_DELETED",r.getJSONObject("SYNTHETIC-id").getString("status"));assertFalse(r.getJSONObject("SYNTHETIC-id").has("fields"));BridgeCache.delete(r,"steps","SYNTHETIC-unknown");assertEquals(2,r.length()) }
    @Test fun expiredWindowDoesNotInventDeletion() { val r=JSONObject();BridgeCache.upsert(r,record());BridgeCache.upsert(r,record("SYNTHETIC-recent"));BridgeCache.recoveryUnknown(r,setOf("SYNTHETIC-recent"));assertEquals("UNKNOWN",r.getJSONObject("SYNTHETIC-id").getString("status"));assertEquals("VALUE",r.getJSONObject("SYNTHETIC-recent").getString("status")) }
    @Test fun tombstoneIsNotChangedByRecovery() { val r=JSONObject();BridgeCache.upsert(r,record());BridgeCache.delete(r,"steps","SYNTHETIC-id");BridgeCache.recoveryUnknown(r,emptySet());assertEquals("SOURCE_DELETED",r.getJSONObject("SYNTHETIC-id").getString("status")) }
    @Test fun cumulativeSnapshotSurvivesRestartAndTransferRetry() { val r=JSONObject();BridgeCache.upsert(r,record());BridgeCache.delete(r,"steps","SYNTHETIC-id");val restart=JSONObject(r.toString());assertEquals("SOURCE_DELETED",restart.getJSONObject("SYNTHETIC-id").getString("status"));BridgeCache.upsert(restart,record("SYNTHETIC-other"));assertEquals(2,restart.length()) }
}
