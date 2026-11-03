import AppKit
import SwiftUI
import UniformTypeIdentifiers

private let audioExtensions: Set<String> = ["mp3", "m4a", "wav", "aac", "flac", "aiff", "aif"]

struct ContentView: View {
    @StateObject private var player = PlayerViewModel()
    @State private var showPlaylist = true

    var body: some View {
        HStack(spacing: 0) {
            ZStack(alignment: .bottom) {
                Color.black
                artworkView
                controlBar
            }
            .frame(minWidth: 420, minHeight: 420)
            .onDrop(of: [.fileURL], isTargeted: nil, perform: handleDrop)

            if showPlaylist {
                Divider()
                PlaylistView(player: player)
                    .frame(width: 240)
            }
        }
        .frame(minWidth: 420, minHeight: 380)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button(action: openFilePicker) {
                    Image(systemName: "plus")
                }
                .help("Add songs…")
            }
            ToolbarItem(placement: .primaryAction) {
                Button {
                    showPlaylist.toggle()
                } label: {
                    Image(systemName: "sidebar.right")
                }
                .help("Toggle playlist")
            }
        }
    }

    @ViewBuilder
    private var artworkView: some View {
        if let artwork = player.currentTrack?.artwork {
            Image(nsImage: artwork)
                .resizable()
                .aspectRatio(contentMode: .fit)
                .padding(28)
        } else {
            VStack(spacing: 12) {
                Image(systemName: "music.note")
                    .font(.system(size: 56))
                    .foregroundStyle(.secondary)
                Text(player.playlist.isEmpty ? "Drop songs here, or click + to add some" : "No Artwork")
                    .font(.callout)
                    .foregroundStyle(.secondary)
            }
        }
    }

    private var controlBar: some View {
        VStack(spacing: 6) {
            HStack {
                Text(player.currentTrack?.title ?? "")
                    .font(.callout.bold())
                    .lineLimit(1)
                Spacer()
                Text(player.currentTrack?.artist ?? "")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }

            Slider(
                value: Binding(
                    get: { player.currentTime },
                    set: { player.seek(to: $0) }
                ),
                in: 0...max(player.currentTrack?.duration ?? 0, 1)
            )
            .disabled(player.currentTrack == nil)

            HStack {
                Text(timeString(player.currentTime))
                    .font(.caption2.monospacedDigit())

                Spacer()

                HStack(spacing: 20) {
                    Button(action: player.previous) {
                        Image(systemName: "backward.fill")
                    }
                    Button(action: player.togglePlayPause) {
                        Image(systemName: player.isPlaying ? "pause.fill" : "play.fill")
                            .font(.title2)
                    }
                    Button(action: player.next) {
                        Image(systemName: "forward.fill")
                    }
                }
                .buttonStyle(.plain)
                .disabled(player.currentTrack == nil)

                Spacer()

                HStack(spacing: 4) {
                    Image(systemName: "speaker.fill")
                        .font(.caption2)
                    Slider(
                        value: Binding(
                            get: { Double(player.volume) },
                            set: { player.volume = Float($0) }
                        ),
                        in: 0...1
                    )
                    .frame(width: 70)
                }
            }
        }
        .padding(12)
        .background(.ultraThinMaterial)
        .foregroundStyle(.white)
        .clipShape(RoundedRectangle(cornerRadius: 10))
        .padding(16)
    }

    private func timeString(_ seconds: Double) -> String {
        guard seconds.isFinite, seconds >= 0 else { return "0:00" }
        let total = Int(seconds)
        return String(format: "%d:%02d", total / 60, total % 60)
    }

    private func handleDrop(providers: [NSItemProvider]) -> Bool {
        let group = DispatchGroup()
        var urls: [URL] = []

        for provider in providers {
            group.enter()
            provider.loadItem(forTypeIdentifier: UTType.fileURL.identifier, options: nil) { item, _ in
                defer { group.leave() }
                if let data = item as? Data, let url = URL(dataRepresentation: data, relativeTo: nil) {
                    urls.append(url)
                } else if let url = item as? URL {
                    urls.append(url)
                }
            }
        }

        group.notify(queue: .main) {
            let audioURLs = urls.filter { audioExtensions.contains($0.pathExtension.lowercased()) }
            if !audioURLs.isEmpty {
                player.addTracks(urls: audioURLs)
            }
        }
        return true
    }

    private func openFilePicker() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = true
        panel.canChooseDirectories = false
        panel.allowedContentTypes = [.audio]
        if panel.runModal() == .OK {
            player.addTracks(urls: panel.urls)
        }
    }
}
