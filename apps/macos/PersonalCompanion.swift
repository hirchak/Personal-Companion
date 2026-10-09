import AppKit
import WebKit
import LocalAuthentication
import AVFoundation
import Sparkle

enum NativeFailure: Error { case unavailable }

// A private inherited pipe, no socket/credential arguments or console logging.
final class Backend {
    let process = Process(), input = Pipe(), output = Pipe()
    var serial = 0
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
        guard process.isRunning else { throw NativeFailure.unavailable }
        serial += 1
        var value = fields; value["op"] = op; value["id"] = serial
        var bytes = try JSONSerialization.data(withJSONObject:value); bytes.append(10)
        try input.fileHandleForWriting.write(contentsOf:bytes)
        var reply = Data()
        // Backend commands are serialized on the UI thread. They are local and
        // bounded; update/backup shows native progress before blocking writers.
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
    func quit() {
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
    var base: URL!
    var backend: Backend?
    var window: NSWindow!
    var web: WKWebView!
    var content: NSView!
    let state = NSTextField(labelWithString:"Дані на цьому Mac · AI вимкнений")
    var openButton: NSButton!
    var updater: SPUStandardUpdaterController?
    var port: Int = 0
    var prepared = false
    var installing = false
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
        updater = SPUStandardUpdaterController(startingUpdater:true,updaterDelegate:self,userDriverDelegate:nil)
        #endif
        window.makeKeyAndOrderFront(nil); NSApp.activate(ignoringOtherApps:true)
        testEvent("window-ready")
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
        guard port>0 else { throw NativeFailure.unavailable }
        replaceContent(web);web.load(URLRequest(url:URL(string:"http://127.0.0.1:\(port)/")!))
        state.stringValue="Локальний простір заблоковано · AI недоступний";openButton.isEnabled=true
        testEvent("core-started")
    }
    @objc func unlock() {
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
        state.stringValue="Перевіряємо резервну копію…";lock()
        do { _=try backend!.call("backup");try start();state.stringValue="Резервну копію перевірено. Простір заблоковано." }
        catch { try? start();problem("Копію не підтверджено. Попередні дані збережено; перевірте місце й захист диска.") }
    }
    @objc func restore() {
        let panel=NSOpenPanel();panel.canChooseDirectories=true;panel.canChooseFiles=false
        panel.directoryURL=base.appendingPathComponent("backups");panel.prompt="Обрати копію"
        guard panel.runModal() == .OK,let url=panel.url,
              url.deletingLastPathComponent().standardizedFileURL == base.appendingPathComponent("backups").standardizedFileURL else { return }
        let alert=NSAlert();alert.messageText="Відновити копію в новий простір?"
        alert.informativeText="Погоджуюся на нове локальне сховище й захищені копії без хмарної синхронізації. Попереднє сховище зберігається; AI та дозволи потребують нового погодження."
        alert.addButton(withTitle:"Погоджуюсь і відновлюю");alert.addButton(withTitle:"Скасувати")
        guard alert.runModal() == .alertFirstButtonReturn else {return}
        do {lock();_=try backend!.call("restore",["name":url.lastPathComponent,"confirmation":true]);try start()}
        catch {try? start();problem("Відновлення не підтверджено. Попереднє сховище й копія збережені.")}
    }
    @objc func showBackups() {if FileManager.default.fileExists(atPath:base.appendingPathComponent("backups").path) {NSWorkspace.shared.open(base.appendingPathComponent("backups"))}}
    @objc func previousCode() {
        let url=base.appendingPathComponent("previous-code.app")
        guard FileManager.default.fileExists(atPath:url.path) else {problem("Попередня програма ще не збережена. Дані залишаються у локальному сховищі.");return}
        NSWorkspace.shared.activateFileViewerSelecting([url])
    }
    @objc func guide() {NSWorkspace.shared.open(bundle.appendingPathComponent("Contents/Resources/User Guide.md"))}
    @objc func checkUpdates() {
        #if LOCAL_TEST
        updater?.checkForUpdates(nil)
        #else
        problem("Канал оновлень ще не активований. Потрібен окремо перевірений підписаний реліз.")
        #endif
    }
    func allowedChannels(for updater:SPUUpdater) -> Set<String> { ["M8F_LOCAL_TEST"] }
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
        lock();state.stringValue="Готуємо оновлення: перевіряємо копію й відновлення…"
        do {_=try backend!.call("prepare-update",["target":["product":product,"channel":item.channel!,"arch":arch,
            "build":build,"source_sha":sha,"manifest_hash":hash,"schema":schema]])
            prepared=true;state.stringValue="Доступна нова версія. Копію перевірено; дані призупинено до завершення оновлення.";testEvent("update-prepared")
        } catch {try? start();throw NSError(domain:"PersonalCompanion",code:1,userInfo:[NSLocalizedDescriptionKey:"Оновлення не пройшло перевірку. Попередня програма й дані збережені."])}
        #else
        throw NativeFailure.unavailable
        #endif
    }
    func updater(_ updater:SPUUpdater,willInstallUpdate item:SUAppcastItem) {installing=true;testEvent("update-installing")}
    func updater(_ updater:SPUUpdater,didAbortWithError error:Error) {prepared=false;installing=false;try? start();state.stringValue="Оновлення не виконано. Попередня версія працює.";testEvent("update-aborted")}
    func updater(_ updater:SPUUpdater,didFinishUpdateCycleFor updateCheck:SPUUpdateCheck,error:Error?) {
        if !installing {prepared=false;try? start()}
    }
    func applicationShouldTerminate(_ sender:NSApplication) -> NSApplication.TerminateReply {
        backend?.quit();backend=nil;return .terminateNow
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender:NSApplication)->Bool {false}
    func applicationShouldHandleReopen(_ sender:NSApplication,hasVisibleWindows flag:Bool)->Bool {window.makeKeyAndOrderFront(nil);return true}
    func webView(_ webView:WKWebView,decidePolicyFor action:WKNavigationAction,decisionHandler:@escaping(WKNavigationActionPolicy)->Void) {
        guard let url=action.request.url,url.scheme=="http",url.host=="127.0.0.1",url.port==port else {decisionHandler(.cancel);return}
        decisionHandler(.allow)
    }
    func webView(_ webView:WKWebView,requestMediaCapturePermissionFor origin:WKSecurityOrigin,initiatedByFrame frame:WKFrameInfo,type:WKMediaCaptureType,decisionHandler:@escaping(WKPermissionDecision)->Void) {
        guard origin.protocol=="http",origin.host=="127.0.0.1",origin.port==port,type == .microphone else {decisionHandler(.deny);return}
        // WebKit's capture prompt occurs only following the existing explicit
        // microphone action. TCC is never requested at app launch.
        decisionHandler(.prompt)
    }
    func userContentController(_ userContentController:WKUserContentController,didReceive message:WKScriptMessage) {
        guard message.frameInfo.isMainFrame,message.frameInfo.securityOrigin.host=="127.0.0.1",
              message.frameInfo.securityOrigin.port==port,message.body as? String == "unlock" else {return}
        unlock()
    }
}

let application=NSApplication.shared
let delegate=Companion()
application.delegate=delegate
application.setActivationPolicy(.regular)
application.run()
