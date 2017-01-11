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

app = Flask(__name__)

#  Client Keys
# James
CLIENT_ID = "35a534a9bf1c446c9d9b0c6acd7f9aac"
CLIENT_SECRET = "f26b4a6600de46419e98d45bc9b939fe"
# Oamar (for testing purpose only)
CLIENT_ID = "6fd8426e0d5842c8a71f5fb2fe500755"
CLIENT_SECRET = "c8dd889c094b47f99e89ae221a29df9b"


# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)


# Server-side Parameters
#CLIENT_SIDE_URL = "http://127.0.0.1"
#CLIENT_SIDE_URL = "http://3rdworldjuander.pythonanywhere.com"
CLIENT_SIDE_URL = "http://myorpheus.servemp3.com"
#PORT = 5000
#REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
REDIRECT_URI = "{}/callback/q".format(CLIENT_SIDE_URL)
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
    for name, spotify_ids in USER.iteritems():
        users.append(User(name, spotify_ids))

    orpheus = Orpheus(users)
    return orpheus.get_playlist(num_tracks=50)['spotify_id']


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



    return redirect("/orpheus")

@app.route("/orpheus")
def orpheus():
    return render_template("index.html")

@app.route("/orpheus/player")
def player():
    playlist_api_endpoint = "https://api.spotify.com/v1/users/1217498016/playlists/3Fafmpj0dxo6SIF3w8wVNR/tracks"
    tracks = get_orpheus_playlist()
    data = json.dumps({'uris': list(tracks)})
    playlists_songs = requests.put(playlist_api_endpoint, data, headers=GLOBAL['authorization_header'])
    return render_template("player.html")

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
    tracks = get_orpheus_playlist()
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
    for i in range(0,len(featurelist)):
        attributes['uri'].append(str(featurelist[i]['uri']))
        attributes['energy'].append(float(featurelist[i]['energy']))
        attributes['liveness'].append(float(featurelist[i]['liveness']))
        attributes['tempo'].append(float(featurelist[i]['tempo']))
        attributes['key'].append(str(featurelist[i]['key']))
        attributes['valence'].append(float(featurelist[i]['valence']))

    df_att = pd.DataFrame.from_dict(attributes)
    print df_att
    b = df_att.sort_values(GLOBAL['choice'][0])
    print b
    data = json.dumps({'uris': list(b.uri)})
    playlist_api_endpoint = "https://api.spotify.com/v1/users/1217498016/playlists/3Fafmpj0dxo6SIF3w8wVNR/tracks"
    playlists_songs = requests.put(playlist_api_endpoint, data, headers=GLOBAL['authorization_header'])
    sleep(1)
    return render_template("player.html")

@app.route("/orpheus/player/down")
def downfeatplay():
    tracks = get_orpheus_playlist()
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
    for i in range(0,len(featurelist)):
        attributes['uri'].append(str(featurelist[i]['uri']))
        attributes['energy'].append(float(featurelist[i]['energy']))
        attributes['liveness'].append(float(featurelist[i]['liveness']))
        attributes['tempo'].append(float(featurelist[i]['tempo']))
        attributes['key'].append(str(featurelist[i]['key']))
        attributes['valence'].append(float(featurelist[i]['valence']))

    df_att = pd.DataFrame.from_dict(attributes)
    print df_att
    b = df_att.sort_values(GLOBAL['choice'][0], ascending = False)
    print b

    data = json.dumps({'uris': list(b.uri)})
    playlist_api_endpoint = "https://api.spotify.com/v1/users/1217498016/playlists/3Fafmpj0dxo6SIF3w8wVNR/tracks"
    playlists_songs = requests.put(playlist_api_endpoint, data, headers=GLOBAL['authorization_header'])
    sleep(1)   
    return render_template("player.html")

@app.route('/orpheus/user1', methods=['GET', 'POST'])
def search1():
    if request.method == 'POST':
        PLAYLIST['list1'] = []  
        username = request.form['Username']
        playlists = requests.get("https://api.spotify.com/v1/users/{}/playlists".format(username),headers = GLOBAL['authorization_header'])
        textplaylists = json.loads(playlists.text)      
        if not 'items' in textplaylists:
            continue
        for i in range(0,len(textplaylists['items'])):
            USER['user_1'].append(str(textplaylists['items'][i]['id']))
        for j in USER['user_1']:
            songs = requests.get("https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(username, j),headers = GLOBAL['authorization_header'])
            textsongs = json.loads(songs.text)
            if not 'items' in textsongs:
                continue
            for k in range(0,len(textsongs['items'])):
                PLAYLIST['list1'].append(str(textsongs['items'][k]['track']['uri']))
        print USER['user_1']
        print PLAYLIST['list1']
        return redirect(url_for('orpheus', _anchor = "accounts"))

         
    return render_template("playlist.html")

@app.route('/orpheus/user2', methods=['GET', 'POST'])
def search2():
    if request.method == 'POST':
        PLAYLIST['list2'] = []  
        username = request.form['Username']
        playlists = requests.get("https://api.spotify.com/v1/users/{}/playlists".format(username),headers = GLOBAL['authorization_header'])
        textplaylists = json.loads(playlists.text)['items']
        for i in range(0,len(textplaylists)):
            USER['user_2'].append(str(textplaylists[i]['id']))
        for j in USER['user_2']:
            songs = requests.get("https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(username, j),headers = GLOBAL['authorization_header'])
            textsongs = json.loads(songs.text)['items']
            for k in range(0,len(textsongs)):
                PLAYLIST['list2'].append(str(textsongs[k]['track']['uri']))
        print USER['user_2']
        print PLAYLIST['list2']
        return redirect(url_for('orpheus', _anchor ="accounts"))

         
    return render_template("playlist.html")

@app.route('/orpheus/user3', methods=['GET', 'POST'])
def search3():
    if request.method == 'POST':
        PLAYLIST['list3'] = []  
        username = request.form['Username']
        playlists = requests.get("https://api.spotify.com/v1/users/{}/playlists".format(username),headers = GLOBAL['authorization_header'])
        textplaylists = json.loads(playlists.text)['items']
        for i in range(0,len(textplaylists)):
            USER['user_3'].append(str(textplaylists[i]['id']))
        for j in USER['user_3']:
            songs = requests.get("https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(username, j),headers = GLOBAL['authorization_header'])
            textsongs = json.loads(songs.text)['items']
            for k in range(0,len(textsongs)):
                PLAYLIST['list3'].append(str(textsongs[k]['track']['uri']))
        print USER['user_3']
        print PLAYLIST['list3']
        return redirect(url_for('orpheus', _anchor ="accounts"))

         
    return render_template("playlist.html")

@app.route('/orpheus/user4', methods=['GET', 'POST'])
def search4():
    if request.method == 'POST':
        PLAYLIST['list4'] = []  
        username = request.form['Username']
        playlists = requests.get("https://api.spotify.com/v1/users/{}/playlists".format(username),headers = GLOBAL['authorization_header'])
        textplaylists = json.loads(playlists.text)['items']
        for i in range(0,len(textplaylists)):
            USER['user_4'].append(str(textplaylists[i]['id']))
        for j in USER['user_4']:
            songs = requests.get("https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(username, j),headers = GLOBAL['authorization_header'])
            textsongs = json.loads(songs.text)['items']
            for k in range(0,len(textsongs)):
                PLAYLIST['list4'].append(str(textsongs[k]['track']['uri']))
        print USER['user_4']
        print PLAYLIST['list4']
        return redirect(url_for('orpheus', _anchor ="accounts"))

         
    return render_template("playlist.html")

@app.route('/orpheus/user5', methods=['GET', 'POST'])
def search5():
    if request.method == 'POST':
        PLAYLIST['list5'] = []  
        username = request.form['Username']
        playlists = requests.get("https://api.spotify.com/v1/users/{}/playlists".format(username),headers = GLOBAL['authorization_header'])
        textplaylists = json.loads(playlists.text)['items']
        for i in range(0,len(textplaylists)):
            USER['user_5'].append(str(textplaylists[i]['id']))
        for j in USER['user_5']:
            songs = requests.get("https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(username, j),headers = GLOBAL['authorization_header'])
            textsongs = json.loads(songs.text)['items']
            for k in range(0,len(textsongs)):
                PLAYLIST['list5'].append(str(textsongs[k]['track']['uri']))
        print USER['user_5']
        print PLAYLIST['list5']
        return redirect(url_for('orpheus', _anchor ="accounts"))

         
    return render_template("playlist.html")

@app.route('/orpheus/user6', methods=['GET', 'POST'])
def search6():
    if request.method == 'POST':
        PLAYLIST['list6'] = []  
        username = request.form['Username']
        playlists = requests.get("https://api.spotify.com/v1/users/{}/playlists".format(username),headers = GLOBAL['authorization_header'])
        textplaylists = json.loads(playlists.text)['items']
        for i in range(0,len(textplaylists)):
            USER['user_6'].append(str(textplaylists[i]['id']))
        for j in USER['user_6']:
            songs = requests.get("https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(username, j),headers = GLOBAL['authorization_header'])
            textsongs = json.loads(songs.text)['items']
            for k in range(0,len(textsongs)):
                PLAYLIST['list6'].append(str(textsongs[k]['track']['uri']))
        print USER['user_6']
        print PLAYLIST['list6']
        return redirect(url_for('orpheus', _anchor ="accounts"))

         
    return render_template("playlist.html")






if __name__ == '__main__':
    app.run(debug=True)
