#!/usr/bin/env python

from panda3d.core import *
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import os

# Tell Panda3D to use OpenAL, not FMOD
loadPrcFileData("", "audio-library-name p3openal_audio")

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText

def addInstructions(pos, msg):
    return OnscreenText(text=msg, style=1, fg=(0, 0, 0, 1), shadow=(1, 1, 1, 1),
                        parent=base.a2dTopLeft, align=TextNode.ALeft,
                        pos=(0.08, -pos - 0.04), scale=.06)

class MediaPlayer(ShowBase):
    def __init__(self, media_file_native, media_file_panda):
        ShowBase.__init__(self)
        self.media_file_native = media_file_native  # For mutagen and file handling
        self.media_file_panda = media_file_panda    # For Panda3D operations
        self.is_audio_only = media_file_native.lower().endswith(".mp3")

        self.instructions = [
            addInstructions(0.06, "K: Play/Pause"),
            addInstructions(0.12, "S: Stop"),
            addInstructions(0.18, "ESC: Quit the player")
        ]

        if self.is_audio_only:
            self.setup_audio_with_metadata()
        else:
            self.setup_video()

        self.accept("escape", self.quit_program)

    def setup_video(self):
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

        self.accept("k", self.playpause)
        self.accept("K", self.playpause)
        self.accept("s", self.stopsound)
        self.accept("S", self.stopsound)

    def setup_audio_with_metadata(self):
        self.sound = loader.loadSfx(self.media_file_panda)
        assert self.sound, "Failed to load MP3!"

        metadata = self.extract_metadata(self.media_file_native)
        if metadata:
            self.display_metadata(metadata)

        self.accept("k", self.playpause)
        self.accept("K", self.playpause)
        self.accept("s", self.stopsound)
        self.accept("S", self.stopsound)

    def extract_metadata(self, file_path):
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
        addInstructions(0.30, f"Title: {metadata['title']}")
        addInstructions(0.36, f"Artist: {metadata['artist']}")
        addInstructions(0.42, f"Album: {metadata['album']}")

        if metadata["album_art"]:
            album_tex = loader.loadTexture(metadata["album_art"])
            album_tex.setMagfilter(Texture.FTLinear)
            album_tex.setMinfilter(Texture.FTLinearMipmapLinear)

            album_card = self.render2d.attachNewNode(CardMaker("AlbumCover").generate())
            album_card.setTexture(album_tex)
            album_card.setScale(2)
            album_card.setPos(-1, 0, -1)

    def playpause(self):
        if self.sound.status() == AudioSound.PLAYING:
            t = self.sound.getTime()
            self.sound.stop()
            self.sound.setTime(t)
        else:
            self.sound.play()

    def stopsound(self):
        self.sound.stop()

    def quit_program(self):
        print("Escape key pressed. Exiting...")
        self.cleanup()
        self.userExit()

    def cleanup(self):
        if self.is_audio_only and os.path.exists("album_art_temp.jpg"):
            os.remove("album_art_temp.jpg")

def select_media_file():
    Tk().withdraw()
    filetypes = [("Media Files", "*.mp3 *.mp4"), ("All Files", "*.*")]
    file_path_native = askopenfilename(title="Select a Media File", filetypes=filetypes)
    if file_path_native:
        file_path_panda = Filename.fromOsSpecific(file_path_native).getFullpath()
        return file_path_native, file_path_panda
    return None, None

selected_file_native, selected_file_panda = select_media_file()
if selected_file_native and selected_file_panda:
    player = MediaPlayer(selected_file_native, selected_file_panda)
    player.run()
else:
    print("No file selected. Exiting...")




