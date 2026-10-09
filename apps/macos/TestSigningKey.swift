// Test keys only: fresh raw seed outside Keychain, never shipped in a bundle.
import Foundation
import CryptoKit
let key=Curve25519.Signing.PrivateKey()
let folder=URL(fileURLWithPath:CommandLine.arguments[1])
try key.rawRepresentation.base64EncodedString().write(to:folder.appendingPathComponent("test-private.key"),atomically:true,encoding:.utf8)
try FileManager.default.setAttributes([.posixPermissions:0o600],ofItemAtPath:folder.appendingPathComponent("test-private.key").path)
try key.publicKey.rawRepresentation.base64EncodedString().write(to:folder.appendingPathComponent("test-public.txt"),atomically:true,encoding:.utf8)
