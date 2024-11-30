#!/usr/bin/env python

from panda3d.core import *
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
import os
import threading

# Tell Panda3D to use OpenAL, not FMOD
loadPrcFileData("", "audio-library-name p3openal_audio")

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText

def addInstructions(pos, msg):
    return OnscreenText(text=msg, style=1, fg=(0, 0, 0, 1), shadow=(1, 1, 1, 1),
                        parent=base.a2dTopLeft, align=TextNode.ALeft,
                        pos=(0.08, -pos - 0.04), scale=.06)

class MediaPlayer(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.media_file_native = None  # Windows-style path for mutagen
        self.media_file_panda = None  # Unix-style path for Panda3D
        self.is_audio_only = None
        self.sound = None
        self.tex = None

        # Console-related attributes
        self.running = True
        self.thread = threading.Thread(target=self.run_console, daemon=True)
        self.thread.start()

        self.console_instructions = [
            "Commands:",
            "  load <file_path>: Load a media file (mp3 or mp4)",
            "  play: Play the loaded media",
            "  pause: Pause the media playback",
            "  stop: Stop the media playback",
            "  exit: Quit the media player"
        ]
        self.print_instructions()

    def print_instructions(self):
        """Print the console instructions."""
        print("\n--- Media Player Console ---")
        for line in self.console_instructions:
            print(line)
        print("-----------------------------\n")

    def run_console(self):
        """Run the command-line interface."""
        while self.running:
            command = input("MediaPlayer> ").strip()
            if command.startswith("load"):
                _, path = command.split(" ", 1)
                self.load_media(path.strip())
            elif command == "play":
                self.play_media()
            elif command == "pause":
                self.pause_media()
            elif command == "stop":
                self.stop_media()
            elif command == "exit":
                self.quit_program()
                break
            else:
                print(f"Unknown command: {command}")
                self.print_instructions()

    def load_media(self, file_path):
        """Load the specified media file."""
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return

        self.media_file_native = file_path
        self.media_file_panda = Filename.fromOsSpecific(file_path).getFullpath()
        self.is_audio_only = file_path.lower().endswith(".mp3")

        if self.is_audio_only:
            self.setup_audio_with_metadata()
        else:
            self.setup_video()

        print(f"Loaded: {file_path}")

    def setup_video(self):
        """Set up video playback (MP4 with audio)."""
        if self.tex:
            self.tex.clear()  # Clear existing texture if loaded

        self.tex = MovieTexture("VideoTexture")
        self.tex.setMagfilter(Texture.FTLinear)
        self.tex.setMinfilter(Texture.FTLinearMipmapLinear)

        success = self.tex.read(self.media_file_panda)
        assert success, "Failed to load video!"

        cm = CardMaker("FullscreenCard")
        cm.setFrameFullscreenQuad()
        cm.setUvRange(self.tex)
        card = NodePath(cm.generate())
        card.reparentTo(self.render2d)
        card.setTexture(self.tex)

        self.sound = loader.loadSfx(self.media_file_panda)
        self.tex.synchronizeTo(self.sound)

        print("Video loaded successfully.")

    def setup_audio_with_metadata(self):
        """Set up audio-only playback (MP3) and extract metadata."""
        if self.sound:
            self.sound.stop()  # Stop existing audio

        self.sound = loader.loadSfx(self.media_file_panda)
        assert self.sound, "Failed to load MP3!"

        metadata = self.extract_metadata(self.media_file_native)
        if metadata:
            self.display_metadata(metadata)

        print("Audio loaded successfully.")

    def extract_metadata(self, file_path):
        """Extract metadata and album cover from MP3."""
        metadata = {}
        try:
            audio = MP3(file_path, ID3=ID3)
            id3_tags = ID3(file_path)

            metadata["title"] = str(id3_tags.get("TIT2", "Unknown Title"))
            metadata["artist"] = str(id3_tags.get("TPE1", "Unknown Artist"))
            metadata["album"] = str(id3_tags.get("TALB", "Unknown Album"))

            if "APIC:" in id3_tags:
                apic = id3_tags["APIC:"]
                album_art_path = "album_art_temp.jpg"
                with open(album_art_path, "wb") as img:
                    img.write(apic.data)
                metadata["album_art"] = album_art_path
            else:
                metadata["album_art"] = None
        except Exception as e:
            print(f"Error extracting metadata: {e}")
        return metadata

    def display_metadata(self, metadata):
        """Display metadata and album cover."""
        print(f"Title: {metadata['title']}")
        print(f"Artist: {metadata['artist']}")
        print(f"Album: {metadata['album']}")

    def play_media(self):
        """Play the loaded media."""
        if not self.sound:
            print("No media loaded. Use 'load <file_path>' to load a file.")
            return

        self.sound.play()
        print("Playing media...")

    def pause_media(self):
        """Pause media playback."""
        if not self.sound or self.sound.status() != AudioSound.PLAYING:
            print("No media is currently playing.")
            return

        t = self.sound.getTime()
        self.sound.stop()
        self.sound.setTime(t)
        print("Media paused.")

    def stop_media(self):
        """Stop media playback."""
        if not self.sound:
            print("No media loaded to stop.")
            return

        self.sound.stop()
        print("Media stopped.")

    def quit_program(self):
        """Quit the program."""
        print("Exiting media player...")
        self.running = False
        self.cleanup()
        self.userExit()

    def cleanup(self):
        """Clean up temporary files (album art)."""
        if self.is_audio_only and os.path.exists("album_art_temp.jpg"):
            os.remove("album_art_temp.jpg")

# Run the media player
player = MediaPlayer()
player.run()
