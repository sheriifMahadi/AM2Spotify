import json
from datetime import datetime

def getJsonData(jsonData):
    # Json file containing songs gotten from applemusic account
    songs = []
    with open(jsonData) as f:
        data = json.load(f)

    for i in data:
        songs.append(f"{i['Artist']} - {i['Title']}")
    return songs


def jsonOutput(addedTracks):
    # return Json output of songs added to library with their name and ID in order to confirm 

    curr_dt = datetime.now()    
    filename = f"AddedTracks-{curr_dt.hour}:{curr_dt.minute}:{curr_dt.second}.json"
    with open(filename, "w") as final:
        json.dump(addedTracks, final)

def getArtist(jsonData):
    artists = set()
    with open(jsonData) as f:
        data = json.load(f)
    for i in data:
        try:
            artists.add(f"{i['Album Artist']}")
        except KeyError:
            pass
        artists.add(f"{i['Sort Artist']}")
    return artists

def readPlaylist(jsonData):
    pass