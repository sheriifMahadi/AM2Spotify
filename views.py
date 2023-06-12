import sys

sys.path.append('..')
import functools
import time
from urllib.parse import urlencode
import os
from werkzeug.utils import secure_filename
from Applemusic_Spotify.json_data import getJsonData
from flask import (make_response, redirect, render_template, request, session,
                   url_for, flash)

from util import (UPLOAD_PATH, AUTH_URL, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPE, checkTokenStatus,
                  createStateKey, fileName, getCurrentUser, getCurrentlyPlaying, getTopTracks, getTopArtists, refreshToken,
                  tokenHeadersData, searchForSongs, addToLibrary, fileName)


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('logged_in') == False or session.get('logged_in') == None:
            return redirect(url_for('login'))
        return view(**kwargs)

    return wrapped_view

def check_login_status(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('logged_in') == True:
            return redirect(url_for('index'))
        return view(**kwargs)

    return wrapped_view

@login_required
def index():
	topArtistsShort = getTopArtists(session, 'artists', 'short_term')
	topArtistsMid = getTopArtists(session, 'artists', 'medium_term')
	topArtistsLong = getTopArtists(session, 'artists', 'long_term')

	topTracksShort = getTopTracks(session, 'tracks', 'short_term')
	topTracksMid = getTopTracks(session, 'tracks', 'medium_term')
	topTracksLong = getTopTracks(session, 'tracks', 'long_term')

	currentlyPlaying = getCurrentlyPlaying(session)

	return render_template('index.html', 
						topArtistsShort=topArtistsShort,
						topArtistsMid=topArtistsMid,
						topArtistsLong=topArtistsLong,
						topTracksShort=topTracksShort,
						topTracksMid=topTracksMid,
						topTracksLong=topTracksLong,
						currentlyPlaying=currentlyPlaying)

@login_required
def uploadFile():
	if request.method == 'POST' and 'file' in request.files:
		file = request.files['file']
		filename = secure_filename(fileName(session, file, 'setname'))
		if filename != None:
			file.save(os.path.join(UPLOAD_PATH, filename))
			return {"message": "File uploaded successfuly."}

@login_required
def uploadtoSpotify():
	ids = request.form.getlist('tracks')
	addedTracks = addToLibrary(session, ids)
	if addedTracks == '200':
		flash(f'{len(ids)} tracks have been added to library.')
		return redirect(url_for('index'))
	else: 
		return render_template('error.html', 
		error='Error adding songs to library. Please make a selection and try again')

@login_required
def importSongs():
	filename = fileName(session, 'file', 'getname')
	songs = searchForSongs(session, filename)
	if filename != "None":
		session['fileuploaded'] = True
	else:
		try:
			session.pop('fileuploaded')
		except:
			pass
	return render_template('importSongs.html', songs=songs)

@login_required
def playlists():
	return render_template('playlists.html')

def tutorial():
	topTracksShort = getTopTracks(session, 'tracks', 'short_term')
	return render_template('tutorial.html', getTopTracks=topTracksShort)

@check_login_status
def login():
	return render_template('login.html', auth_url=url_for('authorize'))

def logout():
    session.clear()
    return redirect(url_for('login'))


@check_login_status
def authorize():
	auth_headers = {
		"client_id": CLIENT_ID,
		"response_type": "code",
		"redirect_uri": REDIRECT_URI,
		"scope": SCOPE, 
		"show_dialog": True,
	}

	response = make_response(redirect(f"{AUTH_URL}authorize?{urlencode(auth_headers)}"))
	return response

# @check_login_status
def callback():
	if request.args.get('error'):
		session["login_failed"] = True
		session["logged_in"] = False
		return render_template('error.html', error='Spotify error.')
	else:
		session.clear()
		code = request.args.get('code')
		token = tokenHeadersData(code)
		if token != None:
			session['access_token'] = token[0]
			session['refresh_token'] = token[1]
			session['token_expiration'] = time.time() + token[2]
			session['current_user'] = getCurrentUser(session)
			session["logged_in"] = True

		else:
			session["login_failed"] = True
			session["logged_in"] = False
			return render_template('error.html', error='Failed to authenticate')

	return redirect('/')



