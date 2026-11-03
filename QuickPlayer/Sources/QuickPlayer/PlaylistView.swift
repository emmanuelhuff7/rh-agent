import SwiftUI

struct PlaylistView: View {
    @ObservedObject var player: PlayerViewModel

    var body: some View {
        List {
            ForEach(Array(player.playlist.enumerated()), id: \.element.id) { index, track in
                HStack(spacing: 10) {
                    artworkThumbnail(for: track)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(track.title)
                            .font(.caption)
                            .fontWeight(index == player.currentIndex ? .bold : .regular)
                            .lineLimit(1)
                        Text(track.artist)
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                    }
                    Spacer()
                    if index == player.currentIndex && player.isPlaying {
                        Image(systemName: "speaker.wave.2.fill")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
                .contentShape(Rectangle())
                .onTapGesture {
                    player.play(track: index)
                }
                .listRowBackground(
                    index == player.currentIndex ? Color.accentColor.opacity(0.15) : Color.clear
                )
                .contextMenu {
                    Button("Remove", role: .destructive) {
                        player.remove(at: index)
                    }
                }
            }
        }
        .listStyle(.sidebar)
        .overlay {
            if player.playlist.isEmpty {
                Text("No songs yet")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }

    @ViewBuilder
    private func artworkThumbnail(for track: AudioTrack) -> some View {
        if let artwork = track.artwork {
            Image(nsImage: artwork)
                .resizable()
                .aspectRatio(contentMode: .fill)
                .frame(width: 36, height: 36)
                .clipShape(RoundedRectangle(cornerRadius: 4))
        } else {
            RoundedRectangle(cornerRadius: 4)
                .fill(Color.gray.opacity(0.25))
                .frame(width: 36, height: 36)
                .overlay(
                    Image(systemName: "music.note")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                )
        }
    }
}
