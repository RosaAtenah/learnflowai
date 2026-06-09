# config/settings.py


# PDF validation

MAX_FILE_SIZE_MB = 10       # Maximum file size in MB
                            # Reason : avoids memory overload on free hosting

ZONE1_PAGES = 30          

ZONE2_PAGES = 50           

MIN_TEXT_LENGTH = 100       

# Chunking

CHUNK_SIZE = 2000           # Tokens per chunk
                           

CHUNK_OVERLAP = 150         # Overlapping tokens between chunks
                            
# QCM generation

MAX_QUESTIONS = 20          # Hard ceiling on number of questions
                           

DEFAULT_QUESTIONS = 5       # Default value shown in the slider


# SRS engine (SM-2)

DEFAULT_EASINESS = 2.5      # Initial easiness factor for all cards

MIN_EASINESS = 1.3          # Minimum easiness factor (SM-2 standard)

INTERVAL_AGAIN = 1          
INTERVAL_HARD  = 1          
INTERVAL_GOOD  = 3         
INTERVAL_EASY  = 7         


# LLM API

# MODEL_PROVIDER = "gemini"
# MODEL   = "gemini-2.0-flash"
#                             # Reason : free on Hugging Face, good instruction

MODEL_PROVIDER = "groq"
MODEL = "llama-3.1-8b-instant"

MAX_RETRIES = 3       # 3 tentatives au lieu de 2
API_TIMEOUT = 30

# UI

DEFAULT_LANGUE = "English"   # Default language for summary and QCM

BASE_MIN_QUESTIONS = 5