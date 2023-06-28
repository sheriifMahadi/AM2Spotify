import base64
import json
import logging
import os
import random as rand
import string as string
import time

import requests
from dotenv import load_dotenv

from json_data import getJsonData, jsonOutput

load_dotenv()

CLIENT_ID = os.getenv("Client_ID")
CLIENT_SECRET = os.getenv("Client_Secret")
REDIRECT_URI = os.getenv("redirect_uri")
SCOPE =  os.getenv("scope")

encoded_credentials = base64.b64encode(CLIENT_ID.encode() + b':' + CLIENT_SECRET.encode()).decode("utf-8")

AUTH_URL = "https://accounts.spotify.com/"
BASEURL = "https://api.spotify.com"

UPLOAD_PATH = os.path.join(os.getcwd(), 'files')
if not os.path.isdir(UPLOAD_PATH):
	os.mkdir(UPLOAD_PATH)

def createStateKey(size):
		return ''.join(rand.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(size))

def fileName(session, file, action_type):
	# function to return file name 
	# or generate name for file uploaded

	curr = session.get('current_user')
	if curr != None:
		curr = curr.get('display_name') # append logged in user name to file

		if action_type == 'setname': # check action type to return name or generate name
			file.filename = 'tracks.json'
			filename = (f"{curr}: {''.join(file.filename)}")
			return filename
		elif action_type == 'getname':
			filename = (f"files/{curr}_tracks.json")
			return filename if os.path.exists(filename) else "None"
		else:
			return None
	else:
		return None

def tokenHeadersData(code):
	token_headers = {
		"Authorization": "Basic " + encoded_credentials,
		'Accept': 'application/json',
		"Content-Type": "application/x-www-form-urlencoded"
	}

	token_data = {
		"grant_type": "authorization_code",
		"code": code,
		"redirect_uri": REDIRECT_URI
	}

	result = requests.post(f"{AUTH_URL}api/token", data=token_data, headers=token_headers)

	try: 
		json = result.json()
		return json["access_token"], json['refresh_token'], json['expires_in']
	except KeyError as err:
		logging.error('getToken:' + str(result.status_code))
		return None

def refreshToken(refresh):
	# Refresh access token from spotify
	response = requests.post(f"{AUTH_URL}api/token",
								data={"grant_type": "refresh_token",
									"refresh_token": refresh},
								headers={"Authorization": "Basic " + encoded_credentials})

	json = response.json()
	try: 
		return json['access_token'], json['expires_in']
	except KeyError as err:
		logging.error('refreshToken')
		return None

def checkTokenStatus(session):
	# Check token expiration and generate a new access token
	if time.time() > session['token_expiration']:
		token = refreshToken(session['refresh_token'])
		if token != None:
			session['access_token'] = token[0]
			session['token_expiration'] = time.time() + token[1]
		else:
			logging.error('checkTokenStatus')
			return None

	return "token refreshed"

def getRequest(session, url, params={}):
	# Make request to spotify endpoints
	headers = {
		'Accept': 'application/json',
		'Content-Type': 'application/json',
		'Authorization': 'Bearer ' + session['access_token']
	}
	response = requests.get(url, headers=headers, params=params)
	if response.status_code == 200:
		return response.json()
	elif response.status_code == 401 and checkTokenStatus(session) != None:
		return getRequest(session, url, params)
	else:
		logging.error('getRequest failed from function getRequest ' + str(response.status_code))
		return None

def postRequest(session, url, data):
	headers = {
		'Accept': 'application/json',
		'Content-Type': 'application/json',
		'Authorization': 'Bearer ' + session['access_token']
	}
	response = requests.post(url, headers=headers, data=data)
	if response.status_code == 201: # response 201 has information body while 204 is empty
		return response.json()
	if response.status_code == 204:
		return response

	# if a 401 error occurs, update the access token
	elif response.status_code == 401 and checkTokenStatus(session) != None:
		return postRequest(session, url, data)
	elif response.status_code == 403 or response.status_code == 404:
		return response.status_code
	else:
		logging.error (f"postRequest failed from function postRequest {str(response.status_code)}")
		return None

def deleteRequest(session, url):
	headers = {
		'Accept': 'application/json',
		'Content-Type': 'application/json',
		'Authorization': 'Bearer ' + session['access_token']
	}	
	response = requests.delete(url, headers=headers)

	if response.status_code == 200:
		return '200'

	# if a 401 error occurs, update the access token
	elif response.status_code == 401 and checkTokenStatus(session) != None:
		return deleteRequest(session, url)
	else:
		logging.error('DeleteRequest failed from function deleteRequest' + str(response.status_code))
		return None

def getCurrentUser(session):
	url = f"{BASEURL}/v1/me"
	# url = 'https://api.spotify.com/v1/me'
	data = getRequest(session, url)
	if data == None:
		return None

	return data

def addToLibrary(session, tracks):
	# Check token Status function
	tracksId = ','.join(tracks) # Join ids from list into comma separated string and call addToLibrary method
	if tracksId == None or len(tracksId) == 0:
		return None
	
	# headers = {
	# 	'Accept': 'application/json',
	# 	'Content-Type': 'application/json',
	# 	'Authorization': 'Bearer ' + session['access_token']
	# }
	# params = {
	# 	'ids': tracksId, # String of ids separated by comma
	# }

	# response = requests.put(f'{BASEURL}/v1/me/tracks', params=params, headers=headers)
	# if response:
	# 	if response.status_code == 200:
	# 		return '200'
	# 	else:
	# 		return None
	create = createPlaylist(session)
	if create != None:
		url = f'{BASEURL}/v1/playlists/{create}/tracks'
	uri_list = []
	added = []
	for uri in tracks:
		uri_list.append(f'spotify:track:{uri}')

	while len(tracks) > 0:
		print(uri_list)
		data = {"uris": uri_list[:99]}
		json_object = json.dumps(data)
		added.append(uri_list[:99])
		del uri_list[:99]
		response = postRequest(session, url, json_object)
		if len(uri_list) <= 0:
			if response != None and response['snapshot_id']:
				return '200'
			else: 
				return None

def searchForSongs(session, uploadedJson):
	url = f'{BASEURL}/v1/search'
	try:
		songs = getJsonData(uploadedJson)
	except FileNotFoundError as e:
		logging.error(e)
		songs = []
	
	tracks = []
	tracksId = ""
	#  Search from songs from Json file and add to library
	for song in songs: # Looping Json file
		params = { # Search params taken from json file
			'q': song,
			'type': 'track',
			'limit': '1',
		}
		data = getRequest(session, url, params)
		if data == None:
			return None
		for track in data['tracks']['items']:
			tracks.append(track['id'])
	return tracks


def extractNameArtists(data):
	artists = []
	songItems= []
	for track in data['items']:
		artists.append((track['artists']))

	x = [name['name'] for name in data['items']]
	mapped = zip(x, artists)

	for i, j in list(mapped):
		songDetails = {}
		songDetails['name'] = i
		songDetails['artists'] = j
		songItems.append(songDetails)
	for i in songItems:
		song_title = i['name']
		song_artists = [artist['name'] for artist in i['artists']]
		x.append(f'{song_title} - {", ".join(song_artists)} ')
	return x

def getTopTracks(session, type, time_range):
	track_id = []

	url = f'{BASEURL}/v1/me/top/{type}?time_range={time_range}&limit=5'
	data = getRequest(session, url)
	if data == None:
		return None
	
	for track in data['items']:
		track_id.append(track['id'])

	return track_id	

def getTopArtists(session, type, time_range):
	artists = []

	url = f'{BASEURL}/v1/me/top/{type}?time_range={time_range}&limit=5'
	data = getRequest(session, url)
	if data == None:
		return None
	
	for artist in data['items']:
		artists.append(artist['id'])
	return artists

def getCurrentlyPlaying(session):
	url = f'{BASEURL}/v1/me/player/currently-playing'
	data = getRequest(session, url)
	if data == None:
		return None
	return data.get('item').get('id')

def getSavedTracks(session):
	url = f'{BASEURL}/v1/me/tracks?limit=50'
	tracks = []
	while True:
		print(url)
		data = getRequest(session, url)
		if data == None:
			return None
		for items in data['items']:
			if items.get('track') != None:
				tracks.append(items.get('track').get('id'))
		if data['next']:
			url = data['next']
		else:
			return tracks
		
def getUserPlaylists(session):
	playlists = []
	url = f'{BASEURL}/v1/me/playlists'
	data = getRequest(session, url)
	if data == None:
		return None
	for items in data['items']:
		playlistdetails = {}
		playlistdetails['name'] =  "".join(items.get('name').split())
		playlistdetails['id'] = items.get('id')
		playlistdetails['snapshotId'] = items.get('snapshot_id')

		try:
			playlistdetails['cover'] = items.get('images')[0]
		except IndexError as e:	
			playlistdetails['cover'] = items.get('images')
		playlists.append(playlistdetails)
	return playlists

def getPlaylistItems(session):
	playlistsItems = []
	url = f'{BASEURL}/v1/playlists/{session["sourceId"]}/tracks'
	
	while True:
		data = getRequest(session, url)
		if data == None:
			return None
		for items in data['items']:
			playlistsItems.append(items['track']['id'])
		if data['next']:
			url = data['next']
		else:
			return playlistsItems

def addToPlaylist(session, data):
	url = f'{BASEURL}/v1/playlists/{session["targetId"]}/tracks'
	uri_list = []
	added = []
	for uri in data:
		uri_list.append(f'spotify:track:{uri}')
	while len(uri_list) > 0:
		data = {"uris": uri_list[:99]}
		json_object = json.dumps(data)
		added.append(uri_list[:99])
		del uri_list[:99]

		response = postRequest(session, url, json_object)
		if len(uri_list) <= 0:
			if response != None and response['snapshot_id']:
				return '200'
			else: 
				return None


def deletePlaylist(session, data):
	url = f'{BASEURL}/v1/users/'
	response = deleteRequest(session, url)
	return response

def createPlaylist(session):
	url = f'{BASEURL}/v1/users/{session["current_user"]["id"]}/playlists'
	data = {
		'name': 'Apple music songs',
		'description': 'Songs imported from apple music library',
		'public': False,
	}
	json_object = json.dumps(data)

	response = postRequest(session, url, json_object)
	if response != None and response['name']:
			return response['id']
	else: 
		return None

def playListAction(action, session, ids):
	Errormsg = 'An error occured. Please make a selection and try again.'

	if action == 'copy':
		addedToPlaylist = addToPlaylist(session, ids)
		if addedToPlaylist == '200':
			return {'msg': 'copy success'}
		else: 
			return {"error": Errormsg} 

	elif action == 'move':
		addedToPlaylist = addToPlaylist(session, ids)
		if addedToPlaylist == '200':
			deletedItem = deletePlaylist(session, ids)
			if deletedItem == 200:
				return {'msg': 'move success'}
			else:
				return {'msg': 'move failed'}
		else: 
			return {"error": Errormsg} 

