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
    'user_1': "",
    'user_2': "",
    'user_3': "",
    'user_4': "",
    'user_5': "",
    'user_6': "",
}


app = Flask(__name__)

#  Client Keys
CLIENT_ID = "35a534a9bf1c446c9d9b0c6acd7f9aac"
CLIENT_SECRET = "f26b4a6600de46419e98d45bc9b939fe"

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)


# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 5000
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
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
        print name
        print 'spotify ids'
        print spotify_ids
        users.append(User(name, spotify_ids))

    orpheus = Orpheus(users)
    tracks = orpheus.get_playlist(num_tracks=50)['spotify_id']
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
    data =  json.dumps({'name': 'OrpheusList'})
    newlist = requests.post("https://api.spotify.com/v1/users/{}/playlists".format(LogInfo['username']), data, headers = GLOBAL['authorization_header'])
    textnewlist = json.loads(newlist.text)
    LogInfo['playlist'] = textnewlist['id']
    return redirect("/orpheus")

@app.route("/orpheus")
def orpheus():
    return render_template("index.html")

@app.route("/orpheus/player")
def player():
    playlist_api_endpoint = "https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(LogInfo['username'], LogInfo['playlist'])
    tracks = get_orpheus_playlist()
    data = json.dumps({'uris': list(tracks)})
    playlists_songs = requests.put(playlist_api_endpoint, data, headers=GLOBAL['authorization_header'])
    src = "https://embed.spotify.com/?uri=spotify%3Auser%3A{}%3Aplaylist%3A{}&theme=white".format(LogInfo['username'], LogInfo['playlist'])
    Displayname_list = [Displayname['user_1'], Displayname['user_2'], Displayname['user_3'], Displayname['user_4'], Displayname['user_5'], Displayname['user_6']]
    namelist = []
    for itemname in Displayname_list:
        if len(itemname) > 0:
            namelist.append(itemname)
    finallist= ", ".join(namelist)    
    return render_template("player.html", src = src, display = finallist, playertype = "Default Playlist")

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
    playlist_api_endpoint = "https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(LogInfo['username'], LogInfo['playlist'])
    playlists_songs = requests.put(playlist_api_endpoint, data, headers=GLOBAL['authorization_header'])
    Displayname_list = [Displayname['user_1'], Displayname['user_2'], Displayname['user_3'], Displayname['user_4'], Displayname['user_5'], Displayname['user_6']]
    namelist = []
    for itemname in Displayname_list:
        if len(itemname) > 0:
            namelist.append(itemname)
    finallist= ", ".join(namelist) 
    sleep(1)
    src = "https://embed.spotify.com/?uri=spotify%3Auser%3A{}%3Aplaylist%3A{}&theme=white".format(LogInfo['username'], LogInfo['playlist'])
    return render_template("player.html", src = src, display = finallist, playertype = "Ascending Playlist")
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
    playlist_api_endpoint = "https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(LogInfo['username'], LogInfo['playlist'])
    playlists_songs = requests.put(playlist_api_endpoint, data, headers=GLOBAL['authorization_header'])
    Displayname_list = [Displayname['user_1'], Displayname['user_2'], Displayname['user_3'], Displayname['user_4'], Displayname['user_5'], Displayname['user_6']]
    namelist = []
    for itemname in Displayname_list:
        if len(itemname) > 0:
            namelist.append(itemname)
    finallist= ", ".join(namelist)     
    sleep(1)
    src = "https://embed.spotify.com/?uri=spotify%3Auser%3A{}%3Aplaylist%3A{}&theme=white".format(LogInfo['username'], LogInfo['playlist'])
    return render_template("player.html", src = src, display = finallist, playertype = "Descending Playlist")

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
        for i in range(0,len(textplaylists['items'])):
            print textplaylists['items'][i]['name']
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
        for i in range(0,len(textplaylists['items'])):
            print textplaylists['items'][i]['name']
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
        for i in range(0,len(textplaylists['items'])):
            print textplaylists['items'][i]['name']
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
        for i in range(0,len(textplaylists['items'])):
            print textplaylists['items'][i]['name']
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
        for i in range(0,len(textplaylists['items'])):
            print textplaylists['items'][i]['name']
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
        for i in range(0,len(textplaylists['items'])):
            print textplaylists['items'][i]['name']
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