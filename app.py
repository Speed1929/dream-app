import os
# TEMPORARY FIX - Set Spotify credentials directly
os.environ['SPOTIPY_CLIENT_ID'] = '7f1404593f0c4f23a2c6464d36deab37'
os.environ['SPOTIPY_CLIENT_SECRET'] = '029fcc7c966842cbab01b842c3942765'
os.environ['SPOTIPY_REDIRECT_URI'] = 'https://dream-app-lpo2.onrender.com/callback'

from flask import Flask, request, jsonify, session
import pandas as pd
import numpy as np
from textblob import TextBlob
import re
import random
import time
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

# Spotify credentials
SPOTIFY_CLIENT_ID = '7f1404593f0c4f23a2c6464d36deab37'
SPOTIFY_CLIENT_SECRET = '029fcc7c966842cbab01b842c3942765'
SPOTIFY_REDIRECT_URI = 'https://dream-app-lpo2.onrender.com/callback'

# Remove emotion classifier (pytorch dependency) and use TextBlob only
logger.info("✅ Using lightweight TextBlob for sentiment analysis")

# --- EMOTION TO MOODS MAPPING ---
# --- ENHANCED EMOTION TO MOODS MAPPING ---
emotion_to_moods = {
    "sadness": [
        "heartbreak", "heartbreak pain", "bittersweet unrequited", "wanderer loss", "heartbreak loss", 
        "restless longing", "reflective longing", "introspection loss", "memories nostalgia", 
        "longing reunion", "hopeful longing", "rainy days", "winter bear", "lonely whale", 
        "separation pain", "trauma reflection", "melancholy loss", "introspection strange", 
        "rainy melancholy", "illusion love", "ending relationship", "guilt stigma", "hidden struggles", 
        "self-doubt", "overwork reflection", "sad instrumental", "emotional pain", "tearful moments",
        "lost love", "empty feeling", "quiet despair", "aching heart", "fading memories"
    ],
    "joy": [
        "sweet love", "joyful romance", "joyful love", "sweet adoration", "happiness", "fun love", 
        "playful romance", "playful flirtation", "victory motivation", "girls empowerment", 
        "vibe connection", "eternal bulletproof", "youth forever", "future hope", "celebration pride", 
        "playful banter", "romantic tease", "sweet theft", "shy flirtation", "passionate dance", 
        "playful passion", "energetic flirtation", "energetic arrival", "energetic party", 
        "smooth fun", "chance dance", "boom fun", "marching band", "party call", "fun chicken", 
        "fun remix", "fun party", "fun crush", "embarrassment fun", "fun tuna", "epic motivation", 
        "count fun", "thug take", "seven seas", "permission joy", "blissful moments", "carefree love",
        "sunshine happiness", "celebratory vibes", "uplifting beats", "dancing joy"
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
        "allah girl", "jolt strong", "eternal bulletproof", "we on",
        # Enhanced dark romance themes
        "possessive love", "jealous devotion", "intense obsession", "forbidden desire", 
        "dangerous attraction", "toxic passion", "consuming love", "unhealthy attachment",
        "dark devotion", "fatal attraction", "obsessive possession", "intense yearning",
        "dangerous romance", "forbidden romance", "taboo love", "secret obsession"
    ],
    "anger": [
        "jolt strong", "divine jealousy", "warning sound", "resistance", "social critique", 
        "freedom rebellion", "empowering diss", "rap challenge", "rap triptych",
        "intense fury", "betrayal pain", "broken trust", "revenge motivation", "righteous anger",
        "passionate rage", "fiery determination", "protective anger", "defensive strength"
    ],
    "fear": [
        "introspection fear", "dark romance", "dark passion", "dark introspection",
        "anxious love", "uncertain future", "heart apprehension", "relationship anxiety",
        "fearful devotion", "protective fear", "worried love", "apprehensive romance"
    ],
    "surprise": [
        "playful confusion", "3d dimension", "never let", "seven days", "marching band", 
        "unknown mood", "unknown", "reel audio", "sudden love", "unexpected romance",
        "surprise attraction", "whirlwind romance", "instant connection", "fateful meeting"
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
        "count fun", "thug take", "seven seas", "smooth fun", 
        "chance dance", "boom fun", "marching band", "party call",
        "complex emotions", "mixed feelings", "emotional turmoil", "conflicted heart"
    ]
}

# --- ENHANCED EMOTIONAL SITUATIONS ---
emotional_situations = {
    "dark_romance_obsessive": {
        "feelings": ["obsessed", "possessive", "jealous", "consumed", "intense", "protective", "controlling"],
        "keywords": ["obsessed", "possessive", "jealous", "mine", "only mine", "can't live without", "won't let you go", 
                    "belongs to me", "protective", "controlling", "overprotective", "smothering", "consuming love"],
        "moods": ["dark romance", "obsessive love", "possessive love", "jealous devotion", "intense obsession"],
        "description": "Intense, possessive love with obsessive tendencies",
        "sentiment_bias": -0.2,
        "emotion_map": {"love": 0.8, "fear": 0.6, "anger": 0.4}
    },
    "mafia_dark_romance": {
        "feelings": ["dangerous", "powerful", "protective", "feared", "respected", "intense", "forbidden"],
        "keywords": ["mafia", "boss", "kingpin", "underworld", "crime lord", "dangerous man", "powerful",
                    "feared", "respected", "protection", "territory", "loyalty", "betrayal", "revenge"],
        "moods": ["dark romance", "dangerous attraction", "forbidden desire", "protective love", "intense passion"],
        "description": "Dangerous romance with mafia or underworld themes",
        "sentiment_bias": -0.3,
        "emotion_map": {"love": 0.7, "fear": 0.7, "anger": 0.5}
    },
    "forbidden_romance": {
        "feelings": ["forbidden", "secret", "taboo", "exciting", "dangerous", "thrilling", "illicit"],
        "keywords": ["forbidden", "taboo", "secret", "hidden", "wrong but feels right", "illicit",
                    "against the rules", "secret meetings", "hidden love", "stolen moments"],
        "moods": ["forbidden romance", "secret love", "taboo love", "dangerous attraction", "intense passion"],
        "description": "Secret, forbidden love that breaks social norms",
        "sentiment_bias": 0.1,
        "emotion_map": {"love": 0.8, "fear": 0.5, "surprise": 0.4}
    },
    "gothic_mystery": {
        "feelings": ["dread", "mysterious", "foreboding", "curious", "haunted", "atmospheric", "eerie"],
        "keywords": ["old stone", "corridor", "secret hidden", "ancient", "forgotten", "whispering", 
                    "haunted", "ghostly", "ancient castle", "family secrets", "hidden past"],
        "moods": ["dark romance", "romantic mystery", "introspection fear", "dark passion", "atmospheric love"],
        "description": "Gothic mystery with hidden secrets and haunting atmosphere",
        "sentiment_bias": -0.3,
        "emotion_map": {"fear": 0.8, "love": 0.6, "surprise": 0.4}
    },
    "dark_longing": {
        "feelings": ["longing", "obsessive", "consumed", "intense", "yearning", "aching", "unfulfilled"],
        "keywords": ["dark longing", "strange longing", "consuming desire", "forbidden want", "kidnapped", 
                    "forced marriage", "arranged marriage", "unwanted attraction", "complicated desire"],
        "moods": ["dark romance", "obsessive love", "dark passion", "boundless passion", "intense yearning"],
        "description": "Intense dark desires and obsessive longing",
        "sentiment_bias": -0.1,
        "emotion_map": {"love": 0.6, "fear": 0.5, "anger": 0.4}
    },
    "danger_mystery": {
        "feelings": ["danger", "fear", "thrill", "suspense", "apprehension", "edge", "uncertainty"],
        "keywords": ["overwhelming danger", "sense of danger", "threat", "peril", "fearful", "life at stake",
                    "dangerous situation", "risky", "gambling with life"],
        "moods": ["dark romance", "introspection fear", "dark passion", "dangerous attraction"],
        "description": "Dangerous situations with mysterious elements",
        "sentiment_bias": -0.4,
        "emotion_map": {"fear": 0.9, "anger": 0.5, "surprise": 0.3}
    },
    "enemies_to_lovers": {
        "feelings": ["tense", "competitive", "passionate", "fiery", "conflicted", "transformative", "heated"],
        "keywords": ["enemies", "rivals", "hate", "dislike", "competitive", "fiery", "tension",
                    "from enemies to lovers", "love-hate", "complicated relationship"],
        "moods": ["dark romance", "passionate dance", "fiery love", "intense passion", "transformative love"],
        "description": "Transition from enemies to passionate lovers",
        "sentiment_bias": 0.2,
        "emotion_map": {"love": 0.7, "anger": 0.6, "surprise": 0.5}
    },
    "atmospheric_romance": {
        "feelings": ["romantic", "mysterious", "passionate", "intense", "emotional", "deep", "soulful"],
        "keywords": ["thick with emotion", "passionate", "intense feelings", "emotional atmosphere",
                    "soulful", "deep connection", "emotional intensity"],
        "moods": ["romantic", "sweet love", "boundless passion", "dark romance", "emotional love"],
        "description": "Atmospheric romantic situations with deep emotional connection",
        "sentiment_bias": 0.2,
        "emotion_map": {"love": 0.7, "joy": 0.4, "sadness": 0.3}
    },
    "heartbreak_sad": {
        "feelings": ["sad", "heartbroken", "devastated", "lonely", "grieving", "lost", "empty"],
        "keywords": ["break up", "lost you", "heart broken", "tears", "alone", "goodbye", "ended",
                    "moving on", "letting go", "painful memories"],
        "moods": ["heartbreak", "introspection loss", "reflective longing", "emotional pain", "lost love"],
        "description": "Heartbreak, loss, and deep sadness",
        "sentiment_bias": -0.6,
        "emotion_map": {"sadness": 0.9, "anger": 0.4, "fear": 0.3}
    },
    "joyful_love": {
        "feelings": ["happy", "joyful", "excited", "in love", "blissful", "romantic", "ecstatic"],
        "keywords": ["happy", "joy", "love", "celebrating", "together", "perfect", "bliss",
                    "wonderful", "amazing", "beautiful relationship"],
        "moods": ["sweet love", "happiness", "joyful romance", "romantic adoration", "blissful moments"],
        "description": "Joyful and celebratory romantic moments",
        "sentiment_bias": 0.5,
        "emotion_map": {"joy": 0.9, "love": 0.8, "surprise": 0.3}
    },
    "motivational_drive": {
        "feelings": ["motivated", "determined", "strong", "empowered", "focused", "ambitious", "driven"],
        "keywords": ["motivation", "success", "goal", "achieve", "push forward", "determination",
                    "ambition", "drive", "focus", "achievement"],
        "moods": ["motivational", "victory motivation", "determination", "empowerment rap", "epic motivation"],
        "description": "Building motivation and drive for success",
        "sentiment_bias": 0.3,
        "emotion_map": {"joy": 0.7, "surprise": 0.3, "anger": 0.2}
    },
    "nostalgic_reflection": {
        "feelings": ["nostalgic", "reflective", "melancholic", "wistful", "remembering", "bittersweet"],
        "keywords": ["memories", "past", "old times", "remember", "yesterday", "childhood",
                    "looking back", "bittersweet", "fond memories"],
        "moods": ["memories nostalgia", "reflective longing", "introspection strange", "bittersweet unrequited"],
        "description": "Nostalgic moments and reflective thoughts",
        "sentiment_bias": -0.1,
        "emotion_map": {"sadness": 0.6, "love": 0.3, "joy": 0.3}
    },
    "college_entry": {
        "feelings": ["excited", "nervous", "romantic", "new", "freshman", "hopeful", "anxious"],
        "keywords": ["college", "entry", "first day", "campus", "university", "freshman",
                    "new beginning", "student life", "campus romance"],
        "moods": ["college love", "sweet love", "romantic", "hope new start", "youthful romance"],
        "description": "Exciting entry into college life with romantic vibes",
        "sentiment_bias": 0.3,
        "emotion_map": {"joy": 0.7, "surprise": 0.6, "love": 0.4}
    },
    "cozy_gentle_romance": {
        "feelings": ["gentle", "warm", "content", "relieved", "romantic", "safe", "comfortable"],
        "keywords": ["fireplace", "warmth", "home", "quiet comfort", "gentle romance", "journey hardship", 
                    "worth it", "safe haven", "comfortable", "peaceful"],
        "moods": ["sweet love", "romantic", "soothing romance", "calm dreamy", "gentle romance"],
        "description": "Cozy, gentle romantic moments at home after hardship",
        "sentiment_bias": 0.4,
        "emotion_map": {"love": 0.7, "joy": 0.5, "sadness": 0.2}
    },
    "second_chance_romance": {
        "feelings": ["hopeful", "renewed", "forgiving", "cautious", "redeeming", "healing", "second try"],
        "keywords": ["second chance", "forgiveness", "redemption", "starting over", "reunited",
                    "old flames", "past lovers", "another try", "making it work"],
        "moods": ["hopeful longing", "romantic reunion", "sweet love", "emotional healing"],
        "description": "Second chance at love after past mistakes or separation",
        "sentiment_bias": 0.2,
        "emotion_map": {"love": 0.7, "joy": 0.5, "fear": 0.3}
    }
}

# --- ENHANCED EMOTIONAL WORD BANK ---
emotional_words = {
    "dark_romance": ["obsessed", "possessive", "jealous", "consuming", "dangerous", "forbidden", "taboo",
                    "intense", "protective", "controlling", "overprotective", "smothering", "unhealthy",
                    "toxic", "fatal", "dangerous", "risky", "illicit", "secret", "hidden",
                    "mafia", "boss", "kingpin", "underworld", "crime", "power", "control",
                    "kidnapped", "forced", "arranged", "unwanted", "complicated", "dark", "twisted"],
    "romantic": ["longing", "desire", "passion", "yearning", "love", "heart", "soul", "intimate", 
                "connection", "devotion", "romance", "kiss", "embrace", "marry", "adore", "cherish",
                "affection", "tenderness", "sweet", "caring", "loving", "devoted", "faithful"],
    "mystery": ["secret", "hidden", "unknown", "puzzle", "mystery", "enigma", "riddle", "clue", 
                "discover", "reveal", "uncover", "solve", "investigate", "curious", "suspense"],
    "fear": ["dread", "fear", "terror", "panic", "anxiety", "apprehension", "unease", "foreboding", 
            "scared", "worried", "nervous", "tense", "apprehensive", "concerned", "afraid"],
    "atmospheric": ["air", "thick", "heavy", "atmosphere", "mood", "vibe", "feeling", "sense", 
                   "aura", "energy", "ambiance", "environment", "setting", "scene", "background"],
    "happy": ["happy", "joy", "excited", "celebrate", "fun", "bliss", "laugh", "smile", "ecstatic",
             "delighted", "pleased", "content", "cheerful", "joyful", "blissful", "euphoric"],
    "sad": ["sad", "depressed", "cry", "tear", "loss", "grief", "melancholy", "despair", "broken",
           "heartbroken", "devastated", "miserable", "sorrow", "unhappy", "down", "blue"],
    "motivational": ["motivate", "success", "goal", "achieve", "strong", "empower", "victory", "rise",
                    "conquer", "determined", "focused", "driven", "ambitious", "persistent", "resilient"],
    "cozy": ["warmth", "fireplace", "home", "quiet", "comfort", "gentle", "cozy", "relieved", "content",
            "safe", "secure", "peaceful", "tranquil", "calm", "serene", "comforting"],
    "angry": ["angry", "mad", "furious", "enraged", "irritated", "annoyed", "frustrated", "outraged",
             "bitter", "resentful", "hostile", "aggressive", "vengeful", "spiteful"],
    "surprised": ["surprised", "shocked", "amazed", "astonished", "stunned", "astounded", "startled",
                 "unexpected", "sudden", "unforeseen", "unanticipated", "unpredicted"]
}

def get_spotify_client():
    """Get Spotify client with OAuth"""
    try:
        client_id = SPOTIFY_CLIENT_ID or '7f1404593f0c4f23a2c6464d36deab37'
        client_secret = SPOTIFY_CLIENT_SECRET or '029fcc7c966842cbab01b842c3942765'
        redirect_uri = SPOTIFY_REDIRECT_URI or 'https://dream-app-lpo2.onrender.com/callback'
        
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
    """Analyze user input for emotional context using TextBlob only"""
    user_input_lower = user_input.lower()
    
    # Basic TextBlob sentiment
    blob = TextBlob(user_input)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    
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
    
    # Determine emotion based on sentiment and word scores
    if polarity > 0.3:
        top_emotion = "joy"
    elif polarity < -0.3:
        top_emotion = "sadness"
    elif emotion_scores.get('romantic', 0) > 3:
        top_emotion = "love"
    elif emotion_scores.get('fear', 0) > 3:
        top_emotion = "fear"
    elif emotion_scores.get('anger', 0) > 3:
        top_emotion = "anger"
    else:
        top_emotion = "other"
    
    situation_info['moods'] = emotion_to_moods.get(top_emotion, situation_info['moods'])
    
    return {
        'situation_name': best_situation,
        'situation_info': situation_info,
        'polarity': polarity,
        'subjectivity': subjectivity,
        'emotion_scores': emotion_scores,
        'top_emotions': [top_emotion]
    }

def search_spotify_tracks(mood_keywords, limit=15):
    """Search Spotify for tracks based on mood"""
    try:
        sp = get_spotify_client()
        if not sp:
            return []
        
        # Combine mood keywords for search
        search_terms = []
        for keyword in mood_keywords[:3]:
            # Clean up the keyword for better search
            clean_keyword = re.sub(r'[^\w\s]', '', keyword)
            search_terms.append(clean_keyword)
        
        search_query = " OR ".join(search_terms)
        
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
        
        logger.info(f"✅ Found {len(tracks)} Spotify tracks for query: {search_query}")
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
            return False, "No active Spotify devices found. Please open Spotify on any device."
        
        # Start playback on first available device
        device_id = devices['devices'][0]['id']
        sp.start_playback(device_id=device_id, uris=[f'spotify:track:{track_id}'])
        return True, "Playing on Spotify"
    
    except Exception as e:
        logger.error(f"Spotify playback error: {e}")
        return False, str(e)

# HTML content embedded directly
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Emotional Music Companion</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: black;
            min-height: 100vh;
            color: #333;
            padding: 20px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        header {
            text-align: center;
            margin-bottom: 30px;
        }

        h1 {
            color: #764ba2;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .subtitle {
            color: #666;
            font-size: 1.1em;
        }

        .spotify-section {
            text-align: center;
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }

        .btn-spotify {
            background: #1DB954;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn-spotify:hover {
            background: #1ed760;
            transform: translateY(-2px);
        }

        .status {
            margin-top: 10px;
            font-size: 14px;
        }

        .input-section {
            margin-bottom: 30px;
        }

        #userInput {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            resize: vertical;
            font-family: inherit;
            margin-bottom: 15px;
            min-height: 120px;
        }

        #userInput:focus {
            outline: none;
            border-color: #667eea;
        }

        .btn-primary {
            background: black;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
            transition: all 0.3s ease;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        .loading {
            text-align: center;
            padding: 40px;
            display: none;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .results-section {
            display: none;
        }

        .analysis-result {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }

        .emotion-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 10px 0;
        }

        .emotion-tag {
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 14px;
        }

        .tracks-result {
            display: grid;
            gap: 15px;
        }

        .track-card {
            display: flex;
            align-items: center;
            background: white;
            border: 1px solid #e1e5e9;
            border-radius: 10px;
            padding: 15px;
            transition: all 0.3s ease;
        }

        .track-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .track-image {
            width: 60px;
            height: 60px;
            border-radius: 8px;
            margin-right: 15px;
        }

        .track-info {
            flex: 1;
        }

        .track-name {
            font-weight: bold;
            margin-bottom: 5px;
        }

        .track-artist {
            color: #666;
            font-size: 14px;
        }

        .track-actions {
            display: flex;
            gap: 10px;
        }

        .btn-play {
            background: #1DB954;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        }

        .btn-play:hover {
            background: #1ed760;
        }

        .btn-preview {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        }

        .btn-preview:hover {
            background: #764ba2;
        }

        .audio-preview {
            width: 100%;
            margin-top: 10px;
        }

        .situation-description {
            font-style: italic;
            color: #666;
            margin: 10px 0;
        }

        .analysis-details {
            font-size: 14px;
            color: #888;
            margin-top: 10px;
        }

        .error {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #c33;
        }

        .tracks-count {
            text-align: center;
            color: #666;
            margin: 10px 0;
            font-style: italic;
        }

        @media (max-width: 600px) {
            .container {
                padding: 20px;
            }
            
            h1 {
                font-size: 2em;
            }
            
            .track-card {
                flex-direction: column;
                text-align: center;
            }
            
            .track-image {
                margin-right: 0;
                margin-bottom: 10px;
            }
            
            .track-actions {
                width: 100%;
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎵 Daydreamers</h1>
            <p class="subtitle">I understand complex emotions and find perfect Spotify music for you</p>
        </header>

        <div class="main-content">
            <!-- Spotify Connection -->
            <div class="spotify-section">
                <button id="connectSpotify" class="btn-spotify">
                    🔗 Connect Spotify
                </button>
                <div id="spotifyStatus" class="status">
                    🔒 Connect to play music directly on Spotify
                </div>
            </div>

            <!-- Input Section -->
            <div class="input-section">
                <textarea 
                    id="userInput" 
                    placeholder="Describe your emotions, situation, or atmosphere... 

Examples:
• 'Walking through an old stone corridor with hidden secrets'
• 'Heartbroken after a breakup, feeling completely alone'
• 'Excited about college entry with romantic expectations'
• 'Cozy by the fireplace after a long journey'
• 'Dark longing and mysterious desires'"
                ></textarea>
                <button id="analyzeBtn" class="btn-primary">
                    🎭 Analyze Emotions & Find Music
                </button>
            </div>

            <!-- Error Display -->
            <div id="error" class="error" style="display: none;"></div>

            <!-- Results Section -->
            <div id="results" class="results-section">
                <div id="analysisResult" class="analysis-result"></div>
                <div id="tracksResult" class="tracks-result"></div>
            </div>

            <!-- Loading -->
            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>Analyzing emotions and searching for perfect music...</p>
            </div>
        </div>
    </div>

    <script>
        class EmotionalMusicCompanion {
            constructor() {
                this.checkAuthStatus();
                this.bindEvents();
            }

            bindEvents() {
                document.getElementById('connectSpotify').addEventListener('click', () => this.connectSpotify());
                document.getElementById('analyzeBtn').addEventListener('click', () => this.analyzeEmotions());
            }

            async checkAuthStatus() {
                try {
                    const response = await fetch('/check-auth');
                    const data = await response.json();
                    
                    const statusElement = document.getElementById('spotifyStatus');
                    if (data.authenticated) {
                        statusElement.innerHTML = '✅ Connected to Spotify';
                        statusElement.style.color = '#1DB954';
                    } else {
                        statusElement.innerHTML = '🔒 Connect to play music directly on Spotify';
                        statusElement.style.color = '#666';
                    }
                } catch (error) {
                    console.error('Auth check failed:', error);
                }
            }

            async connectSpotify() {
                try {
                    const response = await fetch('/login');
                    const data = await response.json();
                    window.location.href = data.auth_url;
                } catch (error) {
                    this.showError('Failed to connect to Spotify');
                }
            }

            async analyzeEmotions() {
                const userInput = document.getElementById('userInput').value.trim();
                
                if (!userInput) {
                    this.showError('Please describe your emotions or situation');
                    return;
                }

                this.showLoading(true);
                this.hideError();
                
                try {
                    const response = await fetch('/analyze', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ message: userInput })
                    });

                    const data = await response.json();
                    
                    if (data.error) {
                        this.showError(data.error);
                        return;
                    }

                    this.displayResults(data);
                    
                } catch (error) {
                    this.showError('Failed to analyze emotions. Please try again.');
                } finally {
                    this.showLoading(false);
                }
            }

            displayResults(data) {
                const resultsSection = document.getElementById('results');
                const analysisElement = document.getElementById('analysisResult');
                const tracksElement = document.getElementById('tracksResult');

                // Display analysis
                analysisElement.innerHTML = this.createAnalysisHTML(data.analysis);
                
                // Display tracks
                tracksElement.innerHTML = this.createTracksHTML(data.spotify_tracks, data.tracks_found);
                
                resultsSection.style.display = 'block';
                resultsSection.scrollIntoView({ behavior: 'smooth' });
            }

            createAnalysisHTML(analysis) {
                const situation = analysis.situation_info;
                
                return `
                    <h3>🎭 Emotional Analysis</h3>
                    <div class="situation-description">${situation.description}</div>
                    
                    <div class="emotion-tags">
                        ${situation.feelings.slice(0, 4).map(feeling => 
                            `<span class="emotion-tag">${feeling}</span>`
                        ).join('')}
                    </div>
                    
                    <div class="analysis-details">
                        <strong>Detected Scenario:</strong> ${analysis.situation_name.replace('_', ' ')}<br>
                        <strong>Sentiment:</strong> ${analysis.polarity > 0 ? 'Positive' : analysis.polarity < 0 ? 'Negative' : 'Neutral'} 
                        (${analysis.polarity.toFixed(2)})<br>
                        ${analysis.top_emotions.length ? `<strong>Primary Emotions:</strong> ${analysis.top_emotions.join(', ')}` : ''}
                    </div>
                `;
            }

            createTracksHTML(spotifyTracks, tracksFound) {
                let html = '<h3>🎵 Recommended Spotify Music</h3>';
                
                if (tracksFound > 0) {
                    html += `<div class="tracks-count">Found ${tracksFound} tracks matching your mood</div>`;
                }
                
                // Spotify tracks
                if (spotifyTracks && spotifyTracks.length > 0) {
                    html += spotifyTracks.map(track => this.createSpotifyTrackHTML(track)).join('');
                } else {
                    html += '<p>No tracks found for this mood. Try describing your emotions differently.</p>';
                }
                
                return html;
            }

            createSpotifyTrackHTML(track) {
                const duration = Math.floor(track.duration_ms / 1000 / 60) + ':' + 
                                String(Math.floor((track.duration_ms / 1000) % 60)).padStart(2, '0');
                
                return `
                    <div class="track-card">
                        ${track.image ? `<img src="${track.image}" alt="${track.name}" class="track-image">` : 
                          '<div class="track-image" style="background: #ddd; display: flex; align-items: center; justify-content: center; color: #666;">No Image</div>'}
                        
                        <div class="track-info">
                            <div class="track-name">${track.name}</div>
                            <div class="track-artist">${track.artist} • ${duration}</div>
                            
                            ${track.preview_url ? `
                                <audio controls class="audio-preview">
                                    <source src="${track.preview_url}" type="audio/mpeg">
                                    Your browser does not support audio preview.
                                </audio>
                            ` : '<div style="color: #888; font-size: 12px; margin-top: 5px;">No preview available</div>'}
                        </div>
                        
                        <div class="track-actions">
                            <button class="btn-play" onclick="companion.playSpotifyTrack('${track.id}')">
                                Play on Spotify
                            </button>
                            <a href="${track.external_url}" target="_blank" class="btn-preview">
                                Open in Spotify
                            </a>
                        </div>
                    </div>
                `;
            }

            async playSpotifyTrack(trackId) {
                try {
                    const response = await fetch(`/play-spotify/${trackId}`);
                    const data = await response.json();
                    
                    if (data.success) {
                        this.showMessage('🎵 Playing on Spotify! Check your Spotify app.', 'success');
                    } else {
                        this.showMessage(`❌ ${data.message}`, 'error');
                    }
                } catch (error) {
                    this.showError('Failed to play track on Spotify. Make sure you are connected.');
                }
            }

            showLoading(show) {
                document.getElementById('loading').style.display = show ? 'block' : 'none';
                document.getElementById('analyzeBtn').disabled = show;
            }

            showError(message) {
                const errorElement = document.getElementById('error');
                errorElement.textContent = message;
                errorElement.style.display = 'block';
            }

            hideError() {
                document.getElementById('error').style.display = 'none';
            }

            showMessage(message, type = 'info') {
                // Create toast notification
                const toast = document.createElement('div');
                toast.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 15px 20px;
                    border-radius: 8px;
                    color: white;
                    font-weight: bold;
                    z-index: 1000;
                    transition: all 0.3s ease;
                    background: ${type === 'error' ? '#e74c3c' : type === 'success' ? '#2ecc71' : '#3498db'};
                `;
                toast.textContent = message;
                
                document.body.appendChild(toast);
                
                setTimeout(() => {
                    toast.remove();
                }, 4000);
            }
        }

        // Initialize the application
        const companion = new EmotionalMusicCompanion();
    </script>
</body>
</html>
"""

# --- FLASK ROUTES ---

@app.route('/')
def index():
    return HTML_CONTENT

@app.route('/login')
def login():
    try:
        sp = get_spotify_client()
        auth_url = sp.auth_manager.get_authorize_url()
        return jsonify({'auth_url': auth_url})
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Failed to generate auth URL'}), 500

@app.route('/callback')
def callback():
    try:
        sp = get_spotify_client()
        sp.auth_manager.get_access_token(request.args['code'])
        # Return success page
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Spotify Connected</title>
            <style>
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    margin: 0;
                    padding: 20px;
                }
                .success-box {
                    background: white;
                    padding: 40px;
                    border-radius: 15px;
                    text-align: center;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    max-width: 400px;
                }
                .success { 
                    color: #1DB954; 
                    font-size: 24px; 
                    margin-bottom: 20px;
                }
                .message {
                    color: #666;
                    margin-bottom: 20px;
                    line-height: 1.5;
                }
            </style>
        </head>
        <body>
            <div class="success-box">
                <div class="success">✅ Spotify Connected Successfully!</div>
                <p class="message">You can now close this window and return to the Emotional Music Companion.</p>
                <button onclick="window.close()" style="
                    background: #1DB954;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 20px;
                    cursor: pointer;
                    font-size: 16px;
                ">Close Window</button>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Callback error: {e}")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Connection Failed</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 50px; 
                }
                .error { 
                    color: #e74c3c; 
                    font-size: 24px; 
                    margin-bottom: 20px; 
                }
            </style>
        </head>
        <body>
            <div class="error">❌ Spotify Connection Failed</div>
            <p>Error: {str(e)}</p>
            <p>Please try again.</p>
        </body>
        </html>
        """

@app.route('/analyze', methods=['POST'])
def analyze_emotion():
    try:
        user_input = request.json.get('message', '')
        
        if not user_input:
            return jsonify({'error': 'Please provide some text to analyze'})
        
        # Analyze emotions
        analysis_result = understand_complex_emotions(user_input)
        
        # Search Spotify with mood keywords
        mood_keywords = analysis_result['situation_info']['moods'][:5]
        spotify_tracks = search_spotify_tracks(mood_keywords)
        
        # Prepare response
        response = {
            'analysis': analysis_result,
            'spotify_tracks': spotify_tracks,
            'mood_keywords': mood_keywords,
            'tracks_found': len(spotify_tracks)
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/play-spotify/<track_id>')
def play_spotify_track(track_id):
    success, message = play_on_spotify(track_id)
    return jsonify({'success': success, 'message': message})

@app.route('/check-auth')
def check_auth():
    try:
        sp = get_spotify_client()
        if sp.current_user():
            return jsonify({'authenticated': True})
    except Exception as e:
        logger.error(f"Auth check error: {e}")
    return jsonify({'authenticated': False})

@app.route('/get-user-info')
def get_user_info():
    try:
        sp = get_spotify_client()
        user = sp.current_user()
        return jsonify({
            'authenticated': True,
            'user_name': user.get('display_name', 'User'),
            'user_id': user.get('id')
        })
    except Exception as e:
        logger.error(f"User info error: {e}")
        return jsonify({'authenticated': False})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Debug info
    print("=== DEBUG: Environment Variables ===")
    print(f"SPOTIFY_CLIENT_ID: {os.getenv('SPOTIFY_CLIENT_ID')}")
    print(f"SPOTIFY_CLIENT_SECRET: {os.getenv('SPOTIFY_CLIENT_SECRET')}")
    print(f"Current directory: {os.getcwd()}")
    print("====================================")
    
    logger.info(f"🚀 Starting Spotify-Only Emotional Music Companion on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)



