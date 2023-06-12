from flask import Flask
import views
import os

SECRET_KEY = os.getenv("secret_key")


app = Flask(__name__)
app.add_url_rule('/', view_func=views.index)
app.add_url_rule('/import', view_func=views.importSongs, methods=['GET'])
app.add_url_rule('/upload', view_func=views.uploadFile, methods=['POST'])
app.add_url_rule('/import', view_func=views.uploadtoSpotify, methods=['POST'])

app.add_url_rule('/playlists', view_func=views.playlists, methods=['GET', 'POST'])
app.add_url_rule('/tutorial', view_func=views.tutorial)

app.add_url_rule('/login', view_func=views.login)
app.add_url_rule('/logout', view_func=views.logout)
app.add_url_rule('/authorize', view_func=views.authorize)
app.add_url_rule('/callback', view_func=views.callback)

app.secret_key=SECRET_KEY

if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
