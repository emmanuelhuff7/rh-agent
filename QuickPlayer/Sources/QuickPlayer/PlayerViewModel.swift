import AVFoundation
import Combine
import Foundation

@MainActor
final class PlayerViewModel: ObservableObject {
    @Published private(set) var playlist: [AudioTrack] = []
    @Published private(set) var currentIndex: Int?
    @Published private(set) var isPlaying = false
    @Published var currentTime: Double = 0
    @Published var volume: Float = 1.0 {
        didSet { player?.volume = volume }
    }

    private var player: AVPlayer?
    private var timeObserverToken: Any?
    private var endObserver: NSObjectProtocol?

    var currentTrack: AudioTrack? {
        guard let currentIndex, playlist.indices.contains(currentIndex) else { return nil }
        return playlist[currentIndex]
    }

    func addTracks(urls: [URL]) {
        Task {
            for url in urls {
                let track = await AudioTrack.load(from: url)
                playlist.append(track)
                if currentIndex == nil {
                    play(track: playlist.count - 1)
                }
            }
        }
    }

    func play(track index: Int) {
        guard playlist.indices.contains(index) else { return }
        currentIndex = index
        loadCurrentTrack(autoplay: true)
    }

    func togglePlayPause() {
        guard let player else { return }
        if isPlaying {
            player.pause()
        } else {
            player.play()
        }
        isPlaying.toggle()
    }

    func next() {
        guard let currentIndex else { return }
        let nextIndex = currentIndex + 1
        if playlist.indices.contains(nextIndex) {
            play(track: nextIndex)
        } else {
            player?.pause()
            isPlaying = false
        }
    }

    func previous() {
        guard let currentIndex else { return }
        if currentTime > 3 {
            seek(to: 0)
            return
        }
        let prevIndex = currentIndex - 1
        if playlist.indices.contains(prevIndex) {
            play(track: prevIndex)
        } else {
            seek(to: 0)
        }
    }

    func seek(to time: Double) {
        guard let player else { return }
        player.seek(to: CMTime(seconds: time, preferredTimescale: 600))
        currentTime = time
    }

    func remove(at index: Int) {
        guard playlist.indices.contains(index) else { return }
        playlist.remove(at: index)

        guard let currentIndex else { return }

        if currentIndex == index {
            removeObservers()
            player = nil
            isPlaying = false
            if playlist.isEmpty {
                self.currentIndex = nil
            } else {
                play(track: min(currentIndex, playlist.count - 1))
            }
        } else if currentIndex > index {
            self.currentIndex = currentIndex - 1
        }
    }

    private func loadCurrentTrack(autoplay: Bool) {
        removeObservers()
        guard let track = currentTrack else { return }

        let item = AVPlayerItem(url: track.url)
        let newPlayer = AVPlayer(playerItem: item)
        newPlayer.volume = volume
        player = newPlayer
        currentTime = 0

        timeObserverToken = newPlayer.addPeriodicTimeObserver(
            forInterval: CMTime(seconds: 0.25, preferredTimescale: 600),
            queue: .main
        ) { [weak self] time in
            self?.currentTime = time.seconds
        }

        endObserver = NotificationCenter.default.addObserver(
            forName: .AVPlayerItemDidPlayToEndTime,
            object: item,
            queue: .main
        ) { [weak self] _ in
            self?.next()
        }

        if autoplay {
            newPlayer.play()
            isPlaying = true
        }
    }

    private func removeObservers() {
        if let timeObserverToken, let player {
            player.removeTimeObserver(timeObserverToken)
        }
        timeObserverToken = nil
        if let endObserver {
            NotificationCenter.default.removeObserver(endObserver)
        }
        endObserver = nil
    }
}
