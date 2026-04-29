from pprint import pprint
import time
from os import listdir
import os.path

import tkinter as tk
from tkinter import ttk

from tkinterdnd2 import DND_FILES, TkinterDnD

from tinytag import TinyTag

import pydub
import pyaudio

root = TkinterDnD.Tk()
root.title("mmp")

DEBUG = False

playlist = [
    "./Demon_Days/06 - Karma Police.flac",
    "./Demon_Days/06 - Feel Good Inc.mp3",
]
playlistindex = 0

paused = True


def frame(f):
    if DEBUG:
        f["borderwidth"] = 2
        f["relief"] = "sunken"


previous_image = tk.PhotoImage(file="previous.png")
pause_image = tk.PhotoImage(file="pause.png")
play_image = tk.PhotoImage(file="play.png")
next_image = tk.PhotoImage(file="next.png")

mainframe = ttk.Frame(root, padding=5)
mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

mainframe["width"] = 500
mainframe["height"] = 400

title_frame = ttk.Frame(mainframe)
title_frame.grid(column=1, row=1)
frame(title_frame)

song_title = tk.StringVar()
song_title.set("Nothing playing")
ttk.Label(title_frame, textvariable=song_title, font="TkHeadingFont", padding=5).grid(
    column=1, row=1
)

artist_album_frame = ttk.Frame(mainframe)
artist_album_frame.grid(column=1, row=2)
frame(artist_album_frame)

song_artist = tk.StringVar()
ttk.Label(
    artist_album_frame,
    textvariable=song_artist,
    padding=5,
    anchor="center",
).grid(column=1, row=1)

ttk.Label(artist_album_frame, text=" - ").grid(column=2, row=1)

song_album = tk.StringVar()
ttk.Label(artist_album_frame, textvariable=song_album, padding=5, anchor="center").grid(
    column=3, row=1
)


controls_frame = ttk.Frame(mainframe)
controls_frame.grid(column=1, row=3)
frame(controls_frame)


def split_files(files):
    output = []
    making = ""
    escaped = False
    for char in files + " ":
        if char == "{":
            escaped = True
        elif char == "}":
            escaped = False
        elif char == " " and not escaped:
            output.append(making)
            making = ""
        else:
            making += char
    return output


def extractfiles(dircontents, depth=0):
    music_extentions = ["mp3", "flac", "wav", "ogg"]

    newplaylist = []
    dirs = []
    for file in dircontents:
        is_music = False
        for extention in music_extentions:
            if file.endswith("." + extention) and os.path.isfile(file):
                is_music = True
        if is_music:
            newplaylist.append(file)
        if os.path.isdir(file):
            dirs.append(file)

    newplaylist.sort()

    dirs.sort()
    for dir in dirs:
        if not dir.endswith("/"):
            dir += "/"
        files = map(lambda x: dir + x, listdir(dir))
        newplaylist += extractfiles(list(files), depth + 1)

    return newplaylist


def filedropped(e):
    global playlist, playlistindex
    filenames = split_files(e.data)
    pprint(filenames)

    newplaylist = extractfiles(filenames)
    pprint(newplaylist)

    if len(newplaylist) > 0:
        playlist = newplaylist

        playlistindex = 0

        play_file(playlist[playlistindex])

    # play_file(e.data)


# register the listbox as a drop target
mainframe.drop_target_register(DND_FILES)
mainframe.dnd_bind("<<Drop>>", filedropped)


def previoussong():
    global playlistindex, stream
    playlistindex -= 1
    if playlistindex < 0:
        playlistindex = -1
        pause()
        stream = None
        song_album.set("")
        song_artist.set("")
        song_title.set("Nothing playing")
        return
    play_file(playlist[playlistindex])


def nextsong():
    global playlistindex, stream
    playlistindex += 1
    if playlistindex >= len(playlist):
        playlistindex = len(playlist)
        pause()
        stream = None
        song_album.set("")
        song_artist.set("")
        song_title.set("Nothing playing")
        return
    play_file(playlist[playlistindex])


def playpause():
    if paused:
        play()
    else:
        pause()


def pause():
    global paused
    if stream is not None:
        paused = True
        stream.stop_stream()
        playpause_button["image"] = play_image
    updateplaylistview()


def play():
    global paused
    if stream is not None:
        paused = False
        stream.start_stream()
        playpause_button["image"] = pause_image
    updateplaylistview()


previous_button = ttk.Button(controls_frame, image=previous_image, command=previoussong)
previous_button.grid(row=1, column=1)
playpause_button = ttk.Button(controls_frame, image=play_image, command=playpause)
playpause_button.grid(row=1, column=2)
next_button = ttk.Button(controls_frame, image=next_image, command=nextsong)
next_button.grid(row=1, column=3)


playlist_frame = ttk.Frame(mainframe, padding=0)
frame(playlist_frame)
ttk.Label(playlist_frame, text="Playlist:", font="TkHeadingFont").grid(sticky="W")

playlistview = ttk.Treeview(
    playlist_frame,
    columns=("playing", "file", "folder", "index"),
    show="headings",
    displaycolumns=("playing", "file"),
)
playlistview.column("playing", width=15)
playlistview.column("file")
playlistview.heading("file", text="File")
playlistview.heading("folder", text="Folder")
playlistview.grid(sticky="nesw")
playlistview.insert("", "end", values=(">", "nice guys"))


def itemClick(e):
    global playlistindex
    playlistindex = int(playlistview.set(playlistview.focus(), "index")) - 1
    nextsong()


playlistview.tag_bind("ttk", "<Double-1>", itemClick)

pl_shown = False


def updateplaylistview():
    for child in playlistview.get_children():
        playlistview.delete(child)

    index = 0
    for song in playlist:
        filename = song.split("/")[-1]
        folder = song.removesuffix(filename)
        char = ""
        if index == playlistindex:
            if paused:
                char = "||"
            else:
                char = ">"

        playlistview.insert(
            "", "end", values=(char, filename, folder, index), tags=("ttk",)
        )
        index += 1


def show_hide_playlist():
    global pl_shown
    pl_shown = not pl_shown
    if pl_shown:
        playlist_frame.grid(row=7, column=1, sticky="NSEW")
    else:
        playlist_frame.grid_forget()


show_hide_playlist_button = ttk.Button(
    mainframe, text="pl", command=show_hide_playlist
).grid(row=6, column=1, sticky="W")


stream = None

p = pyaudio.PyAudio()


index = 0


def play_file(file):
    global stream, paused, index

    if stream is not None:
        stream.close()

    print("loading tags")
    tags = TinyTag.get(file)
    song_title.set(str(tags.track) + " - " + tags.title)
    song_artist.set(tags.artist)
    song_album.set(tags.album)
    print("tags loaded")

    print("loading audioSegment")
    audio = pydub.AudioSegment.from_file(file)
    print("audioSegment lodaded")

    index = 0

    bytesperframe = audio.channels * audio.sample_width

    def callback(in_data, frame_count, time_info, status_flag):
        global index
        frame_count *= bytesperframe
        data = audio.raw_data[index : index + frame_count]
        index += frame_count
        if index > len(audio.raw_data):
            nextsong()
        return (data, pyaudio.paContinue)

    stream = p.open(
        format=p.get_format_from_width(audio.sample_width),
        channels=audio.channels,
        rate=audio.frame_rate,
        output=True,
        stream_callback=callback,
        frames_per_buffer=1024,
    )
    # play_obj.write(audio.raw_data)
    print(
        audio.channels,
        audio.frame_rate,
        p.get_format_from_width(audio.sample_width),
    )

    play()


play_file(playlist[playlistindex])
pause()

root.mainloop()
