package ua.companion.health
import java.io.File
/** Fixed app-private artifacts only. Never derive a filename from source data or an Intent. */
object BridgeFiles {
    val names = listOf("bridge-state.json","bridge-export.json","bridge-probe.json")
    fun atomic(directory:File,name:String,text:String) {
        require(name in names);require(text.toByteArray().size<=BridgePolicy.maxBytes)
        val file=File(directory,name);val temp=File(directory,name+".writing")
        try {
            temp.outputStream().use { it.write(text.toByteArray());it.fd.sync() }
            check(temp.renameTo(file))
        } finally { temp.delete() }
    }
    fun discardInterrupted(directory:File) { names.forEach { File(directory,it+".writing").delete() } }
    fun clear(directory:File):Boolean {
        var complete=true
        names.forEach { name -> for(file in listOf(File(directory,name),File(directory,name+".writing"))) {
            if(file.exists() && !file.delete())complete=false
        } }
        return complete
    }
}
