import contextlib
import glob
import os
import shutil
import subprocess
import sys
import wave
import re

import cv2
from pydub import AudioSegment
from tqdm import tqdm
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def get_NoteList(fpath):
    f = open(fpath)
    text = f.read()
    f.close()
    text = text.split('\n')
    note_list = []
    for line in text:
        # l = re.findall(r"[^．。？\?]+([．。？\?]|\.(?![0-9]))", line)
        l = re.findall(r'([^．。？\?]+?([．。？\?]|((?<!\d)\.)|$))', line)
        l = [i[0] for i in l]

        l = [l[i // 2] if i % 2 == 0 else "silent" for i in range(len(l) * 2)]

        # print(l)
        note_list.append(l)

    return note_list


def make_Sound(params, text, fname):
    if text == 'silent':  # silent
        sound_len = 1000
        sound = AudioSegment.silent(
            duration=sound_len, frame_rate=params["framerate"])
        sound.export(fname, format="wav")
    else:  # talk
        open_jtalk = ['open_jtalk']
        mech = ['-x', '/var/lib/mecab/dic/open-jtalk/naist-jdic']
        htsvoice = [
            '-m', './MMDAgent_Example-1.8/Voice/mei/mei_normal.htsvoice']
        speed = ['-r', str(params["speed"])]
        sampling = ['-s', str(params["framerate"])]
        outwav = ['-ow', fname]
        cmd = open_jtalk + mech + htsvoice + speed + sampling + outwav
        c = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        c.stdin.write(text.encode('utf-8'))
        c.stdin.close()
        c.wait()


def get_SoundLen(fname):
    with contextlib.closing(wave.open(fname, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
    return duration


def join_Sound(i, fname):
    sound_path_fname = './sound/tmp{:03}/sound_path.txt'.format(i)
    sound_list = sorted(glob.glob(os.path.join(
        './sound/tmp{:03}'.format(i), '*.wav')))
    sound_path = ''
    for line in sound_list:
        sound_path += 'file ' + os.path.split(line)[-1] + '\n'
    with open(sound_path_fname, mode='w') as f:
        f.write(sound_path)
    cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i',
           sound_path_fname, '-loglevel', 'quiet', '-c', 'copy', fname]
    c = subprocess.call(cmd)


def adjust_Sound(fname, add_len=None):
    sound_len = get_SoundLen(fname)
    sound = AudioSegment.from_file(fname)
    add_len = int(sound_len + 1) * 1000
    silent = AudioSegment.silent(duration=add_len)
    result = silent.overlay(sound, position=0)
    result.export(fname, format="wav")


def pil2cv(imgPIL):
    imgCV_RGB = np.array(imgPIL, dtype=np.uint8)
    imgCV_BGR = np.array(imgPIL)[:, :, ::-1]
    return imgCV_BGR


def cv2pil(imgCV):
    imgCV_RGB = imgCV[:, :, ::-1]
    imgPIL = Image.fromarray(imgCV_RGB)
    return imgPIL


def cv2_putText(img, text, org, fontFace, fontScale, color):
    x, y = org
    b, g, r = color
    colorRGB = (r, g, b)
    imgPIL = cv2pil(img)
    draw = ImageDraw.Draw(imgPIL)
    fontPIL = ImageFont.truetype(font=fontFace, size=fontScale)
    draw.text(xy=(x, y), text=text, fill=colorRGB, font=fontPIL)
    imgCV = pil2cv(imgPIL)
    return imgCV


def make_caption(text):
    text_list = [t.replace("silent", "\n") for t in text]
    for t in text_list:
        if len(t) > 90:
            print("一文が長すぎます")
            print(t)
    if len(text_list) > 16:
        print("行数が多すぎます")
        print(text_list)

    text = "".join(text_list)

    width = 1920
    height = 240

    img = np.ones((height, width, 3), np.uint8) * 255
    fontPIL = "meiryo.ttc"

    img = cv2_putText(img,
                      text=text,
                      org=(10, 10),
                      fontFace=fontPIL,
                      fontScale=20,
                      color=(0, 0, 0))

    return img


def make_SilentVideo(slide, sound_len, fname, note_list):
    img = cv2.resize(cv2.imread(slide), (1920, 1080))
    caption = make_caption(note_list)
    img = cv2.vconcat([img, caption])

    h, w = img.shape[:2]
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    video = cv2.VideoWriter(fname, fourcc, 20.0, (w, h))
    framecount = sound_len * 20
    for _ in range(int(framecount)):
        video.write(img)
    video.release()


def join_SilentVideo_Sound(silent_video, sound, fname):
    cmd = ['ffmpeg', '-y', '-i', silent_video, '-i', sound,
           '-loglevel', 'quiet', './video/{:03}.mp4'.format(fname)]
    c = subprocess.call(cmd)


def join_Video(params):
    video_path_fname = './video/video_path.txt'
    video_list = sorted(glob.glob(os.path.join('./video', '*.mp4')))
    video_path = ''
    for line in video_list:
        video_path += 'file ' + os.path.split(line)[-1] + '\n'
    with open(video_path_fname, mode='w') as f:
        f.write(video_path)
    cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i',
           video_path_fname, '-loglevel', 'quiet', '-c', 'copy', './out/' + params["input"].replace('./slide/', '') + '.mp4']
    c = subprocess.call(cmd)


if __name__ == '__main__':
    input_path = "./slide"
    files = os.listdir(input_path)
    dirs = [f for f in files if os.path.isdir(os.path.join(input_path, f))]

    for dir in dirs:
        print(f"{dir} start")
        params = {
            "input": f"./slide/{dir}",
            "output": "out.mp4",
            "framerate": 46000,
            "speed": 1.1
        }

        os.makedirs('./sound', exist_ok=True)
        os.makedirs('./silent_video', exist_ok=True)
        os.makedirs('./video', exist_ok=True)

        note_list = get_NoteList(os.path.join(
            params["input"], f"{params['input'].replace('./slide/', '')}-scenario.txt"))
        slide_path = sorted(glob.glob(os.path.join(params["input"], '*.jpeg')))
        note_num, slide_num = len(note_list), len(slide_path)

        if note_num != slide_num:
            print('Cannot run')
            sys.exit()

        for i in tqdm(range(note_num)):
            sound_fname = './sound/{:03}.wav'.format(i)
            silent_video_fname = './silent_video/{:03}.mp4'.format(i)

            # make sound
            for j, line in enumerate(note_list[i]):
                os.makedirs('./sound/tmp{:03}'.format(i), exist_ok=True)
                tmp_fname = './sound/tmp{:03}/{:03}.wav'.format(i, j)
                make_Sound(params, line, tmp_fname)
            join_Sound(i, sound_fname)
            adjust_Sound(sound_fname)

            # make silentvideo
            sound_len = get_SoundLen(sound_fname)
            make_SilentVideo(slide_path[i], sound_len,
                             silent_video_fname, note_list[i])

            # make video
            join_SilentVideo_Sound(silent_video_fname, sound_fname, i)

        join_Video(params)

        # delete tmp folders
        shutil.rmtree("sound")
        shutil.rmtree("silent_video")
        shutil.rmtree("video")

        print(f"{dir} end")
        print("-" * 100)
