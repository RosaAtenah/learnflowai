
# PDF validation

MAX_FILE_SIZE_MB = 10      
ZONE1_PAGES = 30          
ZONE2_PAGES = 50           
MIN_TEXT_LENGTH = 100       

# Chunking

CHUNK_SIZE = 700           
CHUNK_OVERLAP = 70        
                            
# QCM generation

MAX_QUESTIONS = 20          
DEFAULT_QUESTIONS = 5       


# SRS engine (SM-2)
DEFAULT_EASINESS = 2.5      
MIN_EASINESS = 1.3          

INTERVAL_AGAIN = 1          
INTERVAL_HARD  = 1          
INTERVAL_GOOD  = 3         
INTERVAL_EASY  = 7         


# LLM API

# MODEL_PROVIDER = "gemini"
# MODEL   = "gemini-2.0-flash"

MODEL_PROVIDER = "groq"
MODEL = "llama-3.1-8b-instant"

MAX_RETRIES = 3       
API_TIMEOUT = 30

DEFAULT_LANGUE = "English"   

BASE_MIN_QUESTIONS = 5