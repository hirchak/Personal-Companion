// Geometric notebook mark derived from the existing paper/ink/sage identity.
import AppKit
let size=NSSize(width:1024,height:1024)
let image=NSImage(size:size)
image.lockFocus()
NSColor(calibratedRed:0.27,green:0.38,blue:0.32,alpha:1).setFill()
NSBezierPath(roundedRect:NSRect(x:60,y:60,width:904,height:904),xRadius:200,yRadius:200).fill()
NSColor(calibratedRed:0.97,green:0.96,blue:0.92,alpha:1).setFill()
NSBezierPath(roundedRect:NSRect(x:284,y:204,width:476,height:616),xRadius:32,yRadius:32).fill()
NSColor(calibratedRed:0.16,green:0.24,blue:0.20,alpha:1).setStroke()
let spine=NSBezierPath();spine.lineWidth=14;spine.move(to:NSPoint(x:352,y:216));spine.line(to:NSPoint(x:352,y:808));spine.stroke()
for y in [620,524,428] {
    let line=NSBezierPath();line.lineWidth=14;line.lineCapStyle = .round
    line.move(to:NSPoint(x:416,y:CGFloat(y)));line.line(to:NSPoint(x:656,y:CGFloat(y)));line.stroke()
}
image.unlockFocus()
let rep=NSBitmapImageRep(data:image.tiffRepresentation!)!
try rep.representation(using:.png,properties:[:])!.write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
