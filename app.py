import os
# TEMPORARY FIX - Set Spotify credentials directly
os.environ['SPOTIPY_CLIENT_ID'] = '7f1404593f0c4f23a2c6464d36deab37'
os.environ['SPOTIPY_CLIENT_SECRET'] = '029fcc7c966842cbab01b842c3942765'
os.environ['SPOTIPY_REDIRECT_URI'] = 'https://dream-app-lpo2.onrender.com/callback'
from flask import Flask, render_template, request, jsonify, session
import pandas as pd
import numpy as np
from textblob import TextBlob
import re
import random
import pygame
import time
from transformers import pipeline
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'emotional-music-companion-secret-key')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Now set your app variables to use these values
SPOTIFY_CLIENT_ID = '7f1404593f0c4f23a2c6464d36deab37'
SPOTIFY_CLIENT_SECRET = '029fcc7c966842cbab01b842c3942765'
SPOTIFY_REDIRECT_URI = 'https://dream-app-lpo2.onrender.com/callback'

# Initialize pygame mixer
try:
    pygame.mixer.init()
    logger.info("✅ Audio system initialized!")
except Exception as e:
    logger.error(f"❌ Audio system error: {e}")

# Load the emotion classifier
try:
    emotion_classifier = pipeline("text-classification", model="bhadresh-savani/distilbert-base-uncased-emotion")
    logger.info("✅ Advanced emotion classifier loaded!")
except Exception as e:
    logger.warning(f"⚠️ Could not load advanced classifier: {e}. Falling back to basic analysis.")
    emotion_classifier = None

# --- Load CSV & Define Unique Moods ---
try:
    df = pd.read_csv('songs.csv', quoting=1, on_bad_lines='skip')
    df['mood_lower'] = df['mood'].str.lower().str.strip()
    logger.info(f"✅ Loaded {len(df)} songs from CSV")
except Exception as e:
    logger.error(f"❌ Error loading CSV: {e}")
    df = pd.DataFrame()

# Folder containing all songs
folder = "songs"
files = []
if os.path.exists(folder):
    files = os.listdir(folder)
    files_lower = [f.lower() for f in files]
    logger.info(f"✅ Found {len(files)} audio files")
else:
    logger.warning(f"⚠️ Songs folder '{folder}' not found")

# --- EMOTION TO MOODS MAPPING ---
emotion_to_moods = {
    "sadness": [
        "heartbreak", "heartbreak pain", "bittersweet unrequited", "wanderer loss", "heartbreak loss", 
        "restless longing", "reflective longing", "introspection loss", "memories nostalgia", 
        "longing reunion", "hopeful longing", "rainy days", "winter bear", "lonely whale", 
        "separation pain", "trauma reflection", "melancholy loss", "introspection strange", 
        "rainy melancholy", "illusion love", "ending relationship", "guilt stigma", "hidden struggles", 
        "self-doubt", "overwork reflection", "sad instrumental"
    ],
    "joy": [
        "sweet love", "joyful romance", "joyful love", "sweet adoration", "happiness", "fun love", 
        "playful romance", "playful flirtation", "victory motivation", "girls empowerment", 
        "vibe connection", "eternal bulletproof", "youth forever", "future hope", "celebration pride", 
        "playful banter", "romantic tease", "sweet theft", "shy flirtation", "passionate dance", 
        "playful passion", "energetic flirtation", "energetic arrival", "energetic party", 
        "smooth fun", "chance dance", "boom fun", "marching band", "party call", "fun chicken", 
        "fun remix", "fun party", "fun crush", "embarrassment fun", "fun tuna", "epic motivation", 
        "fun chicken", "count fun", "thug take", "seven seas", "permission joy", "smooth fun", 
        "chance dance", "boom fun", "marching band", "party call"
    ],
    "love": [
        "dark romance", "sweet love", "college love", "romantic", "destiny love", "romantic adoration", 
        "secret love", "devotion", "obsessive love", "sweet adoration", "passion elopement", 
        "carefree love", "romantic pondering", "inexpressible adoration", "gentle romance", 
        "devotional bond", "divine jealousy", "romantic story", "devotion darling", "soothing romance", 
        "faith love", "passion monsoon", "seven births", "necessary love", "life become", 
        "valentine love", "you beloved", "with you", "that girl", "first time", "little love", 
        "friends we", "heart redefined", "allah boy", "allah girl", "picture you", "necessary female", 
        "necessary dillagi", "romantic plea", "wanderer love", "longing reunion", "playful confusion", 
        "hopeful wish", "boundless devotion", "fun love", "romantic tease", "sweet theft", 
        "shy flirtation", "passionate dance", "inexpressible adoration", "hopeful longing", 
        "playful passion", "divine jealousy", "devotion darling", "faith love", "passion monsoon", 
        "listen marble", "valentine love", "fragrance wind", "scenery beauty", "snow flower", 
        "travel coded", "memory started", "here there", "female here there", "yes no", 
        "3d dimension", "never let", "seven days", "romantic deewana", "enchanting love", 
        "hopeful day", "world's cruelty", "sweet devotion", "surrender love", "rainy pleasure", 
        "romantic eyes", "romantic kiss", "mutual deewana", "romantic happening", "marriage proposal", 
        "eyes request", "crazy heart", "searching eyes", "stealing heart", "sweet beauty", 
        "first sight magic", "first time crazy", "god plea", "dance veil", "recognize darling", 
        "romantic embrace", "god thanks", "god seen", "no memory", "heart gift", 
        "crazy heart", "Delhi girlfriend", "drum romance", "romantic reunion", "romantic deewana", 
        "romantic eyes", "romantic kiss", "mutual deewana", "romantic happening", "marriage proposal", 
        "eyes request", "crazy heart", "searching eyes", "stealing heart", "sweet beauty", 
        "first sight magic", "first time crazy", "god plea", "dance veil", "recognize darling", 
        "romantic embrace", "god thanks", "god seen", "no memory", "heart gift", "heart worship", 
        "heart says", "heart does", "pain awakened", "free heart", "crazy heart", 
        "daily love", "face to face", "true deewana", "adorn looting", "safety female", 
        "oath reprise", "god seen", "die love", "without you", "romantic story", 
        "romantic tease", "romantic pondering", "inexpressible adoration", "gentle romance", 
        "devotional bond", "playful passion", "divine jealousy", "bittersweet unrequited", 
        "union love", "searching longing", "memories nostalgia", "romantic story", "hope", 
        "alive motivation", "necessary love", "necessary dillagi", "necessary female", 
        "picture you", "yes no", "here there", "female here there", "memory started", 
        "travel coded", "snow flower", "scenery beauty", "fragrance wind", "valentine love", 
        "life become", "seven days", "never let", "3d dimension", "marching band", 
        "warning sound", "wake up", "vibe connection", "girls empowerment", "youth forever", 
        "future hope", "lonely whale", "wild flower", "with you", "that girl", 
        "first time", "little love", "friends we", "heart redefined", "allah boy", 
        "allah girl", "jolt strong", "eternal bulletproof", "we on"
    ],
    "anger": [
        "jolt strong", "divine jealousy", "warning sound", "resistance", "social critique", 
        "freedom rebellion", "empowering diss", "rap challenge", "rap triptych"
    ],
    "fear": [
        "introspection fear", "dark romance", "dark passion", "dark introspection"
    ],
    "surprise": [
        "playful confusion", "3d dimension", "never let", "seven days", "marching band", 
        "unknown mood", "unknown", "reel audio"
    ],
    "other": [
        "motivational", "victory motivation", "hopeful wish", "motivational aim", "alive motivation", 
        "we on", "hope", "hope new start", "wake up", "wild flower", "traditional hope", 
        "personal growth", "philosophical people", "comfort rest", "longing distance", 
        "genetic connection", "astronaut journey", "stars hope", "untamed flute", 
        "self-expression", "forward hope", "permission joy", "equality hope", 
        "come back", "self-love", "illusion love", "run forward", "stay true", 
        "love serendipity", "too much", "my time", "innocent mistakes", 
        "drama queen", "seven seas", "permission joy", "smooth fun", 
        "chance dance", "boom fun", "marching band", "party call", "fun chicken", 
        "count fun", "thug take", "seven seas", "permission joy", "smooth fun", 
        "chance dance", "boom fun", "marching band", "party call"
    ]
}

# --- EMOTIONAL SITUATIONS ---
emotional_situations = {
    "gothic_mystery": {
        "feelings": ["dread", "mysterious", "foreboding", "curious", "haunted"],
        "keywords": ["old stone", "corridor", "secret hidden", "ancient", "forgotten", "whispering"],
        "moods": ["dark romance", "romantic mystery", "introspection fear", "dark passion"],
        "description": "Gothic mystery with hidden secrets and atmosphere",
        "sentiment_bias": -0.3,
        "emotion_map": {"fear": 0.8, "anger": 0.3}
    },
    "dark_longing": {
        "feelings": ["longing", "obsessive", "consumed", "intense", "yearning"],
        "keywords": ["dark longing", "strange longing", "consuming desire", "forbidden want", "kidnapped", "mafia", "boss", "forced marriage"],
        "moods": ["dark romance", "obsessive love", "dark passion", "boundless passion"],
        "description": "Intense dark desires and obsessive longing",
        "sentiment_bias": -0.1,
        "emotion_map": {"love": 0.6, "fear": 0.5, "anger": 0.4}
    },
    "danger_mystery": {
        "feelings": ["danger", "fear", "thrill", "suspense", "apprehension"],
        "keywords": ["overwhelming danger", "sense of danger", "threat", "peril", "fearful"],
        "moods": ["dark romance", "introspection fear", "dark passion"],
        "description": "Dangerous situations with mysterious elements",
        "sentiment_bias": -0.4,
        "emotion_map": {"fear": 0.9, "anger": 0.5}
    },
    "atmospheric_romance": {
        "feelings": ["romantic", "mysterious", "passionate", "intense", "emotional"],
        "keywords": ["thick with emotion", "passionate", "intense feelings", "emotional atmosphere"],
        "moods": ["romantic", "sweet love", "boundless passion", "dark romance"],
        "description": "Atmospheric romantic situations",
        "sentiment_bias": 0.2,
        "emotion_map": {"love": 0.7, "joy": 0.4}
    },
    "long_travel_boredom": {
        "feelings": ["bored", "restless", "tired", "monotonous"],
        "keywords": ["car for hours", "long drive", "nothing to do", "boring"],
        "moods": ["soothing romance", "calm dreamy", "calm introspection"],
        "description": "Long, boring travel needing pleasant distraction",
        "sentiment_bias": -0.2,
        "emotion_map": {"sadness": 0.3}
    },
    "high_stakes_preparation": {
        "feelings": ["determined", "focused", "nervous", "ambitious"],
        "keywords": ["presentation", "future", "career", "important"],
        "moods": ["motivational", "victory motivation", "determination"],
        "description": "Preparing for important events",
        "sentiment_bias": 0.1,
        "emotion_map": {"joy": 0.5, "surprise": 0.2}
    },
    "heartbreak_sad": {
        "feelings": ["sad", "heartbroken", "devastated", "lonely", "grieving"],
        "keywords": ["break up", "lost you", "heart broken", "tears", "alone"],
        "moods": ["heartbreak", "introspection loss", "reflective longing"],
        "description": "Heartbreak, loss, and deep sadness",
        "sentiment_bias": -0.6,
        "emotion_map": {"sadness": 0.9, "anger": 0.4}
    },
    "joyful_love": {
        "feelings": ["happy", "joyful", "excited", "in love", "blissful", "romantic"],
        "keywords": ["happy", "joy", "love", "celebrating", "together"],
        "moods": ["sweet love", "happiness", "joyful romance", "romantic adoration"],
        "description": "Joyful and celebratory romantic moments",
        "sentiment_bias": 0.5,
        "emotion_map": {"joy": 0.9, "love": 0.8}
    },
    "motivational_drive": {
        "feelings": ["motivated", "determined", "strong", "empowered", "focused"],
        "keywords": ["motivation", "success", "goal", "achieve", "push forward"],
        "moods": ["motivational", "victory motivation", "determination", "empowerment rap"],
        "description": "Building motivation and drive for success",
        "sentiment_bias": 0.3,
        "emotion_map": {"joy": 0.7, "surprise": 0.3}
    },
    "nostalgic_reflection": {
        "feelings": ["nostalgic", "reflective", "melancholic", "wistful"],
        "keywords": ["memories", "past", "old times", "remember", "yesterday"],
        "moods": ["memories nostalgia", "reflective longing", "introspection strange"],
        "description": "Nostalgic moments and reflective thoughts",
        "sentiment_bias": -0.1,
        "emotion_map": {"sadness": 0.6, "love": 0.3}
    },
    "college_entry": {
        "feelings": ["excited", "nervous", "romantic", "new", "freshman"],
        "keywords": ["college", "entry", "first day", "campus", "university"],
        "moods": ["college love", "sweet love", "romantic", "hope new start"],
        "description": "Exciting entry into college life with romantic vibes",
        "sentiment_bias": 0.3,
        "emotion_map": {"joy": 0.7, "surprise": 0.6, "love": 0.4}
    },
    "cozy_gentle_romance": {
        "feelings": ["gentle", "warm", "content", "relieved", "romantic"],
        "keywords": ["fireplace", "warmth", "home", "quiet comfort", "gentle romance", "journey hardship", "worth it"],
        "moods": ["sweet love", "romantic", "soothing romance", "calm dreamy"],
        "description": "Cozy, gentle romantic moments at home after hardship",
        "sentiment_bias": 0.4,
        "emotion_map": {"love": 0.7, "joy": 0.5}
    }
}

# --- EMOTIONAL WORD BANK ---
emotional_words = {
    "dark": ["dread", "danger", "dark", "forbidden", "secret", "hidden", "mysterious", "ancient", "stone", "corridor", "overwhelming", "strange", "haunted", "ghostly", "shadow", "midnight", "threatening", "kidnapped", "mafia", "boss"],
    "romantic": ["longing", "desire", "passion", "yearning", "love", "heart", "soul", "intimate", "connection", "devotion", "romance", "kiss", "embrace", "marry"],
    "mystery": ["secret", "hidden", "unknown", "puzzle", "mystery", "enigma", "riddle", "clue", "discover", "reveal"],
    "fear": ["dread", "fear", "terror", "panic", "anxiety", "apprehension", "unease", "foreboding", "scared"],
    "atmospheric": ["air", "thick", "heavy", "atmosphere", "mood", "vibe", "feeling", "sense", "aura", "energy"],
    "happy": ["happy", "joy", "excited", "celebrate", "fun", "bliss", "laugh", "smile", "ecstatic"],
    "sad": ["sad", "depressed", "cry", "tear", "loss", "grief", "melancholy", "despair", "broken"],
    "motivational": ["motivate", "success", "goal", "achieve", "strong", "empower", "victory", "rise", "conquer"],
    "cozy": ["warmth", "fireplace", "home", "quiet", "comfort", "gentle", "cozy", "relieved", "content"]
}

def get_spotify_client():
    """Get Spotify client with OAuth"""
    try:
        # Use direct values instead of variables
        client_id = SPOTIFY_CLIENT_ID or '7f1404593f0c4f23a2c6464d36deab37'
        client_secret = SPOTIFY_CLIENT_SECRET or '029fcc7c966842cbab01b842c3942765'
        redirect_uri = SPOTIFY_REDIRECT_URI or 'https://dream-app-lpo2.onrender.com/callback'
        
        print(f"DEBUG: Using client_id = {client_id}")
        
        cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope='user-library-read user-read-playback-state user-modify-playback-state',
            cache_handler=cache_handler,
            show_dialog=True
        )
        return spotipy.Spotify(auth_manager=auth_manager)
    except Exception as e:
        logger.error(f"Error creating Spotify client: {e}")
        return None
    
def understand_complex_emotions(user_input):
    """Analyze user input for emotional context"""
    user_input_lower = user_input.lower()
    
    # Basic TextBlob sentiment
    blob = TextBlob(user_input)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    
    # Advanced emotion classification
    emotion_results = []
    if emotion_classifier:
        emotion_results = emotion_classifier(user_input)
    
    # Emotional word scoring
    emotion_scores = {}
    for category, words in emotional_words.items():
        score = 0
        for word in words:
            if word in user_input_lower:
                score += 2
                score += user_input_lower.count(word) - 1
        emotion_scores[category] = score
    
    # Situation scoring
    situation_scores = {}
    
    for situation, info in emotional_situations.items():
        score = 0.0
        
        # Keyword matching
        for keyword in info['keywords']:
            if keyword in user_input_lower:
                score += 3
        
        # Emotional context matching
        for feeling in info['feelings']:
            if feeling in user_input_lower:
                score += 2
        
        # Sentiment bias adjustment
        sentiment_adjust = 0.0
        if info['sentiment_bias'] > 0 and polarity > 0:
            sentiment_adjust = polarity * 10
        elif info['sentiment_bias'] < 0 and polarity < 0:
            sentiment_adjust = abs(polarity) * 10
        score += sentiment_adjust
        
        # Advanced AI emotion boost
        if emotion_classifier:
            for result in emotion_results:
                emotion_label = result['label'].lower()
                if emotion_label in info['emotion_map']:
                    score += result['score'] * info['emotion_map'][emotion_label] * 10
        
        # Context patterns
        if any(word in user_input_lower for word in ['dread', 'danger', 'fear']) and any(word in user_input_lower for word in ['longing', 'desire', 'secret']):
            if situation in ["gothic_mystery", "dark_longing", "danger_mystery"]:
                score += 8
        
        if "stone corridor" in user_input_lower or "old stone" in user_input_lower:
            if situation == "gothic_mystery":
                score += 10
        
        if "dark longing" in user_input_lower or "strange longing" in user_input_lower:
            if situation == "dark_longing":
                score += 10
        
        if "overwhelming danger" in user_input_lower:
            if situation == "danger_mystery":
                score += 8
        
        # Additional patterns
        if any(word in user_input_lower for word in ['break up', 'breakup']) and polarity < -0.2:
            if situation == "heartbreak_sad":
                score += 12
        
        if any(word in user_input_lower for word in ['happy', 'joy']) and polarity > 0.3:
            if situation == "joyful_love":
                score += 10
        
        if "college" in user_input_lower:
            if situation == "college_entry":
                score += 10
        
        if "gentle" in user_input_lower and "romance" in user_input_lower:
            if situation == "cozy_gentle_romance":
                score += 15
        
        if "kidnapped" in user_input_lower and "marry" in user_input_lower:
            if situation == "dark_longing":
                score += 20
        
        if "breakup" in user_input_lower or "break up" in user_input_lower:
            if situation == "heartbreak_sad":
                score += 15
        
        situation_scores[situation] = score
    
    # Get best situation
    best_situation = max(situation_scores, key=situation_scores.get)
    
    # Enhanced overrides
    if (emotion_scores.get('dark', 0) > 3 and emotion_scores.get('mystery', 0) > 2):
        best_situation = "dark_longing"
    
    if polarity < -0.3 and any(word in user_input_lower for word in ['love', 'heart']):
        best_situation = "heartbreak_sad"
    
    if polarity > 0.4 and emotion_scores.get('romantic', 0) > 2:
        best_situation = "joyful_love"
    
    if "romantic" in user_input_lower and "college" in user_input_lower:
        best_situation = "college_entry"
    
    situation_info = emotional_situations[best_situation]
    
    # Override moods with detected emotion
    top_emotion = emotion_results[0]['label'].lower() if emotion_classifier and emotion_results else "other"
    situation_info['moods'] = emotion_to_moods.get(top_emotion, situation_info['moods'])
    
    return {
        'situation_name': best_situation,
        'situation_info': situation_info,
        'polarity': polarity,
        'subjectivity': subjectivity,
        'emotion_scores': emotion_scores,
        'top_emotions': [r['label'] for r in emotion_results[:2]] if emotion_results else []
    }

def play_audio_file(file_path):
    """Play local audio file"""
    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        return True
    except Exception as e:
        logger.error(f"Audio error: {e}")
        return False

def find_songs_for_situation(situation_info, polarity):
    """Find songs matching the emotional situation"""
    possible_moods = situation_info['moods'].copy()
    
    # Mood mapping for better matching
    mood_mapping = {
        "romantic mystery": "dark romance",
        "introspection fear": "dark romance", 
        "obsessive love": "dark romance",
        "soothing romance": "romantic",
        "calm dreamy": "calm introspection",
        "reflective longing": "introspection loss",
        "joyful romance": "sweet love",
        "romantic adoration": "sweet love",
        "hope new start": "romantic"
    }
    
    # Try exact/mapped moods first
    for mood in possible_moods:
        mapped_mood = mood_mapping.get(mood.lower(), mood.lower())
        songs_for_mood = df[df['mood_lower'] == mapped_mood].copy()
        
        if not songs_for_mood.empty:
            songs_for_mood['file_path_abs'] = songs_for_mood.apply(match_file, axis=1)
            playable_songs = songs_for_mood.dropna(subset=['file_path_abs'])
            
            if len(playable_songs) > 0:
                return playable_songs, mood
    
    # Fallback to any playable songs
    all_playable_songs = []
    for _, song in df.iterrows():
        file_path = match_file(song)
        if file_path and os.path.exists(file_path):
            all_playable_songs.append((song, file_path))
    
    if all_playable_songs:
        return pd.DataFrame([s[0] for s in all_playable_songs]), "various moods"
    
    return pd.DataFrame(), "none"

def match_file(song_row):
    """Match song with local audio file"""
    song_name = song_row['song_name']
    file_path = song_row.get('file_path', '')
    filename = song_row.get('filename', '')
    
    if pd.notna(file_path) and os.path.exists(str(file_path).replace('\\', '/')):
        return str(file_path).replace('\\', '/')
    
    if pd.notna(filename):
        possible_path = os.path.join(folder, str(filename))
        if os.path.exists(possible_path):
            return possible_path
    
    clean_song_name = re.sub(r'[^\w\s]', '', str(song_name).lower().strip())
    
    for original_file in files:
        clean_file = re.sub(r'[^\w\s]', '', original_file.lower().replace('.mp3', '').replace('.m4a', ''))
        
        if (clean_song_name in clean_file or 
            clean_file in clean_song_name or
            len(set(clean_song_name.split()) & set(clean_file.split())) >= 1):
            
            matched_path = os.path.join(folder, original_file)
            if os.path.exists(matched_path):
                return matched_path
    
    return None

def search_spotify_tracks(mood_keywords, limit=10):
    """Search Spotify for tracks based on mood"""
    try:
        sp = get_spotify_client()
        if not sp:
            return []
        
        # Combine mood keywords for search
        search_query = " OR ".join(mood_keywords[:3])
        
        results = sp.search(
            q=search_query,
            type='track',
            limit=limit,
            market='US'
        )
        
        tracks = []
        for track in results['tracks']['items']:
            track_info = {
                'id': track['id'],
                'name': track['name'],
                'artist': ', '.join(artist['name'] for artist in track['artists']),
                'album': track['album']['name'],
                'preview_url': track['preview_url'],
                'external_url': track['external_urls']['spotify'],
                'image': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'duration_ms': track['duration_ms']
            }
            tracks.append(track_info)
        
        return tracks
    
    except Exception as e:
        logger.error(f"Spotify search error: {e}")
        return []

def play_on_spotify(track_id):
    """Play track on user's Spotify device"""
    try:
        sp = get_spotify_client()
        if not sp:
            return False, "Not authenticated with Spotify"
        
        # Get available devices
        devices = sp.devices()
        if not devices['devices']:
            return False, "No active Spotify devices found"
        
        # Start playback on first available device
        device_id = devices['devices'][0]['id']
        sp.start_playback(device_id=device_id, uris=[f'spotify:track:{track_id}'])
        return True, "Playing on Spotify"
    
    except Exception as e:
        return False, str(e)

# --- FLASK ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    auth_url = get_spotify_client().auth_manager.get_authorize_url()
    return jsonify({'auth_url': auth_url})

@app.route('/callback')
def callback():
    get_spotify_client().auth_manager.get_access_token(request.args['code'])
    return render_template('index.html', spotify_connected=True)

@app.route('/analyze', methods=['POST'])
def analyze_emotion():
    try:
        user_input = request.json.get('message', '')
        
        if not user_input:
            return jsonify({'error': 'Please provide some text to analyze'})
        
        # Analyze emotions
        analysis_result = understand_complex_emotions(user_input)
        
        # Get local songs
        local_songs, detected_mood = find_songs_for_situation(
            analysis_result['situation_info'], 
            analysis_result['polarity']
        )
        
        # Search Spotify
        mood_keywords = analysis_result['situation_info']['moods'][:5]
        spotify_tracks = search_spotify_tracks(mood_keywords)
        
        # Prepare response
        response = {
            'analysis': analysis_result,
            'local_songs': local_songs.to_dict('records') if not local_songs.empty else [],
            'spotify_tracks': spotify_tracks,
            'mood_keywords': mood_keywords
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({'error': str(e)})

@app.route('/play-local/<int:song_id>')
def play_local_song(song_id):
    try:
        song = df.iloc[song_id].to_dict()
        file_path = match_file(song)
        
        if file_path and os.path.exists(file_path):
            success = play_audio_file(file_path)
            if success:
                return jsonify({
                    'success': True, 
                    'message': f'Playing: {song["song_name"]}',
                    'song': song['song_name'],
                    'artist': song['artist']
                })
        
        return jsonify({'error': 'Audio file not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/play-spotify/<track_id>')
def play_spotify_track(track_id):
    success, message = play_on_spotify(track_id)
    return jsonify({'success': success, 'message': message})

@app.route('/stop-audio')
def stop_audio():
    try:
        pygame.mixer.music.stop()
        return jsonify({'success': True, 'message': 'Playback stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/check-auth')
def check_auth():
    try:
        sp = get_spotify_client()
        if sp.current_user():
            return jsonify({'authenticated': True})
    except:
        pass
    return jsonify({'authenticated': False})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    # Debug: Check what's actually being loaded
    print("=== DEBUG: Environment Variables ===")
    print(f"SPOTIFY_CLIENT_ID: {os.getenv('SPOTIFY_CLIENT_ID')}")
    print(f"SPOTIFY_CLIENT_SECRET: {os.getenv('SPOTIFY_CLIENT_SECRET')}")
    print(f"Current directory: {os.getcwd()}")
    print(f".env file exists: {os.path.exists('.env')}")
    print("====================================")
    logger.info(f"🚀 Starting Emotional Music Companion on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
