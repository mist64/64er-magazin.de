// Tiny CLI wrapper around Apple Vision text recognition.
// Usage:  swift vision_ocr.swift <image_path>
// Prints recognized strings one per line.
import Foundation
import Vision
import AppKit

guard CommandLine.arguments.count >= 2 else {
    FileHandle.standardError.write("usage: vision_ocr <image>\n".data(using: .utf8)!)
    exit(2)
}
let path = CommandLine.arguments[1]
guard let img = NSImage(contentsOfFile: path),
      let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil)
else {
    FileHandle.standardError.write("cannot load \(path)\n".data(using: .utf8)!)
    exit(1)
}

let req = VNRecognizeTextRequest { req, err in
    if let err = err {
        FileHandle.standardError.write("\(err)\n".data(using: .utf8)!)
        exit(1)
    }
    let obs = req.results as? [VNRecognizedTextObservation] ?? []
    for o in obs {
        guard let s = o.topCandidates(1).first?.string else { continue }
        // bbox is normalised, origin at bottom-left
        let b = o.boundingBox
        // print: x y w h \t text
        print(String(format: "%.4f %.4f %.4f %.4f\t%@",
                     b.origin.x, b.origin.y, b.size.width, b.size.height, s))
    }
}
req.recognitionLevel = .accurate
req.usesLanguageCorrection = false

let handler = VNImageRequestHandler(cgImage: cg, options: [:])
do {
    try handler.perform([req])
} catch {
    FileHandle.standardError.write("\(error)\n".data(using: .utf8)!)
    exit(1)
}
