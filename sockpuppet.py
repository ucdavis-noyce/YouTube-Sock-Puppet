from ytdriver import YTDriver, Video, VideoUnavailableException
import sys
import json
from datetime import datetime
import os
from random import choice

puppet = None

def parse_args():
    with open(sys.argv[1]) as f:
        return json.load(f)

def init_puppet(puppetId, profile_dir):
    global puppet
    puppet = dict(
        # driver=YTDriver(verbose=True, profile_dir=profile_dir),#, use_virtual_display=True),
        driver=YTDriver(browser='chrome', verbose=True, use_virtual_display=True),
        puppetId=puppetId,
        actions=[],
        start_time=datetime.now()
    )
    return puppet

def makedir(outputDir, d):
    dir = os.path.join(outputDir, d)
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir

def make_url(videoId):
    return 'https://youtube.com/watch?v=%s' % videoId

def add_action(action, params=None):
    print(action, params)
    puppet['actions'].append(dict(action=action, params=params))

def get_homepage():
    homepage = puppet['driver'].get_homepage()
    add_action('get_homepage', [vid.videoId for vid in homepage])
    return homepage

def get_recommendations():
    recommendations = puppet['driver'].get_recommendations()
    add_action('get_recommendations', [vid.videoId for vid in recommendations])
    return recommendations

def watch(video: Video, duration):
    driver = puppet['driver']
    driver.play(video, duration=duration)
    add_action('watch', video.videoId)

def save_puppet():
    js = dict(
            puppet_id=puppet['puppetId'],
            start_time=puppet['start_time'],
            end_time=datetime.now(),
            duration=puppet['duration'],
            description=puppet['description'],
            actions=puppet['actions'],
            args=args
        )
    with open(os.path.join(makedir(args['outputDir'], 'puppets'), puppet['puppetId']), 'w') as f:
        json.dump(js, f, default=str, indent=4)

def train():
    get_homepage()
    add_action("training_start")

    # get list of videoIds
    training_videos = args['training']

    # remove empty strings
    training_videos = [videoId for videoId in training_videos if len(videoId) > 0]
    
    # get number of videos to actually watch
    trainingN = int(args['trainingN'])

    # number of videos watched
    watched = 0
    
    for videoId in training_videos:
        # watch until N videos have been watched
        if watched >= trainingN:
            break
        # watch next video if available
        try:
            video = Video(None, make_url(videoId))
            watch(video, args['duration'])
            watched += 1
        except VideoUnavailableException:
            continue
        except Exception as e:
            print(e)
    add_action("training_end")

def test():
    get_homepage()
    add_action("testing_start")
    video = Video(None, make_url(args['testSeed']))
    for _ in range(20):
        watch(video, 0)
        r = get_recommendations()
        video = r[0]
    add_action("testing_end")

def intervention():
    get_homepage()
    add_action("intervention_start")
    for videoId in args['intervention']:
        video = Video(None, make_url(videoId))
        watch(video, args['duration'])
        get_homepage()
    add_action("intervention_end")


if __name__ == '__main__':
    args = parse_args()

    try:
        # conduct end-to-end experiment
        profile_dir = os.path.join(makedir(args['outputDir'], 'profiles'), args['puppetId'])
        init_puppet(args['puppetId'], profile_dir)

        for action in args['steps'].split(','):
            if action == 'train':
                train()
            if action == 'test':
                test()
            if action == 'intervention':
                intervention()
    
        # finalize puppet
        puppet['driver'].close()
        puppet['steps'] = args['steps']
        puppet['duration'] = args['duration']
        puppet['description'] = args['description']
        save_puppet()
    except Exception as e:
        exception = dict(time=datetime.now(), exception=str(e), module='sock-puppet')
        print(exception)
        with open(os.path.join(makedir(args['outputDir'], 'exceptions'), args['puppetId']), 'w') as f:
            json.dump(exception, f, default=str)
