import base64
import logging
import os
import random as rand
import string as string
import time
import requests
from json_data import getJsonData, jsonOutput

from dotenv import load_dotenv
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
	query = "https://accounts.spotify.com/api/token"

	response = requests.post(query,
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
		logging.error('getRequest failed from function getRequest' + str(response.status_code))
		return None

def getCurrentUser(session):
	url = 'https://api.spotify.com/v1/me'
	data = getRequest(session, url)
	if data == None:
		return None

	return data

def addToLibrary(session, tracks):
	# Check token Status function
	tracksId = ','.join(tracks) # Join ids from list into comma separated string and call addToLibrary method
	if tracksId == None or len(tracksId) == 0:
		return None
	
	headers = {
		'Accept': 'application/json',
		'Content-Type': 'application/json',
		'Authorization': 'Bearer ' + session['access_token']
	}
	params = {
		'ids': tracksId, # String of ids separated by comma
	}

	response = requests.put(f'{BASEURL}/v1/me/tracks', params=params, headers=headers)
	if response.status_code == 200:
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
	for song in songs[10:13]: # Looping Json file
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

	url = f'https://api.spotify.com/v1/me/top/{type}?time_range={time_range}&limit=5'
	data = getRequest(session, url)
	if data == None:
		return None
	
	for track in data['items']:
		track_id.append(track['id'])

	return track_id	

def getTopArtists(session, type, time_range):
	artists = []

	url = f'https://api.spotify.com/v1/me/top/{type}?time_range={time_range}&limit=5'
	data = getRequest(session, url)
	if data == None:
		return None
	
	for artist in data['items']:
		artists.append(artist['id'])
	return artists

def getCurrentlyPlaying(session):
	url = 'https://api.spotify.com/v1/me/player/currently-playing'
	data = getRequest(session, url)
	if data == None:
		return None
	return data.get('item').get('id')

def transferPlaylist(self):
	# read apple playlist xml file and add playlist to spotify
	pass



