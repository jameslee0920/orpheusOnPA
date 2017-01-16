from flask import Flask, request, redirect, g, render_template, jsonify, url_for
import json
import requests
import random
import base64
import urllib
import os
import pprint
import sys
import pandas as pd
from time import sleep
from recommender import User, Orpheus

LogInfo = {
    'playlist' : None,
    'username' : None,
    'displayname' : None
}

GLOBAL = {
    'authorization_header': None,
    'avatar': None,
    'spotify_playlists_ids': [],
    'spotify_playlists_names': [],
    'tracklist': [],
    'choice': ['energy']
    }
PLAYLIST = {
    'list1': [],
    'list2': [],
    'list3': [],
    'list4': [],
    'list5': [],
    'list6': []
}
USER = {
    'user_1': [],
    'user_2': [],
    'user_3': [],
    'user_4': [],
    'user_5': [],
    'user_6': []
}
Displayname = {
    'user_1': "User 1",
    'user_2': "User 2",
    'user_3': "User 3",
    'user_4': "User 4",
    'user_5': "User 5",
    'user_6': "User 6",
}

IMAGES = {
    'user_1': "static/img/portfolio/thumbnails/1.jpg",
    'user_2': "static/img/portfolio/thumbnails/2.jpg",
    'user_3': "static/img/portfolio/thumbnails/3.jpg",
    'user_4': "static/img/portfolio/thumbnails/4.jpg",
    'user_5': "static/img/portfolio/thumbnails/5.jpg",
    'user_6': "static/img/portfolio/thumbnails/6.jpg",
}



RECOMMENDER = None


app = Flask(__name__)

#  Client Keys
# James
CLIENT_ID = "35a534a9bf1c446c9d9b0c6acd7f9aac"
CLIENT_SECRET = "f26b4a6600de46419e98d45bc9b939fe"
# Oamar (for testing purpose only)
#CLIENT_ID = "6fd8426e0d5842c8a71f5fb2fe500755"
#CLIENT_SECRET = "c8dd889c094b47f99e89ae221a29df9b"

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)


# Server-side Parameters
LOCAL = True
if LOCAL:
    # James
    CLIENT_ID = "35a534a9bf1c446c9d9b0c6acd7f9aac"
    CLIENT_SECRET = "f26b4a6600de46419e98d45bc9b939fe"
    CLIENT_SIDE_URL = "http://127.0.0.1"
    PORT = 5000
    REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
    PATH_TO_DATA = 'processed_data/'
else:
    # Oamar (for testing purpose only)
    CLIENT_ID = "6fd8426e0d5842c8a71f5fb2fe500755"
    CLIENT_SECRET = "c8dd889c094b47f99e89ae221a29df9b"
    CLIENT_SIDE_URL = "http://myorpheus.servemp3.com"
    REDIRECT_URI = "{}/callback/q".format(CLIENT_SIDE_URL)
    PATH_TO_DATA = '/home/3rdworldjuander/mysite/processed_data/'

#CLIENT_SIDE_URL = "http://127.0.0.1"
#CLIENT_SIDE_URL = "http://3rdworldjuander.pythonanywhere.com"
#CLIENT_SIDE_URL = "http://myorpheus.servemp3.com"
#PORT = 5000
#REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
#REDIRECT_URI = "{}/callback/q".format(CLIENT_SIDE_URL)
SCOPE = "playlist-modify-public playlist-modify-private playlist-read-private"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()


auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    "client_id": CLIENT_ID
}
def get_orpheus_playlist():
    users = []
    for name, spotify_ids in PLAYLIST.iteritems():
        users.append(User(name, spotify_ids))

    # orpheus = Orpheus(users, PATH_TO_DATA)
    tracks = RECOMMENDER.get_playlist(users, num_tracks=50)['spotify_id']
    return tracks


@app.route("/")
def index():
    # Auth Step 1: Authorization
    url_args = "&".join(["{}={}".format(key,urllib.quote(val)) for key,val in auth_query_parameters.iteritems()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)

@app.route("/callback/q")
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI
    }
    base64encoded = base64.b64encode("{}:{}".format(CLIENT_ID, CLIENT_SECRET))
    headers = {"Authorization": "Basic {}".format(base64encoded)}
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]

    # Auth Step 6: Use the access token to access Spotify API
    GLOBAL['authorization_header'] = {"Authorization":"Bearer {}".format(access_token)}

    # Get profile data
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=GLOBAL['authorization_header'])
    profile_data = json.loads(profile_response.text)
    LogInfo['username'] = profile_data['id']
    LogInfo['displayname'] = profile_data['display_name']
    return redirect('/loading')


@app.route('/loading')
def loading():
    return render_template("loading.html")

@app.route('/load_orpheus')
def load_orpheus():
    global RECOMMENDER
    RECOMMENDER = Orpheus(PATH_TO_DATA)
    return redirect('/orpheus')

@app.route('/orpheus')
def orpheus():
    return render_template("index.html", images=IMAGES, names=Displayname, choice = GLOBAL['choice'][0].capitalize())


def create_playlist():
    """Create a playlist and return a list of names to display"""

    # Get all the names
    Displayname_list = [Displayname['user_1'], Displayname['user_2'], Displayname['user_3'], Displayname['user_4'], Displayname['user_5'], Displayname['user_6']]
    namelist = []
    for itemname in Displayname_list:
        if not itemname.startswith('User'):
            namelist.append(itemname)
    finallist= ", ".join(namelist)

    # Create empty playlist
    data = json.dumps({'name': 'Orpheus by {}'.format(finallist)})
    newlist = requests.post("https://api.spotify.com/v1/users/{}/playlists".format(LogInfo['username']), data, headers = GLOBAL['authorization_header'])
    textnewlist = json.loads(newlist.text)
    LogInfo['playlist'] = textnewlist['id']
    return finallist

@app.route("/orpheus/player")
def player():
    # Create playlist
    finallist = create_playlist()

    # Getting tracks for playlist
    tracks = get_orpheus_playlist()

    # POST tracks to playlist
    print tracks
    playlist_api_endpoint = "https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(LogInfo['username'], LogInfo['playlist'])
    data = json.dumps({'uris': list(tracks)})
    playlists_songs = requests.put(playlist_api_endpoint, data, headers=GLOBAL['authorization_header'])
    print playlists_songs
    src = "https://embed.spotify.com/?uri=spotify%3Auser%3A{}%3Aplaylist%3A{}&theme=white".format(LogInfo['username'], LogInfo['playlist'])
    return render_template("player.html", src = src, display = finallist, choice = "", playertype = "Default")

@app.route("/orpheus/energy")
def energychoice():
    GLOBAL['choice'][0] = 'energy'
    return redirect(url_for('orpheus', _anchor = "services"))

@app.route("/orpheus/liveness")
def livenesschoice():
    GLOBAL['choice'][0] = 'liveness'
    return redirect(url_for('orpheus', _anchor = "services"))

@app.route("/orpheus/tempo")
def tempochoice():
    GLOBAL['choice'][0] = 'tempo'
    return redirect(url_for('orpheus', _anchor = "services"))

@app.route("/orpheus/valence")
def valencechoice():
    GLOBAL['choice'][0] = 'valence'
    return redirect(url_for('orpheus', _anchor = "services"))



@app.route("/orpheus/player/up")
def upfeatplay():
    # Create playlist
    finallist = create_playlist()

    # Get tracks for playlist
    tracks = get_orpheus_playlist()

    # Collect attributes
    idlist = [x[14:] for x in list(tracks)]

    attributes= {
        'uri':[],
        'energy':[],
        'liveness':[],
        'tempo':[],
        'key':[],
        'valence':[]
    }
    features = requests.get("https://api.spotify.com/v1/audio-features/?ids="+ ",".join(idlist) ,headers = GLOBAL['authorization_header'])
    featurelist = json.loads(features.text)['audio_features']
    featurelist = filter(lambda x: x!=None, featurelist)
    for i in range(0,len(featurelist)):
        attributes['uri'].append(str(featurelist[i]['uri']))
        attributes['energy'].append(float(featurelist[i]['energy']))
        attributes['liveness'].append(float(featurelist[i]['liveness']))
        attributes['tempo'].append(float(featurelist[i]['tempo']))
        attributes['key'].append(str(featurelist[i]['key']))
        attributes['valence'].append(float(featurelist[i]['valence']))
    df_att = pd.DataFrame.from_dict(attributes)
    b = df_att.sort_values(GLOBAL['choice'][0])
    data = json.dumps({'uris': list(b.uri)})

    playlist_api_endpoint = "https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(LogInfo['username'], LogInfo['playlist'])
    playlists_songs = requests.put(playlist_api_endpoint, data, headers=GLOBAL['authorization_header'])

    sleep(1)
    src = "https://embed.spotify.com/?uri=spotify%3Auser%3A{}%3Aplaylist%3A{}&theme=white".format(LogInfo['username'], LogInfo['playlist'])
    return render_template("player.html", src = src, display = finallist, choice = GLOBAL['choice'][0].capitalize(), playertype = "Ascending")
@app.route("/orpheus/player/down")
def downfeatplay():
    # Create playlist
    finallist = create_playlist()

    # Get tracks for playlist
    tracks = get_orpheus_playlist()

    # Collect attributes
    idlist = [x[14:] for x in list(tracks)]

    attributes= {
        'uri':[],
        'energy':[],
        'liveness':[],
        'tempo':[],
        'key':[],
        'valence':[]
    }
    features = requests.get("https://api.spotify.com/v1/audio-features/?ids="+ ",".join(idlist) ,headers = GLOBAL['authorization_header'])
    featurelist = json.loads(features.text)['audio_features']
    featurelist = filter(lambda x: x!=None, featurelist)
    for i in range(0,len(featurelist)):
        attributes['uri'].append(str(featurelist[i]['uri']))
        attributes['energy'].append(float(featurelist[i]['energy']))
        attributes['liveness'].append(float(featurelist[i]['liveness']))
        attributes['tempo'].append(float(featurelist[i]['tempo']))
        attributes['key'].append(str(featurelist[i]['key']))
        attributes['valence'].append(float(featurelist[i]['valence']))
    df_att = pd.DataFrame.from_dict(attributes)
    b = df_att.sort_values(GLOBAL['choice'][0], ascending = False)

    data = json.dumps({'uris': list(b.uri)})
    playlist_api_endpoint = "https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(LogInfo['username'], LogInfo['playlist'])
    playlists_songs = requests.put(playlist_api_endpoint, data, headers=GLOBAL['authorization_header'])
    Displayname_list = [Displayname['user_1'], Displayname['user_2'], Displayname['user_3'], Displayname['user_4'], Displayname['user_5'], Displayname['user_6']]
    namelist = []
    for itemname in Displayname_list:
        if not itemname.startswith('User'):
            namelist.append(itemname)
    finallist= ", ".join(namelist)
    sleep(1)
    src = "https://embed.spotify.com/?uri=spotify%3Auser%3A{}%3Aplaylist%3A{}&theme=white".format(LogInfo['username'], LogInfo['playlist'])
    return render_template("player.html", src = src, display = finallist, choice = GLOBAL['choice'][0].capitalize(),playertype = "Descending")

@app.route('/orpheus/user1', methods=['GET', 'POST'])
def search1():
    if request.method == 'POST':
        PLAYLIST['list1'] = []
        username = request.form['Username']
        playlists = requests.get("https://api.spotify.com/v1/users/{}/playlists".format(username),headers = GLOBAL['authorization_header'])
        textplaylists = json.loads(playlists.text)
        profileget = requests.get("https://api.spotify.com/v1/users/{}".format(username))
        profiletext = json.loads(profileget.text)
        Displayname['user_1'] = str(profiletext['display_name'])
        IMAGES['user_1'] = profiletext['images'][0]['url']
        for i in range(0,len(textplaylists['items'])):
            USER['user_1'].append(str(textplaylists['items'][i]['id']))
        for j in USER['user_1']:
            songs = requests.get("https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(username, j),headers = GLOBAL['authorization_header'])
            textsongs = json.loads(songs.text)
            if not 'items' in textsongs:
                continue
            for k in range(0,len(textsongs['items'])):
                PLAYLIST['list1'].append(str(textsongs['items'][k]['track']['uri']))
        return redirect(url_for('orpheus', _anchor = "accounts"))
    return render_template("playlist.html", search = 1)

@app.route('/orpheus/user2', methods=['GET', 'POST'])
def search2():
    if request.method == 'POST':
        PLAYLIST['list2'] = []
        username = request.form['Username']
        playlists = requests.get("https://api.spotify.com/v1/users/{}/playlists".format(username),headers = GLOBAL['authorization_header'])
        textplaylists = json.loads(playlists.text)
        profileget = requests.get("https://api.spotify.com/v1/users/{}".format(username))
        profiletext = json.loads(profileget.text)
        Displayname['user_2'] = str(profiletext['display_name'])
        IMAGES['user_2'] = profiletext['images'][0]['url']
        for i in range(0,len(textplaylists['items'])):
            USER['user_2'].append(str(textplaylists['items'][i]['id']))
        for j in USER['user_2']:
            songs = requests.get("https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(username, j),headers = GLOBAL['authorization_header'])
            textsongs = json.loads(songs.text)
            if not 'items' in textsongs:
                continue
            for k in range(0,len(textsongs['items'])):
                PLAYLIST['list2'].append(str(textsongs['items'][k]['track']['uri']))
        return redirect(url_for('orpheus', _anchor = "accounts"))
    return render_template("playlist.html", search = 2)

@app.route('/orpheus/user3', methods=['GET', 'POST'])
def search3():
    if request.method == 'POST':
        PLAYLIST['list3'] = []
        username = request.form['Username']
        playlists = requests.get("https://api.spotify.com/v1/users/{}/playlists".format(username),headers = GLOBAL['authorization_header'])
        textplaylists = json.loads(playlists.text)
        profileget = requests.get("https://api.spotify.com/v1/users/{}".format(username))
        profiletext = json.loads(profileget.text)
        Displayname['user_3'] = str(profiletext['display_name'])
        IMAGES['user_3'] = profiletext['images'][0]['url']
        for i in range(0,len(textplaylists['items'])):
            USER['user_3'].append(str(textplaylists['items'][i]['id']))
        for j in USER['user_3']:
            songs = requests.get("https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(username, j),headers = GLOBAL['authorization_header'])
            textsongs = json.loads(songs.text)
            if not 'items' in textsongs:
                continue
            for k in range(0,len(textsongs['items'])):
                PLAYLIST['list3'].append(str(textsongs['items'][k]['track']['uri']))
        return redirect(url_for('orpheus', _anchor = "accounts"))
    return render_template("playlist.html", search = 3)

@app.route('/orpheus/user4', methods=['GET', 'POST'])
def search4():
    if request.method == 'POST':
        PLAYLIST['list4'] = []
        username = request.form['Username']
        playlists = requests.get("https://api.spotify.com/v1/users/{}/playlists".format(username),headers = GLOBAL['authorization_header'])
        textplaylists = json.loads(playlists.text)
        profileget = requests.get("https://api.spotify.com/v1/users/{}".format(username))
        profiletext = json.loads(profileget.text)
        Displayname['user_4'] = str(profiletext['display_name'])
        IMAGES['user_4'] = profiletext['images'][0]['url']
        for i in range(0,len(textplaylists['items'])):
            USER['user_4'].append(str(textplaylists['items'][i]['id']))
        for j in USER['user_4']:
            songs = requests.get("https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(username, j),headers = GLOBAL['authorization_header'])
            textsongs = json.loads(songs.text)
            if not 'items' in textsongs:
                continue
            for k in range(0,len(textsongs['items'])):
                PLAYLIST['list4'].append(str(textsongs['items'][k]['track']['uri']))
        return redirect(url_for('orpheus', _anchor = "accounts"))
    return render_template("playlist.html", search = 4)

@app.route('/orpheus/user5', methods=['GET', 'POST'])
def search5():
    if request.method == 'POST':
        PLAYLIST['list5'] = []
        username = request.form['Username']
        playlists = requests.get("https://api.spotify.com/v1/users/{}/playlists".format(username),headers = GLOBAL['authorization_header'])
        textplaylists = json.loads(playlists.text)
        profileget = requests.get("https://api.spotify.com/v1/users/{}".format(username))
        profiletext = json.loads(profileget.text)
        Displayname['user_5'] = str(profiletext['display_name'])
        IMAGES['user_5'] = profiletext['images'][0]['url']
        for i in range(0,len(textplaylists['items'])):
            USER['user_5'].append(str(textplaylists['items'][i]['id']))
        for j in USER['user_5']:
            songs = requests.get("https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(username, j),headers = GLOBAL['authorization_header'])
            textsongs = json.loads(songs.text)
            if not 'items' in textsongs:
                continue
            for k in range(0,len(textsongs['items'])):
                PLAYLIST['list5'].append(str(textsongs['items'][k]['track']['uri']))
        return redirect(url_for('orpheus', _anchor = "accounts"))
    return render_template("playlist.html", search = 5)

@app.route('/orpheus/user6', methods=['GET', 'POST'])
def search6():
    if request.method == 'POST':
        PLAYLIST['list6'] = []
        username = request.form['Username']
        playlists = requests.get("https://api.spotify.com/v1/users/{}/playlists".format(username),headers = GLOBAL['authorization_header'])
        textplaylists = json.loads(playlists.text)
        profileget = requests.get("https://api.spotify.com/v1/users/{}".format(username))
        profiletext = json.loads(profileget.text)
        Displayname['user_6'] = str(profiletext['display_name'])
        IMAGES['user_6'] = profiletext['images'][0]['url']
        for i in range(0,len(textplaylists['items'])):
            USER['user_6'].append(str(textplaylists['items'][i]['id']))
        for j in USER['user_6']:
            songs = requests.get("https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(username, j),headers = GLOBAL['authorization_header'])
            textsongs = json.loads(songs.text)
            if not 'items' in textsongs:
                continue
            for k in range(0,len(textsongs['items'])):
                PLAYLIST['list6'].append(str(textsongs['items'][k]['track']['uri']))
        return redirect(url_for('orpheus', _anchor = "accounts"))
    return render_template("playlist.html", search = 6)






if __name__ == '__main__':
    app.run(debug=True)
