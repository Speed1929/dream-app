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

logger.info("✅ Using enhanced emotion analysis system")

# --- COMPREHENSIVE EMOTION TO MOODS MAPPING ---
emotion_to_moods = {
    "flirting_teasing": [
        "playful flirtation", "romantic tease", "sweet theft", "shy flirtation", "energetic flirtation",
        "playful banter", "fun love", "playful romance", "smooth fun", "chance dance", "fun crush",
        "embarrassment fun", "playful passion", "cheeky romance", "flirtatious vibes", "teasing love",
        "playful tension", "romantic banter", "flirty moments", "teasing romance", "playful seduction"
    ],
    "love_devotion": [
        "sweet love", "romantic adoration", "devotion", "boundless devotion", "devotional bond",
        "faith love", "devotion darling", "soothing romance", "necessary love", "valentine love",
        "you beloved", "with you", "little love", "heart redefined", "romantic story", "devotion",
        "faithful love", "eternal devotion", "unconditional love", "soulmate connection", "deep devotion",
        "romantic commitment", "loving bond", "heartfelt devotion", "spiritual love"
    ],
    "passion_intensity": [
        "passionate dance", "playful passion", "intense passion", "boundless passion", "dark passion",
        "passion monsoon", "fiery love", "burning desire", "intense romance", "consuming passion",
        "electric love", "sizzling romance", "heated passion", "wild love", "untamed desire",
        "volcanic love", "fiery romance", "passionate embrace", "intense connection", "burning love"
    ],
    "dark_romance": [
        "dark romance", "obsessive love", "possessive love", "jealous devotion", "intense obsession",
        "forbidden desire", "dangerous attraction", "toxic passion", "consuming love", "unhealthy attachment",
        "dark devotion", "fatal attraction", "obsessive possession", "intense yearning", "dangerous romance",
        "forbidden romance", "taboo love", "secret obsession", "gothic love", "twisted desire"
    ],
    "calm_peaceful": [
        "soothing romance", "gentle romance", "calm dreamy", "peaceful love", "tranquil moments",
        "serene romance", "quiet love", "soft romance", "mellow love", "gentle affection",
        "peaceful devotion", "calm adoration", "quiet intimacy", "soft moments", "tranquil love",
        "soothing moments", "gentle connection", "peaceful bond", "calm romance", "serene love"
    ],
    "longing_yearning": [
        "restless longing", "reflective longing", "longing reunion", "hopeful longing", "wanderer love",
        "longing distance", "aching heart", "yearning soul", "pining love", "distant longing",
        "hopeful waiting", "emotional longing", "heart yearning", "soul longing", "distant love",
        "waiting heart", "yearning romance", "longing desire", "emotional pining", "heart's longing"
    ],
    "joy_happiness": [
        "joyful romance", "joyful love", "happiness", "fun love", "blissful moments", "carefree love",
        "sunshine happiness", "celebratory vibes", "uplifting beats", "dancing joy", "happy love",
        "joyful moments", "ecstatic romance", "blissful love", "happy heart", "joyful connection",
        "cheerful love", "radiant joy", "happy romance", "joyful devotion"
    ],
    "sadness_heartbreak": [
        "heartbreak", "heartbreak pain", "bittersweet unrequited", "wanderer loss", "heartbreak loss",
        "introspection loss", "memories nostalgia", "emotional pain", "tearful moments", "lost love",
        "empty feeling", "quiet despair", "aching heart", "fading memories", "broken heart",
        "sad love", "melancholy romance", "tearful love", "heartache", "emotional loss"
    ],
    "mystery_intrigue": [
        "romantic mystery", "dark introspection", "secret love", "hidden romance", "mysterious love",
        "enigmatic romance", "secret affair", "hidden passion", "mysterious connection", "intriguing love",
        "secret devotion", "hidden desire", "mysterious attraction", "secret rendezvous", "hidden feelings"
    ],
    "fantasy_magic": [
        "destiny love", "fated romance", "magical love", "enchanted romance", "fantasy passion",
        "epic love", "mythical romance", "fairy tale love", "magical connection", "enchanted moments",
        "fantasy devotion", "magical bond", "enchanted love", "fantasy romance", "magical moments"
    ],
    "sensual_intimate": [
        "passionate dance", "intimate moments", "sensual romance", "tender love", "intimate connection",
        "sensual passion", "tender moments", "intimate devotion", "sensual desire", "tender romance",
        "intimate passion", "sensual love", "tender intimacy", "sensual connection", "intimate bond"
    ],
    "angry_intense": [
        "divine jealousy", "intense fury", "betrayal pain", "broken trust", "revenge motivation",
        "righteous anger", "passionate rage", "fiery determination", "protective anger", "defensive strength",
        "angry love", "fiery passion", "intense emotion", "burning anger", "righteous fury"
    ],
    "fear_anxiety": [
        "introspection fear", "anxious love", "uncertain future", "heart apprehension", "relationship anxiety",
        "fearful devotion", "protective fear", "worried love", "apprehensive romance", "nervous love",
        "anxious heart", "fearful love", "uncertain romance", "apprehensive devotion", "worried romance"
    ],
    "surprise_excitement": [
        "playful confusion", "sudden love", "unexpected romance", "surprise attraction", "whirlwind romance",
        "instant connection", "fateful meeting", "surprise love", "unexpected connection", "sudden romance",
        "exciting love", "surprise devotion", "unexpected passion", "sudden attraction", "exciting romance"
    ],
    "nostalgic_memories": [
        "memories nostalgia", "reflective longing", "bittersweet unrequited", "fading memories",
        "past love", "nostalgic romance", "memory love", "retro romance", "old flames", "past memories",
        "nostalgic devotion", "memory lane", "past passion", "nostalgic love", "remembering love"
    ]
}

# --- UNIVERSAL EMOTIONAL SITUATIONS ---
emotional_situations = {
    # Romantic Core Emotions
    "flirting_teasing": {
        "feelings": ["flirty", "teasing", "playful", "cheeky", "charming", "seductive", "whimsical"],
        "context_patterns": [
            r"(flirt|tease|playful|banter|charming|seductive|wink|smirk|cheeky)",
            r"(playful.*touch|gentle.*tease|flirtatious.*glance)",
            r"(charming.*smile|seductive.*voice|whimsical.*romance)",
            r"(lighthearted.*fun|cheeky.*comments|flirty.*conversation)"
        ],
        "moods": ["flirting_teasing", "joy_happiness", "surprise_excitement"],
        "description": "Playful flirting and teasing with romantic tension",
        "sentiment_bias": 0.4,
        "emotion_map": {"flirting_teasing": 0.9, "joy_happiness": 0.7, "surprise_excitement": 0.5}
    },
    "love_devotion": {
        "feelings": ["devoted", "faithful", "committed", "loyal", "dedicated", "adoring", "worshipful"],
        "context_patterns": [
            r"(devot|faithful|commit|loyal|dedicate|adore|worship)",
            r"(eternal.*love|unconditional.*devotion|faithful.*heart)",
            r"(soulmate.*connection|deep.*commitment|loving.*bond)",
            r"(spiritual.*love|heartfelt.*devotion|eternal.*promise)"
        ],
        "moods": ["love_devotion", "calm_peaceful", "sensual_intimate"],
        "description": "Deep devotion and unwavering commitment in love",
        "sentiment_bias": 0.3,
        "emotion_map": {"love_devotion": 0.9, "calm_peaceful": 0.6, "sensual_intimate": 0.5}
    },
    "passionate_intensity": {
        "feelings": ["passionate", "intense", "fiery", "burning", "electric", "consuming", "volcanic"],
        "context_patterns": [
            r"(passionat|intense|fiery|burning|electric|consuming|volcanic)",
            r"(burning.*desire|electric.*touch|fiery.*kiss)",
            r"(intense.*gaze|consuming.*passion|volcanic.*emotion)",
            r"(heated.*embrace|sizzling.*chemistry|wild.*passion)"
        ],
        "moods": ["passion_intensity", "sensual_intimate", "dark_romance"],
        "description": "Intense, burning passion and electric connection",
        "sentiment_bias": 0.2,
        "emotion_map": {"passion_intensity": 0.9, "sensual_intimate": 0.7, "dark_romance": 0.4}
    },
    
    # Dark Romance Spectrum
    "dark_obsessive": {
        "feelings": ["obsessed", "possessive", "jealous", "consuming", "controlling", "protective", "intense"],
        "context_patterns": [
            r"(obsess|possess|jealous|consum|control|protective|intense)",
            r"(can't.*live.*without|won't.*let.*go|belongs.*to.*me)",
            r"(dark.*desire|forbidden.*want|dangerous.*attraction)",
            r"(protective.*rage|controlling.*love|smothering.*affection)"
        ],
        "moods": ["dark_romance", "passion_intensity", "angry_intense"],
        "description": "Dark, obsessive love with possessive tendencies",
        "sentiment_bias": -0.2,
        "emotion_map": {"dark_romance": 0.9, "passion_intensity": 0.6, "angry_intense": 0.5}
    },
    "forbidden_taboo": {
        "feelings": ["forbidden", "taboo", "secret", "illicit", "dangerous", "thrilling", "hidden"],
        "context_patterns": [
            r"(forbidden|taboo|secret|illicit|dangerous|hidden|clandestine)",
            r"(secret.*affair|hidden.*love|forbidden.*romance)",
            r"(taboo.*desire|illicit.*meeting|dangerous.*attraction)",
            r"(stolen.*moments|clandestine.*meeting|secret.*rendezvous)"
        ],
        "moods": ["dark_romance", "mystery_intrigue", "passion_intensity"],
        "description": "Forbidden love that breaks all rules and taboos",
        "sentiment_bias": 0.1,
        "emotion_map": {"dark_romance": 0.8, "mystery_intrigue": 0.7, "passion_intensity": 0.6}
    },
    
    # Emotional States
    "calm_serenity": {
        "feelings": ["calm", "peaceful", "serene", "tranquil", "soothed", "comfortable", "secure"],
        "context_patterns": [
            r"(calm|peaceful|serene|tranquil|soothe|comfort|secure)",
            r"(quiet.*moments|peaceful.*embrace|tranquil.*love)",
            r"(soothing.*touch|comfortable.*silence|secure.*arms)",
            r"(gentle.*breeze|soft.*whispers|peaceful.*togetherness)"
        ],
        "moods": ["calm_peaceful", "love_devotion", "sensual_intimate"],
        "description": "Calm, peaceful moments of serene connection",
        "sentiment_bias": 0.4,
        "emotion_map": {"calm_peaceful": 0.9, "love_devotion": 0.6, "sensual_intimate": 0.4}
    },
    "longing_desire": {
        "feelings": ["longing", "yearning", "aching", "pining", "wanting", "missing", "desiring"],
        "context_patterns": [
            r"(longing|yearning|aching|pining|missing|desiring|wanting)",
            r"(aching.*heart|yearning.*soul|longing.*gaze)",
            r"(miss.*you|want.*you|desire.*you)",
            r"(distant.*love|waiting.*heart|pining.*soul)"
        ],
        "moods": ["longing_yearning", "passion_intensity", "sadness_heartbreak"],
        "description": "Deep longing and yearning for connection",
        "sentiment_bias": -0.1,
        "emotion_map": {"longing_yearning": 0.9, "passion_intensity": 0.5, "sadness_heartbreak": 0.4}
    },
    "joyful_celebration": {
        "feelings": ["joyful", "happy", "ecstatic", "blissful", "celebratory", "elated", "radiant"],
        "context_patterns": [
            r"(joyful|happy|ecstatic|blissful|celebrat|elated|radiant)",
            r"(happy.*together|joyful.*moments|blissful.*love)",
            r"(ecstatic.*heart|radiant.*smile|elated.*embrace)",
            r"(celebrating.*love|joyful.*reunion|happy.*connection)"
        ],
        "moods": ["joy_happiness", "love_devotion", "surprise_excitement"],
        "description": "Joyful celebration of love and happiness",
        "sentiment_bias": 0.6,
        "emotion_map": {"joy_happiness": 0.9, "love_devotion": 0.7, "surprise_excitement": 0.5}
    },
    "heartbreak_loss": {
        "feelings": ["heartbroken", "devastated", "shattered", "grieving", "lost", "empty", "numb"],
        "context_patterns": [
            r"(heartbroken|devastated|shattered|grieving|lost|empty|numb)",
            r"(broken.*heart|shattered.*dreams|devastated.*soul)",
            r"(lost.*love|empty.*inside|numb.*pain)",
            r"(tearful.*goodbye|painful.*memories|aching.*loss)"
        ],
        "moods": ["sadness_heartbreak", "longing_yearning", "nostalgic_memories"],
        "description": "Deep heartbreak and emotional loss",
        "sentiment_bias": -0.7,
        "emotion_map": {"sadness_heartbreak": 0.9, "longing_yearning": 0.6, "nostalgic_memories": 0.5}
    },
    
    # Specialized Romance Types
    "mysterious_intrigue": {
        "feelings": ["mysterious", "enigmatic", "secretive", "puzzling", "intriguing", "cryptic", "unknown"],
        "context_patterns": [
            r"(myster|enigmat|secretive|puzzling|intriguing|cryptic|unknown)",
            r"(secret.*past|hidden.*identity|mysterious.*stranger)",
            r"(enigmatic.*smile|cryptic.*message|puzzling.*behavior)",
            r"(intriguing.*person|unknown.*motives|secret.*life)"
        ],
        "moods": ["mystery_intrigue", "dark_romance", "passion_intensity"],
        "description": "Mysterious and intriguing romantic connection",
        "sentiment_bias": 0.0,
        "emotion_map": {"mystery_intrigue": 0.9, "dark_romance": 0.5, "passion_intensity": 0.4}
    },
    "fantasy_magic": {
        "feelings": ["magical", "enchanted", "ethereal", "mythical", "fantastical", "dreamlike", "otherworldly"],
        "context_patterns": [
            r"(magic|enchant|ethereal|mythical|fantast|dreamlike|otherworldly)",
            r"(magical.*world|enchanted.*forest|ethereal.*beauty)",
            r"(mythical.*love|fantastical.*romance|dreamlike.*connection)",
            r"(otherworldly.*bond|fairy.*tale|magical.*moment)"
        ],
        "moods": ["fantasy_magic", "love_devotion", "surprise_excitement"],
        "description": "Magical, fantasy-inspired romantic connection",
        "sentiment_bias": 0.3,
        "emotion_map": {"fantasy_magic": 0.9, "love_devotion": 0.6, "surprise_excitement": 0.5}
    },
    "sensual_intimacy": {
        "feelings": ["sensual", "intimate", "tender", "affectionate", "loving", "close", "connected"],
        "context_patterns": [
            r"(sensual|intimate|tender|affectionate|loving|close|connected)",
            r"(sensual.*touch|intimate.*moment|tender.*caress)",
            r"(affectionate.*gesture|loving.*gaze|close.*connection)",
            r"(connected.*souls|intimate.*whisper|tender.*embrace)"
        ],
        "moods": ["sensual_intimate", "love_devotion", "calm_peaceful"],
        "description": "Deep sensual intimacy and tender connection",
        "sentiment_bias": 0.3,
        "emotion_map": {"sensual_intimate": 0.9, "love_devotion": 0.7, "calm_peaceful": 0.5}
    },
    
    # Conflict & Resolution
    "angry_conflict": {
        "feelings": ["angry", "furious", "betrayed", "hurt", "resentful", "bitter", "frustrated"],
        "context_patterns": [
            r"(angry|furious|betrayed|hurt|resentful|bitter|frustrated)",
            r"(heated.*argument|furious.*outburst|betrayed.*trust)",
            r"(hurt.*feelings|resentful.*heart|bitter.*words)",
            r"(frustrated.*love|angry.*tears|broken.*promises)"
        ],
        "moods": ["angry_intense", "passion_intensity", "sadness_heartbreak"],
        "description": "Angry conflict and emotional turmoil in relationship",
        "sentiment_bias": -0.4,
        "emotion_map": {"angry_intense": 0.9, "passion_intensity": 0.6, "sadness_heartbreak": 0.5}
    },
    "fear_uncertainty": {
        "feelings": ["afraid", "anxious", "nervous", "worried", "apprehensive", "insecure", "vulnerable"],
        "context_patterns": [
            r"(afraid|anxious|nervous|worried|apprehensive|insecure|vulnerable)",
            r"(afraid.*lose|anxious.*heart|nervous.*about)",
            r"(worried.*future|apprehensive.*love|insecure.*feelings)",
            r"(vulnerable.*heart|fear.*abandonment|anxious.*attachment)"
        ],
        "moods": ["fear_anxiety", "longing_yearning", "sadness_heartbreak"],
        "description": "Fear and uncertainty in romantic relationship",
        "sentiment_bias": -0.3,
        "emotion_map": {"fear_anxiety": 0.9, "longing_yearning": 0.5, "sadness_heartbreak": 0.4}
    },
    "surprise_delight": {
        "feelings": ["surprised", "shocked", "amazed", "astonished", "delighted", "thrilled", "stunned"],
        "context_patterns": [
            r"(surprised|shocked|amazed|astonished|delighted|thrilled|stunned)",
            r"(surprise.*proposal|shocked.*revelation|amazed.*discovery)",
            r"(astonished.*love|delighted.*moment|thrilled.*romance)",
            r"(stunned.*beauty|unexpected.*love|surprise.*affection)"
        ],
        "moods": ["surprise_excitement", "joy_happiness", "love_devotion"],
        "description": "Pleasant surprises and delightful romantic moments",
        "sentiment_bias": 0.5,
        "emotion_map": {"surprise_excitement": 0.9, "joy_happiness": 0.7, "love_devotion": 0.5}
    },
    "nostalgic_reflection": {
        "feelings": ["nostalgic", "sentimental", "reminiscent", "bittersweet", "wistful", "melancholy", "reflective"],
        "context_patterns": [
            r"(nostalgic|sentimental|reminiscent|bittersweet|wistful|melancholy|reflective)",
            r"(nostalgic.*memories|sentimental.*journey|reminiscent.*love)",
            r"(bittersweet.*moments|wistful.*thinking|melancholy.*heart)",
            r"(reflective.*mood|past.*love|old.*flames)"
        ],
        "moods": ["nostalgic_memories", "longing_yearning", "sadness_heartbreak"],
        "description": "Nostalgic reflection on past love and memories",
        "sentiment_bias": -0.1,
        "emotion_map": {"nostalgic_memories": 0.9, "longing_yearning": 0.6, "sadness_heartbreak": 0.4}
    }
}

# Common English words for basic validation
COMMON_ENGLISH_WORDS = {
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
    'this', 'that', 'these', 'those', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
    'love', 'like', 'hate', 'want', 'need', 'feel', 'happy', 'sad', 'angry', 'scared',
    'good', 'bad', 'beautiful', 'ugly', 'big', 'small', 'hot', 'cold', 'new', 'old',
    'time', 'day', 'night', 'week', 'month', 'year', 'today', 'tomorrow', 'yesterday'
}

# --- UNIVERSAL EMOTION ANALYZER ---
def analyze_universal_emotions(user_input):
    """Lightweight universal emotion analysis that understands romantic/emotional situations"""
    user_input_lower = user_input.lower()
    
    # Check for nonsense words or gibberish using common English words
    words = user_input_lower.split()
    
    # Calculate the percentage of recognizable words
    if len(words) > 0:
        recognizable_words = sum(1 for word in words if word.strip(".,!?;:'\"") in COMMON_ENGLISH_WORDS)
        word_recognition_ratio = recognizable_words / len(words)
    else:
        word_recognition_ratio = 0
    
    # If input contains mostly nonsense words, return confusion
    if len(words) >= 3 and word_recognition_ratio < 0.3:
        return {
            'situation_name': 'unclear_input',
            'situation_info': {
                'description': "I'm not sure I understand what you're expressing. Could you rephrase that?",
                'dynamic_moods': ['uncertain', 'confused', 'questioning']
            },
            'polarity': 0.0,
            'subjectivity': 0.0,
            'primary_emotion': 'confused',
            'confidence_score': 0,
            'mood_keywords': ['uncertain', 'confused', 'questioning']
        }
    
    # Enhanced sentiment analysis with TextBlob (lightweight)
    blob = TextBlob(user_input)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    
    # Multi-dimensional situation scoring with optimized processing
    situation_scores = {}
    
    # Pre-compile regex patterns for better performance
    compiled_patterns = {}
    for situation, info in emotional_situations.items():
        compiled_patterns[situation] = [re.compile(pattern) for pattern in info['context_patterns']]
    
    for situation, info in emotional_situations.items():
        score = 0.0
        
        # Context pattern matching (highest priority) - optimized
        for pattern in compiled_patterns[situation]:
            try:
                matches = pattern.findall(user_input_lower)
                if matches:
                    score += len(matches) * 10  # Slightly reduced weight for performance
            except:
                continue
        
        # Feeling word matching - optimized with set operations
        feeling_matches = sum(1 for feeling in info['feelings'] if feeling in user_input_lower)
        score += feeling_matches * 5
        
        # Sentiment alignment - simplified calculation
        if abs(polarity) > 0.1:
            if (info['sentiment_bias'] > 0 and polarity > 0) or (info['sentiment_bias'] < 0 and polarity < 0):
                sentiment_adjust = abs(polarity) * 20
                score += sentiment_adjust
        
        # Length bonus - simplified
        word_count = len(user_input.split())
        score += min(15, word_count // 5)  # Capped bonus based on length
        
        situation_scores[situation] = score
    
    # Get best situation with confidence
    best_situation = max(situation_scores, key=situation_scores.get)
    max_score = situation_scores[best_situation]
    
    # Enhanced fallback system for low-confidence inputs
    if max_score < 15:
        # Theme-based fallbacks
        theme_keywords = {
            "flirting_teasing": ["flirt", "tease", "playful", "banter", "charming"],
            "love_devotion": ["devot", "faithful", "commit", "loyal", "soulmate"],
            "passionate_intensity": ["passion", "intense", "fiery", "burning", "electric"],
            "dark_obsessive": ["obsess", "possess", "jealous", "dark", "forbidden"],
            "calm_serenity": ["calm", "peaceful", "serene", "tranquil", "quiet"],
            "longing_desire": ["longing", "yearning", "missing", "wanting", "aching"],
            "joyful_celebration": ["happy", "joy", "celebrate", "bliss", "ecstatic"],
            "heartbreak_loss": ["heartbreak", "broken", "devastated", "loss", "goodbye"],
            "mysterious_intrigue": ["mystery", "secret", "enigmatic", "hidden", "puzzle"],
            "fantasy_magic": ["magic", "fantasy", "enchanted", "mythical", "fairy"],
            "sensual_intimacy": ["sensual", "intimate", "tender", "touch", "close"],
            "angry_conflict": ["angry", "mad", "furious", "betrayed", "argument"],
            "fear_uncertainty": ["afraid", "anxious", "worried", "fear", "nervous"],
            "surprise_delight": ["surprise", "shocked", "unexpected", "delighted", "amazed"],
            "nostalgic_reflection": ["nostalgic", "memories", "past", "remember", "old"]
        }
        
        # Find best theme match
        theme_matches = {}
        for theme, keywords in theme_keywords.items():
            match_count = sum(1 for keyword in keywords if keyword in user_input_lower)
            theme_matches[theme] = match_count
        
        best_theme = max(theme_matches, key=theme_matches.get)
        if theme_matches[best_theme] > 0:
            best_situation = best_theme
        else:
            # Ultimate sentiment fallback
            if polarity > 0.4:
                best_situation = "joyful_celebration"
            elif polarity < -0.4:
                best_situation = "heartbreak_loss"
            elif "love" in user_input_lower or "romance" in user_input_lower:
                best_situation = "love_devotion"
            else:
                best_situation = "calm_serenity"
    
    situation_info = emotional_situations[best_situation]
    
    # Dynamic mood selection based on situation
    primary_moods = []
    for mood_category in situation_info['moods']:
        primary_moods.extend(emotion_to_moods.get(mood_category, []))
    
    # Remove duplicates and limit
    primary_moods = list(dict.fromkeys(primary_moods))[:10]
    
    # Update situation info with dynamic moods
    situation_info['dynamic_moods'] = primary_moods
    
    # Determine primary emotion from situation mapping
    primary_emotion = max(situation_info['emotion_map'], key=situation_info['emotion_map'].get)
    
    return {
        'situation_name': best_situation,
        'situation_info': situation_info,
        'polarity': polarity,
        'subjectivity': subjectivity,
        'primary_emotion': primary_emotion,
        'confidence_score': max_score,
        'mood_keywords': primary_moods
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
    """Search Spotify for tracks based on mood"""
    try:
        sp = get_spotify_client()
        if not sp:
            return []
        
        # Enhanced search term selection
        search_terms = []
        for keyword in mood_keywords[:4]:
            clean_keyword = re.sub(r'[^\w\s]', '', keyword)
            words = clean_keyword.split()
            
            # Prioritize emotional and descriptive terms
            emotional_words = ['love', 'romance', 'heart', 'passion', 'dark', 'forbidden', 
                             'obsessive', 'eternal', 'magical', 'fantasy', 'sensual', 'tender']
            
            for word in words:
                if word in emotional_words or len(word) > 4:
                    search_terms.append(word)
            
            if len(words) <= 3:
                search_terms.append(clean_keyword)
        
        search_terms = list(dict.fromkeys(search_terms))[:4]
        
        if not search_terms:
            search_terms = ["romantic", "love", "emotional"]
        
        # Multiple search strategies
        search_queries = [
            " OR ".join(search_terms),
            " ".join(search_terms[:2]),
            f'"{search_terms[0]}"' if search_terms else "romantic"
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
        
        devices = sp.devices()
        if not devices['devices']:
            return False, "No active Spotify devices found. Please open Spotify on any device."
        
        device_id = devices['devices'][0]['id']
        sp.start_playback(device_id=device_id, uris=[f'spotify:track:{track_id}'])
        return True, "Playing on Spotify"
    
    except Exception as e:
        logger.error(f"Spotify playback error: {e}")
        return False, str(e)

# HTML content remains the same
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dreamers</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #000000;
            color: white;
            min-height: 100vh;
            overflow-x: hidden;
            display: flex;
            flex-direction: column;
        }

        .header {
            text-align: center;
            padding: 20px 0;
            position: sticky;
            top: 0;
            z-index: 10;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(5px);
        }

        h1 {
            font-size: 2.5em;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }

        .subtitle {
            color: #ccc;
            font-size: 1.1em;
        }

        .app-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            flex-grow: 1;
        }

        .background-section {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.9)), 
                        url('https://img.freepik.com/free-photo/digital-art-magical-fairy_23-2151589488.jpg?semt=ais_hybrid&w=740&q=80');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }

        .left-panel {
            display: flex;
            flex-direction: column;
            gap: 20px;
            padding: 20px;
        }

        .input-section {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        #userInput {
            width: 100%;
            padding: 15px;
            background: rgba(0, 0, 0, 0.6);
            border: 2px solid #667eea;
            border-radius: 10px;
            color: white;
            font-size: 16px;
            resize: vertical;
            font-family: inherit;
            min-height: 120px;
            margin-bottom: 15px;
        }

        #userInput:focus {
            outline: none;
            border-color: #764ba2;
            box-shadow: 0 0 15px rgba(102, 126, 234, 0.5);
        }

        .round-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            padding: 12px 25px;
            font-size: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 5px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .round-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        }

        .btn-large {
            padding: 15px 30px;
            font-size: 16px;
            font-weight: 600;
        }

        .btn-spotify {
            background: linear-gradient(135deg, #1DB954 0%, #1ed760 100%);
        }

        .btn-random {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        }

        .mood-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 15px 0;
        }

        .mood-tag {
            background: rgba(102, 126, 234, 0.3);
            color: white;
            border: 1px solid #667eea;
            border-radius: 20px;
            padding: 8px 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 13px;
        }

        .mood-tag:hover {
            background: rgba(102, 126, 234, 0.6);
            transform: translateY(-2px);
        }

        .mood-tag.active {
            background: #667eea;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .right-panel {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            max-height: 85vh;
            overflow-y: auto;
        }

        .playlist-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }

        .playlist-header h2 {
            font-size: 1.6em;
            background: linear-gradient(135deg, #1DB954 0%, #1ed760 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .tracks-count {
            color: #ccc;
            font-style: italic;
            font-size: 0.9em;
        }

        .playlist {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .track-card {
            display: flex;
            align-items: center;
            background: rgba(0, 0, 0, 0.4);
            border-radius: 12px;
            padding: 12px;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .track-card:hover {
            transform: translateY(-2px);
            background: rgba(0, 0, 0, 0.6);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        .track-image {
            width: 50px;
            height: 50px;
            border-radius: 8px;
            margin-right: 12px;
            object-fit: cover;
        }

        .track-info {
            flex: 1;
        }

        .track-name {
            font-weight: 600;
            margin-bottom: 4px;
            color: white;
        }

        .track-artist {
            color: #ccc;
            font-size: 13px;
        }

        .track-actions {
            display: flex;
            gap: 8px;
        }

        .btn-play {
            background: #1DB954;
            color: white;
            border: none;
            border-radius: 15px;
            padding: 6px 12px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.3s ease;
        }

        .btn-play:hover {
            background: #1ed760;
            transform: scale(1.05);
        }

        .btn-preview {
            background: #667eea;
            color: white;
            border: none;
            border-radius: 15px;
            padding: 6px 12px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.3s ease;
        }

        .btn-preview:hover {
            background: #764ba2;
            transform: scale(1.05);
        }

        .audio-preview {
            width: 100%;
            margin-top: 8px;
            border-radius: 8px;
        }

        .loading {
            text-align: center;
            padding: 30px;
        }

        .spinner {
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .status {
            padding: 8px 12px;
            border-radius: 8px;
            margin: 8px 0;
            text-align: center;
            font-size: 14px;
        }

        .status.connected {
            background: rgba(29, 185, 84, 0.2);
            border: 1px solid #1DB954;
            color: #1DB954;
        }

        .status.disconnected {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid #666;
            color: #ccc;
        }

        .error {
            background: rgba(231, 76, 60, 0.2);
            color: #e74c3c;
            padding: 12px;
            border-radius: 8px;
            margin: 8px 0;
            border: 1px solid #e74c3c;
        }

        .analysis-result {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 12px;
            margin: 15px 0;
            border-left: 3px solid #667eea;
        }

        .situation-description {
            font-style: italic;
            color: #ccc;
            margin: 8px 0;
            font-size: 14px;
        }

        .analysis-details {
            font-size: 13px;
            color: #aaa;
            margin-top: 8px;
        }

        @media (max-width: 1024px) {
            .app-container {
                grid-template-columns: 1fr;
                gap: 15px;
            }
            .right-panel {
                max-height: none;
            }
        }

        @media (max-width: 768px) {
            .app-container {
                padding: 10px;
            }
            .header {
                padding: 15px 0;
            }
            h1 {
                font-size: 2em;
            }
            .input-section, .right-panel {
                padding: 15px;
            }
            .track-card {
                flex-direction: column;
                text-align: center;
            }
            .track-image {
                margin-right: 0;
                margin-bottom: 8px;
            }
            .track-actions {
                width: 100%;
                justify-content: center;
                margin-top: 8px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎵 Dreamers</h1>
        <p class="subtitle">Describe your emotions and discover perfect music</p>
    </div>

    <div class="background-section"></div>

    <div class="app-container">
        <div class="left-panel">
            <div class="input-section">
                <button id="connectSpotify" class="round-btn btn-spotify">
                    🔗 Connect Spotify
                </button>
                <div id="spotifyStatus" class="status disconnected">
                    🔒 Connect to play music directly on Spotify
                </div>
            </div>

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
                
                <button id="analyzeBtn" class="round-btn btn-large">
                    🎭 Analyze Emotions & Find Music
                </button>
            </div>

            <div class="input-section">
                <h3>🎯 Mood Tags</h3>
                <div id="moodTags" class="mood-tags">
                </div>
                <p style="color: #ccc; font-size: 14px; margin-top: 10px;">
                    Click on mood tags to refine your search
                </p>
            </div>

            <div class="input-section" style="text-align: center;">
                <button id="randomBtn" class="round-btn btn-large btn-random">
                    🎲 Discover Random Music
                </button>
                <p style="color: #ccc; margin-top: 10px;">
                    Explore music based on random emotional themes
                </p>
            </div>

            <div id="error" class="error" style="display: none;"></div>

            <div id="loading" class="loading" style="display: none;">
                <div class="spinner"></div>
                <p>Analyzing emotions and searching for perfect music...</p>
            </div>
        </div>

        <div class="right-panel">
            <div class="playlist-header">
                <h2>🎵 Your Playlist</h2>
                <div id="tracksCount" class="tracks-count">No tracks yet</div>
            </div>

            <div id="playlist" class="playlist">
                <div style="text-align: center; color: #ccc; padding: 40px;">
                    <p>Your matching songs will appear here</p>
                    <p style="font-size: 14px; margin-top: 10px;">Describe your emotions to get started</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        class EmotionalMusicCompanion {
            constructor() {
                this.currentMoodTags = [];
                this.checkAuthStatus();
                this.bindEvents();
            }

            bindEvents() {
                document.getElementById('connectSpotify').addEventListener('click', () => this.connectSpotify());
                document.getElementById('analyzeBtn').addEventListener('click', () => this.analyzeEmotions());
                document.getElementById('randomBtn').addEventListener('click', () => this.playRandomMusic());
            }

            async checkAuthStatus() {
                try {
                    const response = await fetch('/check-auth');
                    const data = await response.json();
                    
                    const statusElement = document.getElementById('spotifyStatus');
                    if (data.authenticated) {
                        statusElement.innerHTML = '✅ Connected to Spotify';
                        statusElement.className = 'status connected';
                    } else {
                        statusElement.innerHTML = '🔒 Connect to play music directly on Spotify';
                        statusElement.className = 'status disconnected';
                    }
                } catch (error) {
                    console.error('Auth check failed:', error);
                    this.showError('Failed to check Spotify connection');
                }
            }

            async connectSpotify() {
                try {
                    const response = await fetch('/login');
                    const data = await response.json();
                    if (data.auth_url) {
                        window.location.href = data.auth_url;
                    } else {
                        this.showError('Failed to connect to Spotify');
                    }
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
                this.displayMoodTags(data.mood_keywords);
                this.displayTracks(data.spotify_tracks, data.tracks_found);
                document.querySelector('.right-panel').scrollIntoView({ behavior: 'smooth' });
            }

            displayMoodTags(moodKeywords) {
                const moodTagsContainer = document.getElementById('moodTags');
                this.currentMoodTags = moodKeywords || [];
                
                moodTagsContainer.innerHTML = '';
                
                this.currentMoodTags.forEach(mood => {
                    const moodTag = document.createElement('div');
                    moodTag.className = 'mood-tag';
                    moodTag.textContent = mood;
                    moodTag.addEventListener('click', () => {
                        document.getElementById('userInput').value = mood;
                        this.analyzeEmotions();
                    });
                    moodTagsContainer.appendChild(moodTag);
                });
            }

            displayTracks(spotifyTracks, tracksFound) {
                const playlistElement = document.getElementById('playlist');
                const tracksCountElement = document.getElementById('tracksCount');
                
                tracksCountElement.textContent = tracksFound > 0 ? `${tracksFound} tracks found` : 'No tracks yet';
                
                if (spotifyTracks && spotifyTracks.length > 0) {
                    playlistElement.innerHTML = spotifyTracks.map(track => this.createTrackHTML(track)).join('');
                } else {
                    playlistElement.innerHTML = `
                        <div style="text-align: center; color: #ccc; padding: 40px;">
                            <p>No tracks found for this mood</p>
                            <p style="font-size: 14px; margin-top: 10px;">Try describing your emotions differently</p>
                        </div>
                    `;
                }
            }

            createTrackHTML(track) {
                const duration = Math.floor(track.duration_ms / 1000 / 60) + ':' + 
                                String(Math.floor((track.duration_ms / 1000) % 60)).padStart(2, '0');
                
                return `
                    <div class="track-card">
                        ${track.image ? `<img src="${track.image}" alt="${track.name}" class="track-image">` : 
                          '<div class="track-image" style="background: #333; display: flex; align-items: center; justify-content: center; color: #666; font-size: 12px;">No Image</div>'}
                        
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

            async playRandomMusic() {
                const randomMoods = [
                    "romantic love", "heartbreak", "joyful celebration", 
                    "dark passion", "calm serenity", "mysterious intrigue",
                    "nostalgic memories", "playful flirtation", "intense longing"
                ];
                
                const randomMood = randomMoods[Math.floor(Math.random() * randomMoods.length)];
                document.getElementById('userInput').value = randomMood;
                await this.analyzeEmotions();
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
                document.getElementById('randomBtn').disabled = show;
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
                const toast = document.createElement('div');
                toast.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 12px 20px;
                    border-radius: 8px;
                    color: white;
                    font-weight: 600;
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
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dreamers - Spotify Connected</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
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
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    padding: 30px;
                    border-radius: 15px;
                    text-align: center;
                    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
                    max-width: 400px;
                    width: 100%;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                .success {
                    color: #1DB954;
                    font-size: 1.8em;
                    font-weight: 600;
                    margin-bottom: 15px;
                }
                .message {
                    color: #ccc;
                    font-size: 1em;
                    margin-bottom: 20px;
                    line-height: 1.5;
                }
                .btn {
                    background: linear-gradient(135deg, #1DB954 0%, #1ed760 100%);
                    color: white;
                    border: none;
                    padding: 12px 25px;
                    border-radius: 25px;
                    cursor: pointer;
                    font-size: 15px;
                    transition: all 0.3s ease;
                    margin: 5px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                }
                .btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 20px rgba(29, 185, 84, 0.3);
                }
                .btn-secondary {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }
                .btn-secondary:hover {
                    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
                }
                @media (max-width: 768px) {
                    .success-box {
                        padding: 20px;
                        margin: 10px;
                    }
                    .success {
                        font-size: 1.5em;
                    }
                    .message {
                        font-size: 0.9em;
                    }
                    .btn {
                        padding: 10px 20px;
                        font-size: 14px;
                    }
                }
            </style>
        </head>
        <body>
            <div class="success-box">
                <div class="success">✅ Spotify Connected Successfully!</div>
                <p class="message">You're now connected to Dreamers. Return to the app to discover music that matches your emotions.</p>
                <div>
                    <button onclick="window.location.href='/'" class="btn">Return to Dreamers</button>
                    <button onclick="window.close()" class="btn btn-secondary">Close Window</button>
                </div>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Callback error: {e}")
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dreamers - Connection Failed</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
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
                .error-box {
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    padding: 30px;
                    border-radius: 15px;
                    text-align: center;
                    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
                    max-width: 400px;
                    width: 100%;
                    border: 1px solid rgba(231, 76, 60, 0.5);
                }
                .error {
                    color: #e74c3c;
                    font-size: 1.8em;
                    font-weight: 600;
                    margin-bottom: 15px;
                }
                .message {
                    color: #ccc;
                    font-size: 1em;
                    margin-bottom: 20px;
                    line-height: 1.5;
                }
                .btn {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 12px 25px;
                    border-radius: 25px;
                    cursor: pointer;
                    font-size: 15px;
                    transition: all 0.3s ease;
                }
                .btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
                }
                @media (max-width: 768px) {
                    .error-box {
                        padding: 20px;
                        margin: 10px;
                    }
                    .error {
                        font-size: 1.5em;
                    }
                    .message {
                        font-size: 0.9em;
                    }
                    .btn {
                        padding: 10px 20px;
                        font-size: 14px;
                    }
                }
            </style>
        </head>
        <body>
            <div class="error-box">
                <div class="error">❌ Spotify Connection Failed</div>
                <p class="message">Error: {}</p>
                <p class="message">Please try connecting again.</p>
                <button onclick="window.location.href='/'" class="btn">Return to Dreamers</button>
            </div>
        </body>
        </html>
        """.format(str(e))
@app.route('/analyze', methods=['POST'])
def analyze_emotion():
    try:
        user_input = request.json.get('message', '')
        
        if not user_input:
            return jsonify({'error': 'Please provide some text to analyze'})
        
        # Use the universal emotion analyzer
        analysis_result = analyze_universal_emotions(user_input)
        
        # Search Spotify with dynamic mood keywords
        mood_keywords = analysis_result['mood_keywords'][:6]
        spotify_tracks = search_spotify_tracks(mood_keywords)
        
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

