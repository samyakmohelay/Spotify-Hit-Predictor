import joblib
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import pandas as pd
import os

# import sys
# sys.path.append("C:/Users/samya/VS Code Projects/Python/Python Projects/Spotify_hit_predictor/backend/secret_key.py")
import secret_key

def hit_flop(track, artist):

    # Load keys
    load_dotenv()
    client_id = os.getenv(secret_key.client_id)
    client_secret = os.getenv(secret_key.secret)   

    # Transform strings to lower case
    track = track.lower()
    artist = artist.lower()

    # Call song
    
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=secret_key.client_id, client_secret=secret_key.secret))
    
    try:
        results = spotify.search(q='track:' + track, type='track')
        # Find song uri by matching artist
        items = results['tracks']['items']
        for i in items:
            item_artist = i['artists'][0]['name']
            if item_artist.lower() == artist:
                uri = i['uri']

        # Setting information from audio analysis
        audio_analysis = spotify.audio_analysis(track_id=uri)
        count_sections = len(audio_analysis['sections'])
        chorus_hit = audio_analysis['sections'][2]['start']
        
        # Setting information from audio features
        audio_features = spotify.audio_features(tracks=[uri])
        f = audio_features[0]

        # Arrange data to load to model
        x = [[f['danceability'],
            f['energy'],
            f['key'],
            f['loudness'],
            f['mode'],
            f['speechiness'],
            f['acousticness'],
            f['instrumentalness'],
            f['liveness'],
            f['valence'],
            f['tempo'],
            f['duration_ms'],
            f['time_signature'],
            chorus_hit,
            count_sections]]
        
        # Arrange data to fill dictionary for DataFrame
        key = ''      
        if f['key'] == 1:
            key = 'Major'
        else:
            key = 'Minor'

        mode = ''
        pitch_class = {-1:'No key was detected',
            0:'C',
            1:'C♯ or D♭',
            2:'D',
            3:'D♯ or E♭',
            4:'E',
            5:'F',
            6:'F♯ or G♭',
            7:'G',
            8:'G♯ or A♭',
            9:'A',
            10:'A♯ or B♭',
            11:'B'}
        if f['mode'] in pitch_class:
            mode = pitch_class[f['mode']]
    

        # Create DataFrame of data
        table = pd.DataFrame({
            'Danceability': [f['danceability']],
            'Energy': [f['energy']],
            'Key': [key],
            'Loudness (db)': [f['loudness']],
            'Mode': [mode],
            'Speechiness': [f['speechiness']],
            'Acousticness': [f['acousticness']],
            'Instrumentalness': [f['instrumentalness']],
            'Liveness': [f['liveness']],
            'Valence': [f['valence']],
            'Tempo (beats per minute (BPM))': [f['tempo']],
            'Duration (seconds)': [f['duration_ms']/1000],
            'Time Signature': [f['time_signature']],
            'Aprox timestamp the chorus "hit" (seconds)': [chorus_hit],
            'Sections count': [count_sections]
            })
        ttable = table.T
        feature_table = ttable.to_html(classes="table table-hover table-success table-striped", 
            justify='center',
            header=False)
 
    except:
        error = "We can't find your entry in the spotify database, please check your spelling and/or try again"
        return [error]
    
    try:
        # Load model
        model = joblib.load('model.sav')
        scaler = joblib.load('scaler.sav')

        # Scaling data
        x_scaled = scaler.transform(x)
        
        # Running model
        hit_predict = model.predict(x_scaled)
        hit_score = model.predict_proba(x_scaled)

        return [hit_predict, hit_score, feature_table]
    
    except:
        error_model = "Model error"
        return [error_model]