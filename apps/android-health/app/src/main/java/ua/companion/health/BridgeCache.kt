package ua.companion.health
import org.json.JSONObject
/** Cumulative replay survives delivery failure. No access to Health Connect/source mutation. */
object BridgeCache {
    fun upsert(records: JSONObject, record: JSONObject) { records.put(record.getString("source_id"),record) }
    fun delete(records: JSONObject,type:String,id:String) {
        val previous=records.optJSONObject(id)
        records.put(id,JSONObject().put("type",type).put("source_id",id).put("origin",previous?.optString("origin") ?: "").put("status","SOURCE_DELETED"))
    }
    fun recoveryUnknown(records:JSONObject,seen:Set<String>) {
        for(key in records.keys().asSequence().toList()) if(key !in seen) {
            val previous=records.getJSONObject(key)
            if(previous.optString("status")=="VALUE") previous.put("status","UNKNOWN")
        }
    }
}
