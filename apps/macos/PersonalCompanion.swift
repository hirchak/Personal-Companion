import AppKit
import WebKit
import LocalAuthentication
import AVFoundation
import Sparkle

enum NativeFailure: Error { case unavailable }

// Supported Sparkle user-driver interface. One explicit Update choice, then
// verified download/extraction/install/relaunch without a second install click.
final class UpdateUI: NSObject, SPUUserDriver {
    weak var owner: Companion?
    var received: UInt64=0, expected: UInt64=0
    func show(_ request:SPUUpdatePermissionRequest,reply:@escaping(SUUpdatePermissionResponse)->Void) {
        reply(SUUpdatePermissionResponse(automaticUpdateChecks:false,sendSystemProfile:false))
    }
    func showUserInitiatedUpdateCheck(cancellation:@escaping()->Void) {owner?.state.stringValue="Перевіряємо локальний підписаний канал…"}
    func showUpdateFound(with appcastItem:SUAppcastItem,state:SPUUserUpdateState,reply:@escaping(SPUUserUpdateChoice)->Void) {
        let alert=NSAlert();alert.messageText="Доступна нова версія"
        alert.informativeText="Перед встановленням перевіримо копію даних і відновлення. Натисніть «Оновити»: програма збереже дані, перевірить пакет і перезапуститься."
        alert.addButton(withTitle:"Оновити");alert.addButton(withTitle:"Пізніше")
        guard alert.runModal() == .alertFirstButtonReturn,let owner=owner else {reply(.dismiss);return}
        owner.prepareChosenUpdate {ok in reply(ok ? .install : .dismiss)}
    }
    func showUpdateReleaseNotes(with downloadData:SPUDownloadData) {}
    func showUpdateReleaseNotesFailedToDownloadWithError(_ error:Error) {}
    func showUpdateNotFoundWithError(_ error:Error,acknowledgement:@escaping()->Void) {
        owner?.settledUpdateText="Нової версії немає. Поточний простір збережено.";owner?.testEvent("update-not-found");acknowledgement()
    }
    func showUpdaterError(_ error:Error,acknowledgement:@escaping()->Void) {
        owner?.presentUpdateFailure();acknowledgement()
    }
    func showDownloadInitiated(cancellation:@escaping()->Void) {received=0;expected=0;owner?.state.stringValue="Завантажуємо локальний пакет…"}
    func showDownloadDidReceiveExpectedContentLength(_ expectedContentLength:UInt64) {expected=expectedContentLength}
    func showDownloadDidReceiveData(ofLength length:UInt64) {
        received+=length
        if expected>0 {owner?.state.stringValue="Оновлення: \(min(100,Int(Double(received)*100/Double(expected))))% · дані збережено"}
    }
    func showDownloadDidStartExtractingUpdate() {owner?.state.stringValue="Підпис перевірено. Готуємо нову програму…"}
    func showExtractionReceivedProgress(_ progress:Double) {owner?.state.stringValue="Готуємо нову програму: \(Int(progress*100))%"}
    func showReady(toInstallAndRelaunch reply:@escaping(SPUUserUpdateChoice)->Void) {reply(.install)}
    func showInstallingUpdate(withApplicationTerminated applicationTerminated:Bool,retryTerminatingApplication:@escaping()->Void) {owner?.state.stringValue="Встановлюємо й перезапускаємо…"}
    func showUpdateInstalledAndRelaunched(_ relaunched:Bool,acknowledgement:@escaping()->Void) {acknowledgement()}
    func dismissUpdateInstallation() {}
    func showUpdateInFocus() {owner?.window.makeKeyAndOrderFront(nil)}
}

// A private inherited pipe, no socket/credential arguments or console logging.
final class Backend {
    let process = Process(), input = Pipe(), output = Pipe()
    var serial = 0
    private let mutex=NSLock()
    private let operations=DispatchQueue(label:"personal-companion.backend-maintenance",qos:.userInitiated)
    init(bundle: URL, base: URL) throws {
        let runtime = bundle.appendingPathComponent("Contents/Resources/runtime")
        process.executableURL = runtime.appendingPathComponent("bin/python3.13")
        process.arguments = ["-I", "-B", bundle.appendingPathComponent("Contents/Resources/payload/native_entry.py").path]
        process.environment = ["PATH":"/var/empty", "HOME":base.deletingLastPathComponent().path,
                               "LANG":"uk_UA.UTF-8", "PYTHONDONTWRITEBYTECODE":"1"]
        process.currentDirectoryURL = bundle.appendingPathComponent("Contents/Resources/payload")
        process.standardInput = input; process.standardOutput = output
        process.standardError = FileHandle.nullDevice
        try process.run()
        _ = try call("bootstrap", ["bundle":bundle.path, "base":base.path])
    }
    func call(_ op: String, _ fields: [String:Any] = [:]) throws -> [String:Any] {
        mutex.lock();defer {mutex.unlock()}
        guard process.isRunning else { throw NativeFailure.unavailable }
        serial += 1
        var value = fields; value["op"] = op; value["id"] = serial
        var bytes = try JSONSerialization.data(withJSONObject:value); bytes.append(10)
        try input.fileHandleForWriting.write(contentsOf:bytes)
        var reply = Data()
        // One inherited pipe conversation at a time, independent of caller thread.
        while reply.count < 32768 {
            let chunk = try output.fileHandleForReading.read(upToCount:1) ?? Data()
            guard !chunk.isEmpty else { throw NativeFailure.unavailable }
            if chunk[0] == 10 { break }
            reply.append(chunk)
        }
        guard let object = try JSONSerialization.jsonObject(with:reply) as? [String:Any],
              object["id"] as? Int == serial, object["ok"] as? Bool == true,
              let result = object["result"] as? [String:Any] else { throw NativeFailure.unavailable }
        return result
    }
    func perform(_ work:@escaping(Backend)throws->[String:Any],completion:@escaping(Result<[String:Any],Error>)->Void) {
        operations.async {
            let result=Result {try work(self)}
            DispatchQueue.main.async {completion(result)}
        }
    }
    func quit() {
        mutex.lock();defer {mutex.unlock()}
        try? input.fileHandleForWriting.close()
        if process.isRunning {
            let deadline = Date().addingTimeInterval(18)
            while process.isRunning && Date()<deadline { Thread.sleep(forTimeInterval:0.02) }
            if process.isRunning { process.terminate() }
        }
        try? output.fileHandleForReading.close()
    }
    deinit { quit() }
}

final class Companion: NSObject, NSApplicationDelegate, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler, SPUUpdaterDelegate {
    let bundle = Bundle.main.bundleURL
    let openedAt = ProcessInfo.processInfo.systemUptime
    var base: URL!
    var backend: Backend?
    var window: NSWindow!
    var web: WKWebView!
    var content: NSView!
    let state = NSTextField(labelWithString:"Дані на цьому Mac · AI вимкнений")
    var openButton: NSButton!
    var updater: SPUUpdater?
    var updateUI: UpdateUI?
    var port: Int = 0
    var prepared = false
    var installing = false
    var maintenanceBusy = false
    var maintenancePulses = 0
    var maintenanceTimer: Timer?
    let progress=NSProgressIndicator()
    var pendingTarget:[String:Any]?
    var updateFailed=false
    var settledUpdateText:String?
    var resumeQueued=false
    var closingPending=false
    var observers: [NSObjectProtocol] = []

    func testEvent(_ name:String,_ fields:[String:Any]=[:]) {
        #if LOCAL_TEST
        guard let base=base else {return}
        // Only known mechanism states and public appcast field names, never
        // note text, credentials, account fields or provider output.
        var event=fields;event["event"]=name
        event["build"]=Bundle.main.object(forInfoDictionaryKey:"CFBundleVersion")
        guard var data=try? JSONSerialization.data(withJSONObject:event) else {return}
        data.append(10)
        let url=base.deletingLastPathComponent().appendingPathComponent("native-events.jsonl")
        if !FileManager.default.fileExists(atPath:url.path) {FileManager.default.createFile(atPath:url.path,contents:nil,attributes:[.posixPermissions:0o600])}
        if let handle=try? FileHandle(forWritingTo:url) {_ = try? handle.seekToEnd();try? handle.write(contentsOf:data);try? handle.close()}
        #endif
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Focus an existing native instance; never spawn another data writer.
        let identifier = Bundle.main.bundleIdentifier!
        if let existing = NSRunningApplication.runningApplications(withBundleIdentifier:identifier)
            .first(where:{$0.processIdentifier != ProcessInfo.processInfo.processIdentifier}) {
            existing.activate(options:[.activateAllWindows]); NSApp.terminate(nil); return
        }
        #if LOCAL_TEST
        guard let test = Bundle.main.object(forInfoDictionaryKey:"PCTestHome") as? String,
              test.hasPrefix("/private/tmp/m8f-"), !test.contains("..") else {
            NSApp.terminate(nil); return
        }
        base = URL(fileURLWithPath:test).appendingPathComponent("Standalone")
        setenv("CFFIXED_USER_HOME",test,1);setenv("HOME",test,1)
        #else
        base = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support/PersonalCompanionStandalone")
        #endif
        buildWindow(); buildMenu()
        do {
            backend = try Backend(bundle:bundle,base:base)
            let status = try backend!.call("status")
            if status["initialized"] as? Bool == true { try start() }
            else { welcome() }
        } catch { problem("Не вдалося відкрити локальне сховище. Дані збережено. Перевірте FileVault, права папки або скористайтеся відновленням.") }
        let nc = NSWorkspace.shared.notificationCenter
        for name in [NSWorkspace.willSleepNotification, NSWorkspace.sessionDidResignActiveNotification] {
            observers.append(nc.addObserver(forName:name,object:nil,queue:.main) { [weak self] _ in self?.lock() })
        }
        #if LOCAL_TEST
        updateUI=UpdateUI();updateUI!.owner=self
        updater=SPUUpdater(hostBundle:Bundle.main,applicationBundle:Bundle.main,userDriver:updateUI!,delegate:self)
        do {try updater!.start()} catch {state.stringValue="Локальний канал оновлень недоступний."}
        #endif
        window.makeKeyAndOrderFront(nil); NSApp.activate(ignoringOtherApps:true)
        testEvent("window-ready",["process_to_window_ms":Int((ProcessInfo.processInfo.systemUptime-openedAt)*1000)])
    }

    func buildWindow() {
        window = NSWindow(contentRect:NSRect(x:0,y:0,width:1160,height:820),
            styleMask:[.titled,.closable,.miniaturizable,.resizable],backing:.buffered,defer:false)
        window.title = "Personal Companion"
        #if LOCAL_TEST
        window.title += " — ORIGINAL SYNTHETIC TEST"
        #endif
        window.minSize = NSSize(width:760,height:600); window.center()
        let root = NSView(); window.contentView = root
        let bar = NSStackView(); bar.orientation = .horizontal; bar.spacing = 12
        bar.translatesAutoresizingMaskIntoConstraints = false
        state.textColor = NSColor(calibratedRed:0.22,green:0.32,blue:0.27,alpha:1)
        state.setContentCompressionResistancePriority(.defaultLow,for:.horizontal)
        bar.addArrangedSubview(state)
        progress.style = .spinning;progress.controlSize = .small;progress.isDisplayedWhenStopped=false
        bar.addArrangedSubview(progress)
        openButton = NSButton(title:"Відкрити простір",target:self,action:#selector(unlock));openButton.bezelStyle = .rounded
        bar.addArrangedSubview(openButton)
        let lockButton=NSButton(title:"Заблокувати",target:self,action:#selector(lock));lockButton.bezelStyle = .rounded
        bar.addArrangedSubview(lockButton)
        content = NSView();content.translatesAutoresizingMaskIntoConstraints = false
        root.addSubview(bar);root.addSubview(content)
        NSLayoutConstraint.activate([
            bar.leadingAnchor.constraint(equalTo:root.leadingAnchor,constant:16),
            bar.trailingAnchor.constraint(equalTo:root.trailingAnchor,constant:-16),
            bar.topAnchor.constraint(equalTo:root.topAnchor,constant:10),
            content.leadingAnchor.constraint(equalTo:root.leadingAnchor),content.trailingAnchor.constraint(equalTo:root.trailingAnchor),
            content.topAnchor.constraint(equalTo:bar.bottomAnchor,constant:10),content.bottomAnchor.constraint(equalTo:root.bottomAnchor)])
        let config=WKWebViewConfiguration();config.websiteDataStore = .nonPersistent()
        config.userContentController.add(self,name:"companion")
        #if LOCAL_TEST
        // No physical microphone access, even with a pre-existing TCC grant.
        let syntheticMedia="""
        (()=>{window.__pcSyntheticCapture=false;window.__pcSyntheticMode='normal';
        const nativeFetch=window.fetch.bind(window);let releaseSave=null;
        window.__pcReleaseSyntheticSave=()=>{releaseSave?.();releaseSave=null;};
        window.fetch=async(input,...args)=>{
          if(window.__pcSyntheticMode==='save-held'&&String(input).startsWith('/api/v1/voice/audio'))
            await new Promise(resolve=>{releaseSave=resolve;});
          return nativeFetch(input,...args);
        };
        const trace=(stage,state='',context_id=0)=>window.webkit.messageHandlers.companion.postMessage({
          kind:'voice-trace',stage,state,context_id,t_ms:Math.round(performance.now()),
          gesture:navigator.userActivation?(navigator.userActivation.isActive?'ACTIVE':'INACTIVE'):'UNSUPPORTED',
          hidden:document.hidden});
        let contextId=0;const NativeAudioContext=window.AudioContext;
        window.AudioContext=class extends NativeAudioContext {
          constructor(...args){super(...args);this.traceId=++contextId;trace('context-created',this.state,this.traceId);
            this.addEventListener('statechange',()=>trace('context-state',this.state,this.traceId));
            setTimeout(()=>trace('context-pending-check',this.state,this.traceId),2000);}
          resume(){trace('resume-requested',this.state,this.traceId);const result=super.resume();
            result.then(()=>trace('resume-resolved',this.state,this.traceId),()=>trace('resume-rejected',this.state,this.traceId));return result;}
        };
        let last='';new MutationObserver(()=>{const state=document.querySelector('[data-voice-state]')?.getAttribute('data-voice-state');
          if(state&&state!==last){last=state;trace('ui-state',state);}}).observe(document,{subtree:true,attributes:true,attributeFilter:['data-voice-state']});
        navigator.mediaDevices.getUserMedia=async constraints=>{
          trace('fixture-requested');
          if(!window.__pcSyntheticCapture||constraints.video)throw new DOMException('Synthetic test microphone denied','NotAllowedError');
          if(window.__pcSyntheticMode==='never')return new Promise(()=>{});
          const context=new AudioContext();let source=null;let timer;let disposed=false;
          const cleanup=()=>{if(disposed)return;disposed=true;try{source?.stop()}catch{}void context.close().catch(()=>{});};
          const activated=context.resume();activated.catch(()=>{});
          const deadline=new Promise((_,reject)=>{timer=setTimeout(()=>{cleanup();reject(new DOMException('Synthetic fixture timed out','TimeoutError'));},45000);});
          const ready=(async()=>{const response=await fetch('/native-test-audio.wav');
          trace('fixture-fetched',context.state,context.traceId);
          const buffer=await context.decodeAudioData(await response.arrayBuffer());
          trace('fixture-decoded',context.state,context.traceId);
          source=context.createBufferSource();source.buffer=buffer;source.loop=true;
          const destination=context.createMediaStreamDestination();source.connect(destination);source.start();
          trace('fixture-wired',context.state,context.traceId);await activated;
          const track=destination.stream.getAudioTracks()[0],stop=track.stop.bind(track);
          track.stop=()=>{stop();cleanup()};trace('fixture-returned',context.state,context.traceId);return destination.stream;})();
          try{return await Promise.race([ready,deadline]);}catch(error){cleanup();throw error;}finally{clearTimeout(timer);}
        };})();
        """
        config.userContentController.addUserScript(WKUserScript(source:syntheticMedia,injectionTime:.atDocumentStart,forMainFrameOnly:true))
        #endif
        web=WKWebView(frame:.zero,configuration:config);web.navigationDelegate=self;web.uiDelegate=self
        web.translatesAutoresizingMaskIntoConstraints=false
    }

    func menuItem(_ title:String,_ action:Selector,_ key:String="") -> NSMenuItem {
        let item=NSMenuItem(title:title,action:action,keyEquivalent:key);item.target=self;return item
    }
    func buildMenu() {
        let menu=NSMenu()
        let appItem=NSMenuItem();menu.addItem(appItem)
        let appMenu=NSMenu(title:"Personal Companion");appItem.submenu=appMenu
        appMenu.addItem(menuItem("Про програму",#selector(about)))
        appMenu.addItem(menuItem("Перевірити оновлення…",#selector(checkUpdates)))
        appMenu.addItem(.separator())
        let hide=NSMenuItem(title:"Сховати Personal Companion",action:#selector(NSApplication.hide(_:)),keyEquivalent:"h");appMenu.addItem(hide)
        appMenu.addItem(NSMenuItem(title:"Завершити",action:#selector(NSApplication.terminate(_:)),keyEquivalent:"q"))
        let editItem=NSMenuItem();menu.addItem(editItem);let edit=NSMenu(title:"Редагування");editItem.submenu=edit
        for (title,selector,key) in [("Скасувати","undo:","z"),("Вирізати","cut:","x"),("Копіювати","copy:","c"),("Вставити","paste:","v"),("Обрати все","selectAll:","a")] {
            edit.addItem(NSMenuItem(title:title,action:NSSelectorFromString(selector),keyEquivalent:key))
        }
        let dataItem=NSMenuItem();menu.addItem(dataItem);let data=NSMenu(title:"Дані");dataItem.submenu=data
        data.addItem(menuItem("Заблокувати простір",#selector(lock),"l"))
        data.addItem(menuItem("Створити резервну копію",#selector(backup)))
        data.addItem(menuItem("Відновити з копії…",#selector(restore)))
        data.addItem(menuItem("Відкрити папку копій",#selector(showBackups)))
        data.addItem(menuItem("Попередня програма",#selector(previousCode)))
        let helpItem=NSMenuItem();menu.addItem(helpItem);let help=NSMenu(title:"Допомога");helpItem.submenu=help
        help.addItem(menuItem("Коротка інструкція",#selector(guide)))
        #if LOCAL_TEST
        help.addItem(menuItem("Увімкнути synthetic PCM fixture",#selector(syntheticCapture)))
        help.addItem(menuItem("Synthetic STARTING: never resolve",#selector(syntheticNever)))
        help.addItem(menuItem("Synthetic save: hold",#selector(syntheticHoldSave)))
        help.addItem(menuItem("Synthetic save: release",#selector(syntheticReleaseSave)))
        help.addItem(menuItem("Synthetic producer: hide",#selector(syntheticHide)))
        #endif
        NSApp.mainMenu=menu
    }

    func replaceContent(_ view:NSView) {
        content.subviews.forEach{$0.removeFromSuperview()}
        view.translatesAutoresizingMaskIntoConstraints=false;content.addSubview(view)
        NSLayoutConstraint.activate([view.leadingAnchor.constraint(equalTo:content.leadingAnchor),
            view.trailingAnchor.constraint(equalTo:content.trailingAnchor),view.topAnchor.constraint(equalTo:content.topAnchor),
            view.bottomAnchor.constraint(equalTo:content.bottomAnchor)])
    }
    func welcome() {
        let host=NSView();let stack=NSStackView();stack.orientation = .vertical;stack.alignment = .leading;stack.spacing=20
        stack.translatesAutoresizingMaskIntoConstraints=false;host.addSubview(stack)
        let title=NSTextField(labelWithString:"Місце для ваших думок.")
        title.font=NSFont(name:"Georgia",size:32) ?? .systemFont(ofSize:32);stack.addArrangedSubview(title)
        let text=NSTextField(wrappingLabelWithString:"Новий порожній простір на цьому Mac. Щоденник, творчість і голос працюють локально. AI початково вимкнений. Копії містять базу, історію та аудіо й захищені FileVault на цьому диску. Програма не імпортує попередні дані.")
        text.font = .systemFont(ofSize:16);stack.addArrangedSubview(text)
        let button=NSButton(title:"Створити локальний простір…",target:self,action:#selector(initialize));button.bezelStyle = .rounded;stack.addArrangedSubview(button)
        NSLayoutConstraint.activate([stack.widthAnchor.constraint(equalToConstant:540),
            stack.centerXAnchor.constraint(equalTo:host.centerXAnchor),stack.centerYAnchor.constraint(equalTo:host.centerYAnchor)])
        replaceContent(host);openButton.isEnabled=false
    }
    @objc func initialize() {
        let alert=NSAlert();alert.messageText="Створити порожнє локальне сховище?"
        alert.informativeText="Підтверджую, що я власниця даних і погоджуюся на їх локальне зберігання та резервні копії. Ця папка не синхронізується мною із хмарою. Потрібен FileVault; копії не мають окремого шифрування архіву. AI, Health, клінічні протоколи й телефон вимкнені."
        #if LOCAL_TEST
        alert.informativeText="ORIGINAL SYNTHETIC TEST: лише новий disposable профіль. "+alert.informativeText
        #endif
        alert.addButton(withTitle:"Погоджуюсь і створюю");alert.addButton(withTitle:"Скасувати")
        guard alert.runModal() == .alertFirstButtonReturn else { return }
        do { _=try backend!.call("initialize",["consent":true,"no_cloud":true]);try start() }
        catch { problem("Сховище не створено або перевірку захисту не пройдено. Перевірте FileVault й права папки; не змінюйте файли сховища для обходу перевірки.") }
    }
    func start() throws {
        let status=try backend!.call("start");port=status["port"] as? Int ?? 0
        try applyStart(status)
    }
    func applyStart(_ status:[String:Any]) throws {
        port=status["port"] as? Int ?? 0
        guard port>0 else { throw NativeFailure.unavailable }
        web.isHidden=false;replaceContent(web);web.load(URLRequest(url:URL(string:"http://127.0.0.1:\(port)/")!))
        state.stringValue="Локальний простір заблоковано · AI недоступний";openButton.isEnabled=true
        testEvent("core-started")
    }
    @objc func unlock() {
        guard !maintenanceBusy else {return}
        #if LOCAL_TEST
        redeem()
        #else
        let context=LAContext()
        context.evaluatePolicy(.deviceOwnerAuthentication,localizedReason:"Відкрити локальний Особистий простір") { ok,_ in
            DispatchQueue.main.async { if ok { self.redeem() } else { self.problem("Доступ не підтверджено. Простір залишається заблокованим.") } }
        }
        #endif
    }
    func redeem() {
        do {
            let result=try backend!.call("unlock")
            guard let code=result["code"] as? String,let sha=result["source_sha"] as? String,
                  web.url?.absoluteString.hasPrefix("http://127.0.0.1:\(port)/")==true else { throw NativeFailure.unavailable }
            let codeJSON=String(data:try JSONSerialization.data(withJSONObject:code,options:.fragmentsAllowed),encoding:.utf8)!
            // The one-time code is scoped to this origin, consumed immediately,
            // held in a lexical closure, never persisted or added to a URL.
            let js="(async()=>{const r=await fetch('/api/v1/auth/unlock',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-PC-Build':'\(sha)'},body:JSON.stringify({code:\(codeJSON)})});return r.ok})()"
            web.callAsyncJavaScript("return await "+js,arguments:[:],in:nil,in:.page) { result in
                switch result {case .success(let value):if value as? Bool == true { self.web.reload();self.state.stringValue="Дані на цьому Mac · AI вимкнений";self.testEvent("native-unlocked") }
                else {self.problem("Не вдалося відкрити простір. Повторіть підтвердження доступу.")}
                case .failure: self.problem("Не вдалося відкрити простір. Повторіть підтвердження доступу.")}
            }
        } catch { problem("Локальний простір недоступний. Закрийте й відкрийте програму; дані залишаються на Mac.") }
    }
    @objc func lock() {
        guard !maintenanceBusy else {return}
        _=try? backend?.call("lock");web?.reload()
        state.stringValue="Локальний простір заблоковано · AI вимкнений"
    }
    func problem(_ text:String) {
        state.stringValue=text
        let alert=NSAlert();alert.messageText="Локальна програма потребує уваги";alert.informativeText=text
        alert.addButton(withTitle:"Зрозуміло");alert.runModal()
    }
    @objc func about() {
        let version=Bundle.main.object(forInfoDictionaryKey:"CFBundleVersion") as? String ?? "?"
        let alert=NSAlert();alert.messageText="Personal Companion 0.8.6 · \(version)"
        alert.informativeText="Локальний engineering-кандидат: Python і UI у програмі, Whisper CPU/small multilingual. AI без погодженого маршруту недоступний. Production-оновлення вимкнені; notarization не виконано. Клінічні протоколи, Health і телефон OFF."
        alert.runModal()
    }
    @objc func backup() {
        guard !maintenanceBusy else {return}
        runMaintenance("Перевіряємо резервну копію…",work: {backend in
            _=try backend.call("backup");return try backend.call("start")
        }) {result in
            do {try self.applyStart(result.get());self.state.stringValue="Резервну копію перевірено. Простір заблоковано."}
            catch {self.resumeAfterUpdate();self.problem("Копію не підтверджено. Дані збережено; перевірте місце й захист диска.")}
        }
    }
    @objc func restore() {
        guard !maintenanceBusy else {return}
        let panel=NSOpenPanel();panel.canChooseDirectories=true;panel.canChooseFiles=false
        panel.directoryURL=base.appendingPathComponent("backups");panel.prompt="Обрати копію"
        guard panel.runModal() == .OK,let url=panel.url,
              url.deletingLastPathComponent().standardizedFileURL == base.appendingPathComponent("backups").standardizedFileURL else { return }
        let alert=NSAlert();alert.messageText="Відновити копію в новий простір?"
        alert.informativeText="Погоджуюся на нове локальне сховище й захищені копії без хмарної синхронізації. Попереднє сховище зберігається; AI та дозволи потребують нового погодження."
        alert.addButton(withTitle:"Погоджуюсь і відновлюю");alert.addButton(withTitle:"Скасувати")
        guard alert.runModal() == .alertFirstButtonReturn else {return}
        runMaintenance("Перевіряємо й відновлюємо копію в новий простір…",work: {backend in
            _=try backend.call("restore",["name":url.lastPathComponent,"confirmation":true]);return try backend.call("start")
        }) {result in
            do {try self.applyStart(result.get());self.state.stringValue="Копію відновлено. Попередній простір збережено."}
            catch {self.resumeAfterUpdate();self.problem("Відновлення не підтверджено. Попереднє сховище й копія збережені.")}
        }
    }
    @objc func showBackups() {if FileManager.default.fileExists(atPath:base.appendingPathComponent("backups").path) {NSWorkspace.shared.open(base.appendingPathComponent("backups"))}}
    @objc func previousCode() {
        let url=base.deletingLastPathComponent().appendingPathComponent(base.lastPathComponent+"-code-recovery/previous-code.app")
        guard FileManager.default.fileExists(atPath:url.path) else {problem("Попередня програма ще не збережена. Дані залишаються у локальному сховищі.");return}
        NSWorkspace.shared.activateFileViewerSelecting([url])
    }
    @objc func guide() {NSWorkspace.shared.open(bundle.appendingPathComponent("Contents/Resources/User Guide.md"))}
    @objc func syntheticCapture() {
        #if LOCAL_TEST
        web.evaluateJavaScript("window.__pcSyntheticCapture=true;window.__pcSyntheticMode='normal'")
        state.stringValue="ORIGINAL SYNTHETIC PCM · фізичний мікрофон заборонений"
        testEvent("synthetic-pcm-enabled")
        #endif
    }
    #if LOCAL_TEST
    @objc func syntheticNever() {
        web.evaluateJavaScript("window.__pcSyntheticCapture=true;window.__pcSyntheticMode='never'")
        testEvent("synthetic-start-never-enabled")
    }
    @objc func syntheticHoldSave() {
        web.evaluateJavaScript("window.__pcSyntheticMode='save-held'")
        testEvent("synthetic-save-held-enabled")
    }
    @objc func syntheticReleaseSave() {
        web.evaluateJavaScript("window.__pcSyntheticMode='normal';window.__pcReleaseSyntheticSave()")
        testEvent("synthetic-save-released")
    }
    @objc func syntheticHide() {
        web.evaluateJavaScript("document.querySelector('.composer-voice')?.style.setProperty('display','none')")
        testEvent("synthetic-producer-hidden")
    }
    #endif
    @objc func checkUpdates() {
        guard !maintenanceBusy else {return}
        #if LOCAL_TEST
        // Conservatively refuse to discard any visible unsaved text or an active
        // recorder. Only a Boolean crosses the native bridge, no draft content.
        let check=unsavedCheck
        web.callAsyncJavaScript(check,arguments:[:],in:nil,in:.page) {result in
            if case .success(let value)=result,value as? Bool == false {
                // No new drafts/capture may begin between check and quiescence.
                _=try? self.backend?.call("lock")
                self.updateFailed=false;self.settledUpdateText=nil;self.pendingTarget=nil
                self.web.isHidden=true;self.openButton.isEnabled=false
                self.window.makeFirstResponder(nil);self.updater?.checkForUpdates()
            }
            else {self.testEvent("update-refused-unsaved");self.problem("Збережіть чернетку або завершіть запис і закрийте редактор перед оновленням.")}
        }
        #else
        problem("Канал оновлень ще не активований. Потрібен окремо перевірений підписаний реліз.")
        #endif
    }
    func allowedChannels(for updater:SPUUpdater) -> Set<String> { ["M8F_LOCAL_TEST"] }
    func runMaintenance(_ label:String,work:@escaping(Backend)throws->[String:Any],completion:@escaping(Result<[String:Any],Error>)->Void) {
        guard !maintenanceBusy,let backend=backend else {completion(.failure(NativeFailure.unavailable));return}
        _=try? backend.call("lock")
        maintenanceBusy=true;maintenancePulses=0
        web.isHidden=true;openButton.isEnabled=false;window.makeFirstResponder(nil)
        state.stringValue=label;progress.startAnimation(nil)
        let timer=Timer(timeInterval:0.2,repeats:true) {[weak self] _ in self?.maintenancePulses+=1}
        maintenanceTimer=timer;RunLoop.main.add(timer,forMode:.common)
        testEvent("maintenance-started")
        backend.perform(work) {result in
            self.maintenanceTimer?.invalidate();self.maintenanceTimer=nil
            self.maintenanceBusy=false;self.progress.stopAnimation(nil)
            self.testEvent("maintenance-finished",["ui_pulses":self.maintenancePulses])
            completion(result)
        }
    }
    func prepareChosenUpdate(_ completion:@escaping(Bool)->Void) {
        guard let target=pendingTarget else {completion(false);return}
        runMaintenance("Готуємо оновлення: перевіряємо копію й відновлення…",work: {backend in
            try backend.call("prepare-update",["target":target])
        }) {result in
            do {
                _=try result.get();self.prepared=true
                self.state.stringValue="Копію перевірено. Встановлюємо підписану нову версію…"
                self.testEvent("update-prepared");completion(true)
            } catch {self.presentUpdateFailure();self.resumeAfterUpdate();completion(false)}
        }
    }
    func presentUpdateFailure() {
        updateFailed=true
        settledUpdateText="Оновлення не виконано. Попередня програма й дані збережені. Спробуйте пізніше або відкрийте папку копій."
        state.stringValue=settledUpdateText!
        testEvent("update-error")
        let alert=NSAlert();alert.messageText="Оновлення не виконано"
        alert.informativeText="Перевірка або встановлення не завершились. Попередня програма та дані збережені. Можна повторити перевірку пізніше; резервні копії й попередній код доступні в меню «Дані»."
        alert.addButton(withTitle:"Зрозуміло");alert.addButton(withTitle:"Відкрити папку копій")
        if alert.runModal() == .alertSecondButtonReturn {showBackups()}
    }
    func resumeAfterUpdate() {
        guard !resumeQueued,!maintenanceBusy,let backend=backend else {return}
        resumeQueued=true
        backend.perform({try $0.call("start")}) {result in
            self.resumeQueued=false
            do {try self.applyStart(result.get())}
            catch {self.state.stringValue="Локальний простір потребує відновлення. Дані й копії збережені."}
            if self.updateFailed {self.state.stringValue=self.settledUpdateText ?? "Оновлення не виконано. Попередня програма й дані збережені."}
            else if let text=self.settledUpdateText {self.state.stringValue=text}
        }
    }
    func updater(_ updater:SPUUpdater, shouldProceedWithUpdate item:SUAppcastItem, updateCheck:SPUUpdateCheck) throws {
        #if LOCAL_TEST
        testEvent("update-selected",["property_keys":item.propertiesDictionary.keys.map {String(describing:$0)}])
        // Signed appcast metadata, independently tied to embedded test public key.
        guard item.channel=="M8F_LOCAL_TEST",let build=Int(item.versionString),
              let product=item.propertiesDictionary["pc:product"] as? String,
              let arch=item.propertiesDictionary["pc:arch"] as? String,
              let sha=item.propertiesDictionary["pc:source"] as? String,
              let hash=item.propertiesDictionary["pc:manifest"] as? String,
              let schemaString=item.propertiesDictionary["pc:schema"] as? String,let schema=Int(schemaString),
              let url=item.fileURL,url.scheme=="http",url.host=="127.0.0.1" else {throw NativeFailure.unavailable}
        let target:[String:Any]=["product":product,"channel":item.channel!,"arch":arch,
            "build":build,"source_sha":sha,"manifest_hash":hash,"schema":schema]
        _=try backend!.call("validate-update",["target":target]);pendingTarget=target
        #else
        throw NativeFailure.unavailable
        #endif
    }
    func updater(_ updater:SPUUpdater,willInstallUpdate item:SUAppcastItem) {installing=true;testEvent("update-installing")}
    func updater(_ updater:SPUUpdater,didAbortWithError error:Error) {prepared=false;installing=false;updateFailed=true;testEvent("update-aborted");resumeAfterUpdate()}
    func updater(_ updater:SPUUpdater,didFinishUpdateCycleFor updateCheck:SPUUpdateCheck,error:Error?) {
        if !installing {prepared=false;resumeAfterUpdate()}
    }
    let unsavedCheck="return Array.from(document.querySelectorAll('textarea,input[type=text]')).some(e=>e.value.trim().length>0)||!!document.querySelector('[data-native-unsaved=true]')||!!document.querySelector('.recording-strip')?.getClientRects().length"
    func applicationShouldTerminate(_ sender:NSApplication) -> NSApplication.TerminateReply {
        if maintenanceBusy {state.stringValue="Дочекайтесь завершення перевірки копії перед закриттям.";return .terminateCancel}
        if closingPending {return .terminateLater}
        closingPending=true
        let finish={
            let closing=self.backend;self.backend=nil
            DispatchQueue.global(qos:.userInitiated).async {
                closing?.quit()
                DispatchQueue.main.async {NSApp.reply(toApplicationShouldTerminate:true)}
            }
        }
        if web.url == nil {finish();return .terminateLater}
        web.callAsyncJavaScript(unsavedCheck,arguments:[:],in:nil,in:.page) {result in
            if case .success(let value)=result,value as? Bool == false {finish()}
            else {
                self.closingPending=false;NSApp.reply(toApplicationShouldTerminate:false)
                self.testEvent("quit-refused-unsaved")
                self.problem("Збережіть чернетку або скасуйте запис перед закриттям програми.")
            }
        }
        return .terminateLater
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender:NSApplication)->Bool {false}
    func applicationShouldHandleReopen(_ sender:NSApplication,hasVisibleWindows flag:Bool)->Bool {window.makeKeyAndOrderFront(nil);return true}
    func webView(_ webView:WKWebView,decidePolicyFor action:WKNavigationAction,decisionHandler:@escaping(WKNavigationActionPolicy)->Void) {
        guard let url=action.request.url,url.scheme=="http",url.host=="127.0.0.1",url.port==port else {decisionHandler(.cancel);return}
        decisionHandler(.allow)
    }
    func webView(_ webView:WKWebView,requestMediaCapturePermissionFor origin:WKSecurityOrigin,initiatedByFrame frame:WKFrameInfo,type:WKMediaCaptureType,decisionHandler:@escaping(WKPermissionDecision)->Void) {
        #if LOCAL_TEST
        testEvent("physical-microphone-denied");decisionHandler(.deny);return
        #else
        guard origin.protocol=="http",origin.host=="127.0.0.1",origin.port==port,type == .microphone else {decisionHandler(.deny);return}
        // WebKit's capture prompt occurs only following the existing explicit
        // microphone action. TCC is never requested at app launch.
        decisionHandler(.prompt)
        #endif
    }
    func userContentController(_ userContentController:WKUserContentController,didReceive message:WKScriptMessage) {
        guard message.frameInfo.isMainFrame,message.frameInfo.securityOrigin.protocol=="http",
              message.frameInfo.securityOrigin.host=="127.0.0.1",message.frameInfo.securityOrigin.port==port else {return}
        #if LOCAL_TEST
        if let body=message.body as? [String:Any],body["kind"] as? String=="voice-trace",
           Set(body.keys)==["kind","stage","state","context_id","t_ms","gesture","hidden"],
           let stage=body["stage"] as? String,
           ["fixture-requested","fixture-fetched","fixture-decoded","fixture-wired","fixture-returned",
            "context-created","context-state","context-pending-check","resume-requested","resume-resolved","resume-rejected","ui-state"].contains(stage),
           let state=body["state"] as? String,
           ["","running","suspended","interrupted","closed","IDLE","STARTING","RECORDING","SAVING","LOCAL_AUDIO_SAVED",
            "TRANSCRIBING","WAITING_FOR_LOCAL_ASR","DRAFT_READY","REVIEW_REQUIRED","FAILED","CANCELLED"].contains(state),
           let id=body["context_id"] as? Int,id>=0,id<=1000,
           let ms=body["t_ms"] as? Int,ms>=0,ms<=86400000,
           let gesture=body["gesture"] as? String,["ACTIVE","INACTIVE","UNSUPPORTED"].contains(gesture),
           let hidden=body["hidden"] as? Bool {
            testEvent("voice-trace",["stage":stage,"state":state,"context_id":id,"t_ms":ms,"gesture":gesture,"hidden":hidden]);return
        }
        #endif
        guard message.body as? String == "unlock" else {return}
        unlock()
    }
}

let application=NSApplication.shared
let delegate=Companion()
application.delegate=delegate
application.setActivationPolicy(.regular)
application.run()
