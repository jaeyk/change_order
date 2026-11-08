import PDFKit
import Vision
import AppKit
// usage: ocr <pdf> <maxPages>
let url = URL(fileURLWithPath: CommandLine.arguments[1])
let maxPages = Int(CommandLine.arguments.count > 2 ? CommandLine.arguments[2] : "4") ?? 4
func ocrImage(_ img: CGImage) -> [String] {
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = true
    try? VNImageRequestHandler(cgImage: img, options: [:]).perform([req])
    return (req.results ?? []).compactMap { $0.topCandidates(1).first?.string }
}
// Image files (PNG/TIFF/JPEG): OCR every frame directly
if ["png", "tif", "tiff", "jpg", "jpeg"].contains(url.pathExtension.lowercased()) {
    guard let src = CGImageSourceCreateWithURL(url as CFURL, nil) else { print("ERR open"); exit(1) }
    let n = CGImageSourceGetCount(src)
    print("PAGES \(n)")
    for i in 0..<min(n, maxPages) {
        guard let img = CGImageSourceCreateImageAtIndex(src, i, nil) else { continue }
        print("=== PAGE \(i + 1)")
        print(ocrImage(img).joined(separator: "\n"))
    }
    exit(0)
}
guard let doc = PDFDocument(url: url) else { print("ERR open"); exit(1) }
print("PAGES \(doc.pageCount)")
for i in 0..<min(maxPages, doc.pageCount) {
    guard let page = doc.page(at: i) else { continue }
    let box = page.bounds(for: .mediaBox)
    let scale: CGFloat = 2.0
    let w = Int(box.width * scale), h = Int(box.height * scale)
    guard let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: 0,
                              space: CGColorSpaceCreateDeviceRGB(),
                              bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { continue }
    ctx.setFillColor(NSColor.white.cgColor); ctx.fill(CGRect(x: 0, y: 0, width: w, height: h))
    ctx.scaleBy(x: scale, y: scale)
    page.draw(with: .mediaBox, to: ctx)
    guard let img = ctx.makeImage() else { continue }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = true
    try? VNImageRequestHandler(cgImage: img, options: [:]).perform([req])
    let lines = (req.results ?? []).compactMap { $0.topCandidates(1).first?.string }
    print("=== PAGE \(i + 1)")
    print(lines.joined(separator: "\n"))
}
