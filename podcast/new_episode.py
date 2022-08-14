from datetime import datetime
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from os import listdir, path, rename

import math
import re
import sys
import xml.etree.ElementTree as ET


def find_next_episode():
    files = listdir('episodes/')
    episodes = list(filter(lambda file: file.endswith('mp3'), files))
    episodes.sort()
    return str(int(episodes[-1].split('.')[0]) + 1)

def get_duration(file_path):
    audio = MP3(file_path)
    s = math.ceil(audio.info.length)

    if s >= 3600:
        return f'{int(s / 3600)}:{int(s % 3600 / 60)}:{int(s % 60)}'
    else:
        return f'{int(s / 60)}:{int(s % 60)}'

def add_id3v2_tags(file_path, title, year):
    audio = EasyID3(file_path)
    audio['title'] = title
    audio['artist'] = 'D-sektionen'
    audio['genre'] = 'Podcast'
    audio['date'] = year
    audio.save()

def print_podcast_rss(title, description, author, duration, size, image, audio):
    now = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    base_path = 'https://dsek-lth.github.io/podcast/'
    image_path = f'{base_path}{image}'
    audio_path = f'{base_path}{audio}'

    title = f'<![CDATA[{title}]]>'
    description = f'<![CDATA[{description}]]>'

    new_episode = '\n'.join([
        f'    <item>',
        f'      <title>{title}</title>',
        f'      <description>{description}</description>',
        f'      <guid isPermaLink="false">{audio_path}</guid>',
        f'      <pubDate>{now}</pubDate>',
        f'      <itunes:summary>{description}</itunes:summary>',
        f'      <itunes:author>{author}</itunes:author>',
        f'      <itunes:image>{image_path}</itunes:image>',
        f'      <itunes:duration>{duration}</itunes:duration>',
        f'      <itunes:subtitle>{description}</itunes:subtitle>',
        f'      <enclosure url="{audio_path}" length="{size}" type="audio/mpeg" />',
        f'    </item>',
    ])

    build_date = f'<lastBuildDate>{now}</lastBuildDate>'

    print('--------------------------------')
    print('MANUAL ACTIONS TO DO IN feed.xml')
    print('--------------------------------')
    print('Update:')
    print(build_date)
    print()
    print('Add:')
    print(new_episode)

def valid_file(file_path):
    size = path.getsize(file_path)
    bitrate = MP3(file_path).info.bitrate / 1000
    is_mp3 = file_path.endswith('.mp3')

    if not is_mp3:
        print('File is not an mp3 file')
        return False

    if size > 100_000_000: # 100 MB
        if bitrate > 192:
            print(f'File is too large (>100MB) and has a very high bitrate ({bitrate}), try lowering it')
            print(f"eg. 'lame -b 192 {file_path} smaller-file.mp3'")
            return False
        print('File is too large (>100MB)')
        return False
    return True

def valid_arguments():
    if len(sys.argv) != 6:
        print('Wrong number of arguments')
        return False

    if not path.isfile(sys.argv[1]):
        print(f'File {sys.argv[1]} does not exist')
        return False

    image_path = 'images/' + sys.argv[2]
    if not path.isfile(image_path):
        print(f'Cover image {image_path} does not exist')
        return False

    if not sys.argv[2].lower().endswith(('.png', '.jpg', '.jpeg')):
        print(f'Cover image {sys.argv[2]} is not a valid image file')
        return False

    if re.match('^\d+\. .*$', sys.argv[3]) is not None:
        print('Title should not contain episode number')
        return False

    return True

def main():
    if not valid_arguments():
        return False

    year = datetime.now().strftime('%Y')
    episode_number = find_next_episode()
    file_path = sys.argv[1]
    image_name = sys.argv[2]
    title = f'{episode_number}. {sys.argv[3]}'
    author = sys.argv[4]
    description = sys.argv[5]

    if not valid_file(file_path):
        return False

    add_id3v2_tags(file_path, title, year)

    print_podcast_rss(title, description, author, get_duration(file_path), path.getsize(file_path), f'images/{image_name}', f'episodes/{episode_number}.mp3')
    rename(file_path, f'episodes/{episode_number}.mp3')

    return True


if __name__ == '__main__':
    try:
        if main():
            print('Done')
        else:
            raise Exception('Verification failed')
    except Exception as e:
        print(f'Aborting due to {type(e).__name__}: {e}')
        print()
        print('Usage:')
        print('  python3 new_episode.py audio_file_path cover_image_name title author description')
        print()
        print()
        raise e