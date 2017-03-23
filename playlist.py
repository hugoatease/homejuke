import pychromecast
import requests
import random
from time import sleep
from requests.auth import HTTPBasicAuth

LFM_API_KEY = '57ee3318536b23ee81d6b27e36997cde'
SPOTIFY_API_CLIENT = 'b5c1e08b7d2846edb40ad73eadcbce95'
SPOTIFY_API_SECRET = '6f92952220eb4b36975d14e928226db2'

def getTopArtists(username):
    request = requests.get('http://ws.audioscrobbler.com/2.0/', params={'format': 'json', 'api_key': LFM_API_KEY, 'method': 'user.gettopartists', 'user': username})
    print request.json()
    return request.json()['topartists']['artist']

def getSpotifyToken():
    request = requests.post('https://accounts.spotify.com/api/token', data={'grant_type': 'client_credentials'}, auth=HTTPBasicAuth(SPOTIFY_API_CLIENT, SPOTIFY_API_SECRET))
    return request.json()['access_token']

def getSpotifyArtistId(bearer, artist):
    search = requests.get('https://api.spotify.com/v1/search', headers={'Authorization': 'Bearer ' + bearer}, params={'q': artist['name'], 'type': 'artist', 'limit': 1})
    return search.json()['artists']['items'][0]['id']

def getSpotifySeed(bearer, artists):
    choice = []
    for i in xrange(0, 5):
        choice.append(random.choice(artists))

    seed = map(lambda c, bearer=bearer: getSpotifyArtistId(bearer, c), choice)
    return seed

def getRecommendations(bearer, seed):
    seed_artists = reduce(lambda s, a: s + a + ',', seed, '')[0:-1]
    recs = requests.get('https://api.spotify.com/v1/recommendations', headers={'Authorization': 'Bearer ' + bearer}, params={'market': 'FR', 'seed_artists': seed_artists, 'limit': 100})
    tracks = map(lambda t: t['id'], recs.json()['tracks'])
    return tracks

def queueInMopidy(tracks):
    data = {
      'id': 500,
      'method': 'core.tracklist.add',
      'jsonrpc': '2.0',
      'params': {
        'uris': map(lambda t: 'spotify:track:' + t, tracks)
      }
    }
    print data

    requests.post('http://raspberrypi.local:6680/mopidy/rpc', json={
      'id': 409,
      'method': 'core.tracklist.clear',
      'jsonrpc': '2.0',
      'params': {}
    })
    request = requests.post('http://raspberrypi.local:6680/mopidy/rpc', json=data)
    requests.post('http://raspberrypi.local:6680/mopidy/rpc', json={
      'id': 501,
      'method': 'core.playback.play',
      'jsonrpc': '2.0',
      'params': {}
    })
    print request.json()

def launchCast(uuid):
    casts = pychromecast.get_chromecasts()
    cast = filter(lambda x: str(x.uuid) == uuid, casts)[0]
    print cast
    cast.media_controller.play_media('http://192.168.2.1:8000/stream', 'audio/vorbis')
    sleep(5)


if __name__ == '__main__':
    bearer = getSpotifyToken()
    top = getTopArtists('hugoatease')
    seed = getSpotifySeed(bearer, top)
    tracks = getRecommendations(bearer, seed)
    queueInMopidy(tracks)
    launchCast('0c63adba-2bab-cfef-697d-bf5167f98e31')
