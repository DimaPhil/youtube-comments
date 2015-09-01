__author__ = 'Dmitry Philippov'

import urllib
import urllib.request
import json

import time
import datetime

import re

API_KEY = "AIzaSyC1vyP1sSJPkEp2QNc1i-pyM2GRkJTPNXY"
DELAY = 5
BIG_DELAY = 50
MAX_BEST_VIDEOS_COUNT = 50

class Video:
    def __init__(self, title, published_at, video_id, comments=0):
        self.title = title
        self.published_at = published_at
        self.video_id = video_id
        self.comments = comments

    def __lt__(self, other):
        return (self.comments > other.comments) or ((self.comments == other.comments) and (self.published_at < other.published_at));

    def __gt__(self, other):
        return (self.comments < other.comments) or ((self.comments == other.comments) and (self.published_at > other.published_at));

last_update = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=BIG_DELAY)
best_videos = []


def parse_youtube_time(str_time):
    str_time = str_time[:-1]
    parts = list(map(int, re.split('-|T|:|\.', str_time)))
    return datetime.datetime(parts[0], parts[1], parts[2], parts[3], parts[4], parts[5])


def find_recent_videos():
    global last_update

    now = last_update.strftime("%Y-%m-%dT%H:%M:%S")
    last_update = datetime.datetime.now(datetime.timezone.utc)
    GET_QUERY = 'https://www.googleapis.com/youtube/v3/search?publishedAfter=' + str(now) + 'Z&order=relevance&part=snippet&maxResults=50&key=' + API_KEY

    request = urllib.request.urlopen(GET_QUERY);
    videos = json.loads(request.read().decode(request.info().get_param('charset') or 'utf-8'))
    recent_videos = []
    for video in videos['items']:
        try:
            title = video['snippet']['title']
            published_at = parse_youtube_time(video['snippet']['publishedAt'])
            video_id = video['id']['videoId']
            recent_videos.append(Video(title, published_at, video_id))
        except:
            continue
    return recent_videos


def update_best_videos(recent_videos):
    global best_videos
    for best_video in best_videos:
        '''minimal_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=BIG_DELAY)
        seconds_minimal = time.mktime(minimal_date.timetuple())
        seconds_best = time.mktime(best_video.published_at.timetuple())
        if seconds_minimal > seconds_best:
            continue'''
        recent_videos.append(best_video)
    best_videos = []

    ids = ','.join(str(video.video_id) for video in recent_videos)
    GET_QUERY = 'https://www.googleapis.com/youtube/v3/videos?part=statistics&id=' + ids + '&key=' + API_KEY
    request = urllib.request.urlopen(GET_QUERY);
    videos = json.loads(request.read().decode(request.info().get_param('charset') or 'utf-8'))
    for video in videos['items']:
        index = -1
        for i in range(len(recent_videos)):
            if recent_videos[i].video_id == video['id']:
                index = i
                break
        assert(index != -1)
        rvideo = recent_videos[index]
        new_video = Video(rvideo.title, rvideo.published_at, rvideo.video_id, int(video['statistics']['commentCount']))
        best_videos.append(new_video)

    best_videos.sort()
    best_videos = best_videos[:MAX_BEST_VIDEOS_COUNT]


def print_html():
    global best_videos

    html = open('index.html', 'w', encoding='utf-8')
    html.write('<html>\n')
    html.write('  <body>\n')
    html.write('    <table border=\"1\">\n')
    html.write('      <tr>\n')
    html.write('        <td>N<sup>o</sup></td>\n')
    html.write('        <td>Title</td>\n')
    html.write('        <td>Published at</td>\n')
    html.write('        <td>Video</td>\n')
    html.write('        <td>Comments count</td>\n')
    html.write('      </tr>\n')
    for i, video in enumerate(best_videos):
        html.write('      <tr>\n')
        html.write('        <td>' + str(i + 1) + '</td>\n')
        html.write('        <td>' + video.title + '</td>\n')
        html.write('        <td>' + str(video.published_at) + ' UTC</td>\n')
        html.write('        <td>http://www.youtube.com/watch?v=' + video.video_id + '</td>\n')
        html.write('        <td>' + str(video.comments) + '</td>\n')
        html.write('      </tr>\n')
    html.write('    </table>\n')
    html.write('  </body>\n')
    html.write('</html>\n')
    html.close()


def main():
    while True:
        print('Updating list of videos')
        print(last_update)
        recent_videos = find_recent_videos()
        update_best_videos(recent_videos)
        print_html()
        print('Finished')
        time.sleep(DELAY)

if __name__ == '__main__':
    main()