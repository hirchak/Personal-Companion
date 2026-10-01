package ua.companion.health
import java.io.File
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
class BridgeFilesTest {
    @get:Rule val temp=TemporaryFolder()
    @Test fun atomicCopyIsDurableAndNoPartialFileRemains() { val dir=temp.newFolder();BridgeFiles.atomic(dir,"bridge-export.json","SYNTHETIC old");BridgeFiles.atomic(dir,"bridge-export.json","SYNTHETIC new");assertEquals("SYNTHETIC new",File(dir,"bridge-export.json").readText());assertFalse(File(dir,"bridge-export.json.writing").exists()) }
    @Test fun cleanupRemovesOnlyOwnedCopiesAndInterruptedFiles() { val dir=temp.newFolder();for(name in BridgeFiles.names){File(dir,name).writeText("SYNTHETIC");File(dir,name+".writing").writeText("SYNTHETIC partial")};val other=File(dir,"SYNTHETIC-other");other.writeText("SYNTHETIC keep");assertTrue(BridgeFiles.clear(dir));assertEquals(listOf("SYNTHETIC-other"),dir.list()!!.toList());assertEquals("SYNTHETIC keep",other.readText()) }
    @Test fun restartDiscardsPartialWithoutDeletingCommittedState() { val dir=temp.newFolder();File(dir,"bridge-state.json").writeText("SYNTHETIC checkpoint");File(dir,"bridge-state.json.writing").writeText("SYNTHETIC partial");BridgeFiles.discardInterrupted(dir);assertEquals("SYNTHETIC checkpoint",File(dir,"bridge-state.json").readText());assertFalse(File(dir,"bridge-state.json.writing").exists()) }
    @Test fun oversizedOrUnknownFileCannotReplaceCommittedCopy() { val dir=temp.newFolder();BridgeFiles.atomic(dir,"bridge-export.json","SYNTHETIC before");for(pair in listOf("bridge-export.json" to "x".repeat(BridgePolicy.maxBytes+1),"../SYNTHETIC-outside" to "SYNTHETIC")){try{BridgeFiles.atomic(dir,pair.first,pair.second);fail("must reject")}catch(_:IllegalArgumentException){}};assertEquals("SYNTHETIC before",File(dir,"bridge-export.json").readText());assertFalse(File(dir,"bridge-export.json.writing").exists()) }
    @Test fun failedWriteCleansItsOwnedTemporaryArtifact() { val dir=temp.newFolder();File(dir,"bridge-state.json.writing").mkdir();try{BridgeFiles.atomic(dir,"bridge-state.json","SYNTHETIC");fail("must fail")}catch(_:java.io.IOException){};assertFalse(File(dir,"bridge-state.json.writing").exists()) }
}
