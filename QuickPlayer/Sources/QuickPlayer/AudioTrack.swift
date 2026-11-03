import AppKit
import AVFoundation

struct AudioTrack: Identifiable, Equatable {
    let id = UUID()
    let url: URL
    var title: String
    var artist: String
    var artwork: NSImage?
    var duration: Double

    static func == (lhs: AudioTrack, rhs: AudioTrack) -> Bool {
        lhs.id == rhs.id
    }

    static func load(from url: URL) async -> AudioTrack {
        let asset = AVURLAsset(url: url)
        var title = url.deletingPathExtension().lastPathComponent
        var artist = "Unknown Artist"
        var artwork: NSImage?
        var duration: Double = 0

        if let items = try? await asset.load(.commonMetadata) {
            for item in items {
                guard let key = item.commonKey else { continue }
                switch key {
                case .commonKeyTitle:
                    if let value = try? await item.load(.stringValue), let value {
                        title = value
                    }
                case .commonKeyArtist:
                    if let value = try? await item.load(.stringValue), let value {
                        artist = value
                    }
                case .commonKeyArtwork:
                    if let data = try? await item.load(.dataValue), let data, let image = NSImage(data: data) {
                        artwork = image
                    }
                default:
                    break
                }
            }
        }

        if let loadedDuration = try? await asset.load(.duration) {
            duration = loadedDuration.seconds.isFinite ? loadedDuration.seconds : 0
        }

        return AudioTrack(url: url, title: title, artist: artist, artwork: artwork, duration: duration)
    }
}
