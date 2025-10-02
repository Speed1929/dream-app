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

# --- CONTEXT-AWARE EMOTIONAL SITUATIONS ---
emotional_situations = {
    "dark_romance_obsessive": {
        "feelings": ["obsessed", "possessive", "jealous", "consumed", "intense", "protective", "controlling"],
        "context_patterns": [
            r"(can't live without|won't let you go|belongs to me|mine alone|only mine)",
            r"(obsess.*love|possess.*love|jealous.*love)",
            r"(protective.*controlling|smothering.*love)",
            r"(dark.*desire|forbidden.*want)"
        ],
        "moods": ["dark romance", "obsessive love", "possessive love", "jealous devotion", "intense obsession"],
        "description": "Intense, possessive love with obsessive tendencies",
        "sentiment_bias": -0.2,
        "emotion_map": {"love": 0.8, "fear": 0.6, "anger": 0.4}
    },
    "mafia_dark_romance": {
        "feelings": ["dangerous", "powerful", "protective", "feared", "respected", "intense", "forbidden"],
        "context_patterns": [
            r"(mafia|underworld|crime lord|dangerous.*man|powerful.*boss)",
            r"(protection.*territory|loyalty.*betrayal|revenge.*love)",
            r"(feared.*respected|dangerous.*attraction)",
            r"(forbidden.*power|control.*love)"
        ],
        "moods": ["dark romance", "dangerous attraction", "forbidden desire", "protective love", "intense passion"],
        "description": "Dangerous romance with mafia or underworld themes",
        "sentiment_bias": -0.3,
        "emotion_map": {"love": 0.7, "fear": 0.7, "anger": 0.5}
    },
    "forbidden_romance": {
        "feelings": ["forbidden", "secret", "taboo", "exciting", "dangerous", "thrilling", "illicit"],
        "context_patterns": [
            r"(forbidden.*love|taboo.*relationship|secret.*love)",
            r"(hidden.*meetings|stolen.*moments|against.*rules)",
            r"(wrong.*feels right|illicit.*affair)",
            r"(secret.*passion|hidden.*desire)"
        ],
        "moods": ["forbidden romance", "secret love", "taboo love", "dangerous attraction", "intense passion"],
        "description": "Secret, forbidden love that breaks social norms",
        "sentiment_bias": 0.1,
        "emotion_map": {"love": 0.8, "fear": 0.5, "surprise": 0.4}
    },
    "gothic_mystery": {
        "feelings": ["dread", "mysterious", "foreboding", "curious", "haunted", "atmospheric", "eerie"],
        "context_patterns": [
            r"(old.*stone|ancient.*castle|stone.*corridor)",
            r"(hidden.*secrets|family.*secrets|forgotten.*past)",
            r"(haunted.*ghostly|whispering.*shadows)",
            r"(mysterious.*atmosphere|eerie.*silence)"
        ],
        "moods": ["dark romance", "romantic mystery", "introspection fear", "dark passion", "atmospheric love"],
        "description": "Gothic mystery with hidden secrets and haunting atmosphere",
        "sentiment_bias": -0.3,
        "emotion_map": {"fear": 0.8, "love": 0.6, "surprise": 0.4}
    },
    "dark_longing": {
        "feelings": ["longing", "obsessive", "consumed", "intense", "yearning", "aching", "unfulfilled"],
        "context_patterns": [
            r"(dark.*longing|strange.*longing|consuming.*desire)",
            r"(kidnapped.*marry|forced.*marriage|arranged.*marriage)",
            r"(unwanted.*attraction|complicated.*desire)",
            r"(aching.*heart|yearning.*soul)"
        ],
        "moods": ["dark romance", "obsessive love", "dark passion", "boundless passion", "intense yearning"],
        "description": "Intense dark desires and obsessive longing",
        "sentiment_bias": -0.1,
        "emotion_map": {"love": 0.6, "fear": 0.5, "anger": 0.4}
    },
    "enemies_to_lovers": {
        "feelings": ["tense", "competitive", "passionate", "fiery", "conflicted", "transformative", "heated"],
        "context_patterns": [
            r"(enemies.*lovers|hate.*love|rivals.*passion)",
            r"(competitive.*tension|fiery.*arguments)",
            r"(love.*hate relationship|complicated.*feelings)",
            r"(from.*enemies to lovers|transformative.*love)"
        ],
        "moods": ["dark romance", "passionate dance", "fiery love", "intense passion", "transformative love"],
        "description": "Transition from enemies to passionate lovers",
        "sentiment_bias": 0.2,
        "emotion_map": {"love": 0.7, "anger": 0.6, "surprise": 0.5}
    },
    "fantasy_romance": {
        "feelings": ["magical", "epic", "destined", "mythical", "enchanted", "fated", "otherworldly"],
        "context_patterns": [
            r"(magical.*world|enchanted.*forest|mythical.*creatures)",
            r"(destined.*love|fated.*mates|soul.*bond)",
            r"(epic.*quest|ancient.*prophecy)",
            r"(otherworldly.*beauty|supernatural.*love)"
        ],
        "moods": ["dark romance", "epic love", "destiny love", "magical romance", "fantasy passion"],
        "description": "Fantasy romance with magical elements and epic destiny",
        "sentiment_bias": 0.3,
        "emotion_map": {"love": 0.8, "surprise": 0.6, "joy": 0.4}
    },
    "vampire_romance": {
        "feelings": ["eternal", "dangerous", "seductive", "immortal", "thirsty", "protective", "ancient"],
        "context_patterns": [
            r"(vampire.*eternal|immortal.*love|ancient.*being)",
            r"(blood.*thirst|seductive.*danger)",
            r"(eternal.*night|undead.*love)",
            r"(protective.*ancient|dangerous.*seduction)"
        ],
        "moods": ["dark romance", "forbidden desire", "eternal love", "dangerous attraction", "vampire passion"],
        "description": "Vampire romance with eternal love and dangerous seduction",
        "sentiment_bias": -0.2,
        "emotion_map": {"love": 0.8, "fear": 0.6, "surprise": 0.4}
    },
    "royal_romance": {
        "feelings": ["regal", "forbidden", "duty", "sacrifice", "noble", "courtly", "political"],
        "context_patterns": [
            r"(royal.*marriage|prince.*princess|king.*queen)",
            r"(court.*intrigue|political.*marriage|duty.*love)",
            r"(forbidden.*royalty|noble.*sacrifice)",
            r"(castle.*romance|royal.*ball)"
        ],
        "moods": ["dark romance", "forbidden love", "royal passion", "courtly love", "noble romance"],
        "description": "Royal romance with duty, sacrifice and forbidden love",
        "sentiment_bias": 0.1,
        "emotion_map": {"love": 0.7, "fear": 0.5, "sadness": 0.3}
    },
    "heartbreak_sad": {
        "feelings": ["sad", "heartbroken", "devastated", "lonely", "grieving", "lost", "empty"],
        "context_patterns": [
            r"(break.*up|heart.*broken|lost.*love)",
            r"(tears.*alone|goodbye.*forever|ended.*relationship)",
            r"(moving.*on|letting.*go|painful.*memories)",
            r"(empty.*inside|devastated.*lost)"
        ],
        "moods": ["heartbreak", "introspection loss", "reflective longing", "emotional pain", "lost love"],
        "description": "Heartbreak, loss, and deep sadness",
        "sentiment_bias": -0.6,
        "emotion_map": {"sadness": 0.9, "anger": 0.4, "fear": 0.3}
    },
    "joyful_love": {
        "feelings": ["happy", "joyful", "excited", "in love", "blissful", "romantic", "ecstatic"],
        "context_patterns": [
            r"(happy.*together|celebrating.*love|perfect.*couple)",
            r"(blissful.*moments|wonderful.*relationship)",
            r"(joyful.*romance|excited.*love)",
            r"(beautiful.*together|amazing.*love)"
        ],
        "moods": ["sweet love", "happiness", "joyful romance", "romantic adoration", "blissful moments"],
        "description": "Joyful and celebratory romantic moments",
        "sentiment_bias": 0.5,
        "emotion_map": {"joy": 0.9, "love": 0.8, "surprise": 0.3}
    },
    "cozy_gentle_romance": {
        "feelings": ["gentle", "warm", "content", "relieved", "romantic", "safe", "comfortable"],
        "context_patterns": [
            r"(fireplace.*warmth|cozy.*home|quiet.*comfort)",
            r"(gentle.*romance|safe.*haven|comfortable.*love)",
            r"(peaceful.*moments|tranquil.*love)",
            r"(soft.*embrace|tender.*moments)"
        ],
        "moods": ["sweet love", "romantic", "soothing romance", "calm dreamy", "gentle romance"],
        "description": "Cozy, gentle romantic moments at home after hardship",
        "sentiment_bias": 0.4,
        "emotion_map": {"love": 0.7, "joy": 0.5, "sadness": 0.2}
    },
    "second_chance_romance": {
        "feelings": ["hopeful", "renewed", "forgiving", "cautious", "redeeming", "healing", "second try"],
        "context_patterns": [
            r"(second.*chance|forgiveness.*redemption|starting.*over)",
            r"(old.*flames|past.*lovers|reunited.*love)",
            r"(another.*try|making.*work|healing.*together)",
            r"(renewed.*hope|cautious.*optimism)"
        ],
        "moods": ["hopeful longing", "romantic reunion", "sweet love", "emotional healing"],
        "description": "Second chance at love after past mistakes or separation",
        "sentiment_bias": 0.2,
        "emotion_map": {"love": 0.7, "joy": 0.5, "fear": 0.3}
    }
}

# --- CONTEXTUAL ANALYSIS FUNCTIONS ---
def analyze_emotional_context(user_input):
    """Advanced emotional context analysis using multiple approaches"""
    user_input_lower = user_input.lower()
    
    # TextBlob sentiment analysis
    blob = TextBlob(user_input)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    
    # Enhanced context pattern matching
    situation_scores = {}
    
    for situation, info in emotional_situations.items():
        score = 0.0
        
        # Context pattern matching (more important than keywords)
        for pattern in info['context_patterns']:
            matches = re.findall(pattern, user_input_lower)
            if matches:
                score += len(matches) * 8  # High weight for context patterns
        
        # Feeling word matching (medium weight)
        for feeling in info['feelings']:
            if re.search(r'\b' + re.escape(feeling) + r'\b', user_input_lower):
                score += 5
        
        # Sentiment alignment
        sentiment_adjust = 0.0
        if abs(polarity) > 0.1:  # Only adjust for meaningful sentiment
            if (info['sentiment_bias'] > 0 and polarity > 0) or (info['sentiment_bias'] < 0 and polarity < 0):
                sentiment_adjust = abs(polarity) * 20
        score += sentiment_adjust
        
        # Length and complexity bonus (longer, more descriptive inputs get bonus)
        word_count = len(user_input.split())
        if word_count > 15:
            score += 5
        if word_count > 25:
            score += 5
        
        situation_scores[situation] = score
    
    # Get best situation
    best_situation = max(situation_scores, key=situation_scores.get)
    max_score = situation_scores[best_situation]
    
    # Fallback logic for low-confidence matches
    if max_score < 10:
        # Use sentiment and thematic fallbacks
        if "love" in user_input_lower or "romance" in user_input_lower:
            if polarity > 0.3:
                best_situation = "joyful_love"
            elif polarity < -0.2:
                best_situation = "heartbreak_sad"
            else:
                best_situation = "dark_romance_obsessive"
        elif "fantasy" in user_input_lower or "magic" in user_input_lower:
            best_situation = "fantasy_romance"
        elif "vampire" in user_input_lower or "eternal" in user_input_lower:
            best_situation = "vampire_romance"
        elif "royal" in user_input_lower or "prince" in user_input_lower or "queen" in user_input_lower:
            best_situation = "royal_romance"
        else:
            # Generic sentiment-based fallback
            if polarity > 0.3:
                best_situation = "joyful_love"
            elif polarity < -0.3:
                best_situation = "heartbreak_sad"
            else:
                best_situation = "cozy_gentle_romance"
    
    situation_info = emotional_situations[best_situation]
    
    # Enhanced emotion detection based on context
    emotion_weights = {
        "joy": max(0, polarity) * 15 + (1 if any(word in user_input_lower for word in ["happy", "joy", "excited", "celebrate"]) else 0),
        "sadness": max(0, -polarity) * 15 + (1 if any(word in user_input_lower for word in ["sad", "cry", "loss", "broken"]) else 0),
        "love": 10 + (5 if any(word in user_input_lower for word in ["love", "romance", "heart", "passion"]) else 0),
        "anger": (1 if any(word in user_input_lower for word in ["angry", "mad", "furious", "hate"]) else 0),
        "fear": (1 if any(word in user_input_lower for word in ["fear", "scared", "afraid", "terror"]) else 0),
        "surprise": (1 if any(word in user_input_lower for word in ["surprise", "shock", "unexpected"]) else 0),
        "other": 1
    }
    
    # Add situation-specific emotion mapping
    for emotion, weight in situation_info['emotion_map'].items():
        emotion_weights[emotion] += weight * 25
    
    # Determine top emotion
    top_emotion = max(emotion_weights, key=emotion_weights.get)
    
    # Combine situation moods with emotion moods
    situation_moods = situation_info['moods']
    emotion_moods = emotion_to_moods.get(top_emotion, [])
    
    # Remove duplicates and combine
    all_moods = list(dict.fromkeys(situation_moods + emotion_moods))
    
    # Update situation info with combined moods
    situation_info['moods'] = all_moods[:8]  # Limit to 8 most relevant moods
    
    return {
        'situation_name': best_situation,
        'situation_info': situation_info,
        'polarity': polarity,
        'subjectivity': subjectivity,
        'top_emotions': [top_emotion],
        'confidence_score': max_score
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

def search_spotify_tracks(mood_keywords, limit=15):
    """Search Spotify for tracks based on mood - IMPROVED"""
    try:
        sp = get_spotify_client()
        if not sp:
            return []
        
        # Better search term selection with context awareness
        search_terms = []
        for keyword in mood_keywords[:4]:
            # Clean and prioritize meaningful terms
            clean_keyword = re.sub(r'[^\w\s]', '', keyword)
            words = clean_keyword.split()
            
            # Prefer emotional and descriptive terms
            emotional_words = ['love', 'romance', 'heart', 'passion', 'dark', 'forbidden', 
                             'obsessive', 'eternal', 'magical', 'fantasy', 'vampire', 'royal']
            
            for word in words:
                if word in emotional_words or len(word) > 4:
                    search_terms.append(word)
            
            # Also include the full phrase for context
            if len(words) <= 3:
                search_terms.append(clean_keyword)
        
        # Remove duplicates and limit
        search_terms = list(dict.fromkeys(search_terms))[:4]
        
        if not search_terms:
            search_terms = ["emotional", "romantic", "love"]
        
        # Try multiple search strategies
        search_queries = [
            " OR ".join(search_terms),  # Broad search
            " ".join(search_terms[:2]),  # Focused search
            f'"{search_terms[0]}" mood' if search_terms else "emotional music"  # Exact match with mood context
        ]
        
        all_tracks = []
        for search_query in search_queries:
            if len(all_tracks) >= limit:
                break
                
            try:
                results = sp.search(
                    q=search_query,
                    type='track',
                    limit=limit - len(all_tracks),
                    market='US'
                )
                
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
                    # Avoid duplicates
                    if not any(t['id'] == track_info['id'] for t in all_tracks):
                        all_tracks.append(track_info)
                        
            except Exception as e:
                logger.warning(f"Search query failed '{search_query}': {e}")
                continue
        
        logger.info(f"✅ Found {len(all_tracks)} Spotify tracks for moods: {mood_keywords[:3]}")
        return all_tracks
    
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

# HTML content remains the same (too long to include here, but it's unchanged)
HTML_CONTENT = """
[Your existing HTML content remains exactly the same]
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
        
        # Use the new context-aware analysis
        analysis_result = analyze_emotional_context(user_input)
        
        # Search Spotify with mood keywords
        mood_keywords = analysis_result['situation_info']['moods'][:5]
        spotify_tracks = search_spotify_tracks(mood_keywords)
        
        # Prepare response
        response = {
            'analysis': analysis_result,
            'spotify_tracks': spotify_tracks,
            'mood_keywords': mood_keywords,
            'tracks_found': len(spotify_tracks),
            'confidence': analysis_result.get('confidence_score', 0)
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
    
    logger.info(f"🚀 Starting Context-Aware Emotional Music Companion on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
