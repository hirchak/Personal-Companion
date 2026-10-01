package ua.companion.health

import android.content.Intent
import android.os.Bundle
import android.widget.*
import androidx.activity.ComponentActivity
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.PermissionController
import androidx.health.connect.client.permission.HealthPermission
import androidx.health.connect.client.records.*
import androidx.health.connect.client.changes.*
import androidx.health.connect.client.request.*
import androidx.health.connect.client.time.TimeRangeFilter
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import kotlinx.coroutines.Job
import kotlinx.coroutines.CancellationException
import org.json.*
import java.io.File
import java.time.Instant
import java.time.temporal.ChronoUnit
import java.util.UUID
import kotlin.reflect.KClass

const val EXPLANATION = "Сон, кроки та активності: лише читання. Без запису, фонового читання, розширеної історії чи геолокації. Дані залишаються локально. AI не отримує health records. Імпортовані копії не змінюють ваш щоденник. Health Connect обмежує історію звичайного дозволу; відсутні дані не означають нуль."
class RationaleActivity: ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState);setContentView(TextView(this).apply { text=EXPLANATION;setPadding(24,40,24,24) }) }
}
class MainActivity: ComponentActivity() {
    private lateinit var status: TextView
    private var importJob: Job? = null
    private fun launchImport() { if(importJob?.isActive==true)return;importJob=lifecycleScope.launch { safeSync() } }
    override fun onStop() { importJob?.cancel();super.onStop() }
    private val recordTypes: Map<String,KClass<out Record>> = mapOf("sleep" to SleepSessionRecord::class,"steps" to StepsRecord::class,"exercise" to ExerciseSessionRecord::class)
    private val permissions = recordTypes.values.map { HealthPermission.getReadPermission(it) }.toSet()
    private val request = registerForActivityResult(PermissionController.createRequestPermissionResultContract()) { lifecycleScope.launch { capability() } }
    private val stateFile get() = File(filesDir,"bridge-state.json")
    private val exportFile get() = File(filesDir,"bridge-export.json")
    private val probeFile get() = File(filesDir,"bridge-probe.json")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val layout=LinearLayout(this).apply { orientation=LinearLayout.VERTICAL;setPadding(24,32,24,24) }
        layout.addView(TextView(this).apply { text="Дані з Health Connect";textSize=26f })
        layout.addView(TextView(this).apply { text=EXPLANATION;textSize=16f })
        status=TextView(this).apply { text="Перевіряємо доступність…";textSize=18f };layout.addView(status)
        fun button(label: String, action: ()->Unit) { layout.addView(Button(this).apply { text=label;minHeight=56;setOnClickListener { action() } }) }
        button("Дозволити читання трьох типів") { if (HealthConnectClient.getSdkStatus(this)==HealthConnectClient.SDK_AVAILABLE) request.launch(permissions) else status.text="Health Connect потребує встановлення або оновлення власником." }
        button("Перевірити доступ / імпортувати") { launchImport() }
        button("Керувати дозволами Health Connect") { try { startActivity(Intent(HealthConnectClient.ACTION_HEALTH_CONNECT_SETTINGS)) } catch (_: Exception) { status.text="Відкрийте Health Connect у системних налаштуваннях." } }
        button("Видалити локальні файли bridge") { android.app.AlertDialog.Builder(this).setMessage("Видалити лише копії bridge? Health Connect originals залишаться. Для нового читання потрібна явна дія імпорту.").setPositiveButton("Видалити") { _,_->stateFile.delete();exportFile.delete();probeFile.delete();status.text="Локальні копії bridge видалено. Оригінали збережено." }.setNegativeButton("Скасувати",null).show() }
        setContentView(ScrollView(this).apply { addView(layout) })
        lifecycleScope.launch { capability();if(intent.action=="ua.companion.health.IMPORT")launchImport() }
    }
    override fun onResume() { super.onResume();if (::status.isInitialized) lifecycleScope.launch { capability() } }
    override fun onNewIntent(intent: Intent) { super.onNewIntent(intent);setIntent(intent);if(intent.action=="ua.companion.health.IMPORT")launchImport() }
    private suspend fun safeSync() { try { sync() } catch (cancel: CancellationException) { throw cancel } catch (_: Exception) { status.text="Імпорт не завершено. Локальну копію збережено; повторіть вручну." } }
    private fun atomic(file: File, text: String) { require(text.toByteArray().size<=BridgePolicy.maxBytes);val temp=File(filesDir,file.name+".writing");temp.outputStream().use { it.write(text.toByteArray());it.fd.sync() };check(temp.renameTo(file)) }
    private suspend fun capability(): Set<String> {
        if(exportFile.exists() && BridgePolicy.exportExpired(exportFile.lastModified(),System.currentTimeMillis()))exportFile.delete()
        val available=HealthConnectClient.getSdkStatus(this)
        val granted=if (available==HealthConnectClient.SDK_AVAILABLE) try { HealthConnectClient.getOrCreate(this).permissionController.getGrantedPermissions() } catch (_: Exception) { emptySet() } else emptySet()
        val probe=JSONObject().put("schema_version",1).put("health_connect",if(available==HealthConnectClient.SDK_AVAILABLE) "AVAILABLE" else if(available==HealthConnectClient.SDK_UNAVAILABLE_PROVIDER_UPDATE_REQUIRED) "UPDATE_REQUIRED" else "UNAVAILABLE").put("api_level",android.os.Build.VERSION.SDK_INT).put("bridge_version","0.6.1-debug").put("write_permissions","NONE").put("background_history_location_permissions","NONE")
        val states=JSONObject();for ((type,record) in recordTypes) states.put(type,if(granted.contains(HealthPermission.getReadPermission(record))) "GRANTED" else "PERMISSION_DENIED")
        probe.put("permissions",states);atomic(probeFile,probe.toString())
        status.text="Health Connect: ${probe.getString("health_connect")}\nСон: ${states.getString("sleep")}\nКроки: ${states.getString("steps")}\nАктивності: ${states.getString("exercise")}\nДані з годинника не є клінічним вимірюванням."
        return granted
    }
    private fun normalized(type: String, r: Record): JSONObject {
        val fields=JSONObject();val start:Instant;val end:Instant;val startOffset:java.time.ZoneOffset?;val endOffset:java.time.ZoneOffset?
        when(r) {
            is SleepSessionRecord -> { start=r.startTime;end=r.endTime;startOffset=r.startZoneOffset;endOffset=r.endZoneOffset
                val stages=JSONArray();r.stages.forEach { stages.put(JSONObject().put("start",it.startTime.toString()).put("end",it.endTime.toString()).put("stage",it.stage).put("classification",BridgePolicy.knownSleep(it.stage))) };fields.put("stages",stages).put("stages_state",if(r.stages.isEmpty()) "MISSING" else "VALUE") }
            is StepsRecord -> { start=r.startTime;end=r.endTime;startOffset=r.startZoneOffset;endOffset=r.endZoneOffset;fields.put("count",r.count).put("unit","count") }
            is ExerciseSessionRecord -> { start=r.startTime;end=r.endTime;startOffset=r.startZoneOffset;endOffset=r.endZoneOffset;fields.put("exercise_type",r.exerciseType).put("classification","SOURCE_CODE") }
            else -> error("UNAUTHORIZED_TYPE")
        }
        return JSONObject().put("type",type).put("source_id",r.metadata.id).put("origin",r.metadata.dataOrigin.packageName).put("modified",r.metadata.lastModifiedTime.toString()).put("start",start.toString()).put("end",end.toString()).put("start_offset",startOffset?.totalSeconds ?: JSONObject.NULL).put("end_offset",endOffset?.totalSeconds ?: JSONObject.NULL).put("fields",fields).put("status","VALUE")
    }
    private suspend fun initial(client:HealthConnectClient,type:String,floor:Instant):List<Record> {
        val range=TimeRangeFilter.between(floor,Instant.now());var page:String?=null;val records=mutableListOf<Record>()
        do {
            when(type) {
                "sleep" -> { val r=client.readRecords(ReadRecordsRequest(SleepSessionRecord::class,range,pageSize=250,pageToken=page));records.addAll(r.records);page=r.pageToken }
                "steps" -> { val r=client.readRecords(ReadRecordsRequest(StepsRecord::class,range,pageSize=250,pageToken=page));records.addAll(r.records);page=r.pageToken }
                "exercise" -> { val r=client.readRecords(ReadRecordsRequest(ExerciseSessionRecord::class,range,pageSize=250,pageToken=page));records.addAll(r.records);page=r.pageToken }
            }
            check(records.size<=BridgePolicy.maxRecords)
        } while(page!=null)
        return records
    }
    private suspend fun sync() {
        val began=System.nanoTime();val granted=capability()
        if(HealthConnectClient.getSdkStatus(this)!=HealthConnectClient.SDK_AVAILABLE)return
        val client=HealthConnectClient.getOrCreate(this)
        val state=if(stateFile.exists()) JSONObject(stateFile.readText()) else JSONObject().put("epoch",UUID.randomUUID().toString()).put("sequence",0).put("scopes",JSONObject())
        val scopes=state.getJSONObject("scopes");val transfers=JSONArray();val probe=JSONObject(probeFile.readText());val presence=JSONObject();val origins=mutableSetOf<String>()
        for ((type,recordType) in recordTypes) {
            val old=scopes.optJSONObject(type) ?: JSONObject().put("records",JSONObject())
            val current=JSONObject(old.toString());val records=current.getJSONObject("records")
            var scopeStatus="PERMISSION_DENIED";var mode="INCREMENTAL"
            if(granted.contains(HealthPermission.getReadPermission(recordType))) try {
                var token=current.optString("token","")
                var floor=if(current.has("floor")) Instant.parse(current.getString("floor")) else Instant.now().minus(29,ChronoUnit.DAYS)
                suspend fun reload() {
                    floor=Instant.now().minus(29,ChronoUnit.DAYS)
                    val freshToken=client.getChangesToken(ChangesTokenRequest(setOf(recordType)))
                    val found=initial(client,type,floor);val seen=found.map { it.metadata.id }.toSet()
                    BridgeCache.recoveryUnknown(records,seen)
                    found.forEach { BridgeCache.upsert(records,normalized(type,it)) };token=freshToken;mode="INITIAL_OR_RECOVERY"
                }
                if(token.isEmpty())reload()
                var more:Boolean;var pages=0
                do {
                    check(++pages<=40)
                    val response=try { client.getChanges(token) } catch (_: IllegalArgumentException) { reload();client.getChanges(token) }
                    if(response.changesTokenExpired) { reload();break }
                    response.changes.forEach { change -> when(change) {
                        is UpsertionChange -> BridgeCache.upsert(records,normalized(type,change.record))
                        is DeletionChange -> BridgeCache.delete(records,type,change.recordId)
                    } }
                    token=response.nextChangesToken;more=response.hasMore
                    check(records.length()<=BridgePolicy.maxRecords)
                } while(more)
                // Check revocation again before publishing private staged data.
                check(client.permissionController.getGrantedPermissions().contains(HealthPermission.getReadPermission(recordType)))
                current.put("token",token).put("floor",floor.toString());scopes.put(type,current);scopeStatus="GRANTED"
            } catch (cancel: CancellationException) { throw cancel } catch (_: SecurityException) { scopeStatus="PERMISSION_DENIED" } catch (_: Exception) { scopeStatus="READ_FAILED" }
            val output=JSONArray();if(scopeStatus=="GRANTED") for(key in records.keys()) { val r=records.getJSONObject(key);output.put(r);if(r.optString("status")=="VALUE")origins.add(BridgePolicy.originClass(r.getString("origin"))) }
            presence.put(type,if(scopeStatus!="GRANTED") "NOT_READ" else if((0 until output.length()).any { output.getJSONObject(it).getString("status")=="VALUE" }) "YES" else "NO")
            transfers.put(JSONObject().put("type",type).put("permission",scopeStatus).put("mode",mode).put("records",output))
        }
        state.put("sequence",state.getLong("sequence")+1)
        val payload=JSONObject().put("schema_version",1).put("source_system","HEALTH_CONNECT").put("epoch",state.getString("epoch")).put("sequence",state.getLong("sequence")).put("scopes",transfers)
        // Entire durable cache plus tombstones is replayable; tokens stay app-private.
        val encoded=payload.toString();check(encoded.toByteArray().size<=BridgePolicy.maxBytes)
        atomic(stateFile,state.toString());atomic(exportFile,encoded)
        probe.put("record_availability",presence).put("source_classes",JSONArray(origins.toList())).put("hardware_origin","NOT_VERIFIED").put("import_duration_bucket",if((System.nanoTime()-began)/1000000<1000) "LT_1S" else "GE_1S").put("export_ready",true)
        atomic(probeFile,probe.toString());status.text="Локальна копія готова для USB-перенесення.\nСон: ${presence.getString("sleep")}\nКроки: ${presence.getString("steps")}\nАктивності: ${presence.getString("exercise")}\nБез запису в Health Connect."
    }
}
