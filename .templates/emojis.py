"""
Emoji constants for use in console output and logging.
Makes logs more readable and visually distinguishable.
"""

# Process States
STATE_START = "🔹"       # Starting a process or general information
STATE_RUNNING = "⏳"     # Process is running/in progress
STATE_SUCCESS = "✅"      # Success / Completed
STATE_WARNING = "⚠️"      # Warning - minor issue but continuing
STATE_ERROR = "❌"        # Error / Failed 
STATE_RETRY = "🔄"       # Retrying or refreshing

# Data Operations
DATA_SEARCH = "🔍"       # Search operation
DATA_SAVE = "💾"         # Saving data
DATA_LOAD = "📂"         # Loading from file/folder
DATA_UPLOAD = "📤"       # Uploading/exporting data
DATA_DOWNLOAD = "📥"     # Downloading/importing data
DATA_BUILD = "🔨"        # Building or constructing data
DATA_ANALYZE = "📊"      # Data analysis
DATA_DELETE = "🗑️"       # Deleting data

# AI and Models
AI_BRAIN = "🧠"          # AI model operations
AI_TRAIN = "🏋️"          # Training a model
AI_INFER = "🔮"          # Inference/prediction
AI_EVAL = "🎯"           # Evaluation/metrics
AI_EMBEDDINGS = "🧩"     # Embeddings/vectors

# System
SYS_CONFIG = "🔧"        # Configuration or setup
SYS_PERF = "🚀"          # Performance improvement or fast operation
SYS_SECURITY = "🔒"      # Security operations
SYS_MEMORY = "🧠"        # Memory operations
SYS_CPU = "⚙️"           # CPU operations
SYS_GPU = "🖥️"           # GPU operations
SYS_TIME = "⏱️"           # Timing information

# Networking
NET_API = "🌐"           # API or web service
NET_REQUEST = "📡"       # Making a request
NET_RESPONSE = "📨"      # Receiving a response
NET_SERVER = "🖧"        # Server operations
NET_DATABASE = "🗄️"      # Database operations

# Files and Storage
FILE_CREATE = "📝"       # Creating a file
FILE_READ = "👓"         # Reading a file
FILE_WRITE = "✍️"        # Writing to a file
FILE_FOLDER = "📁"       # Folder operations
FILE_ZIP = "🗜️"          # Compression/archiving

# Specialty for Patents
PATENT_SEARCH = "🔎"     # Patent search
PATENT_DOCUMENT = "📄"   # Patent document
PATENT_LEGAL = "⚖️"      # Legal aspects
PATENT_INNOVATION = "💡" # Innovation/invention

# Number emojis (keycap and encircled)
NUM_1 = "1️⃣ "  # Keycap 1
NUM_2 = "2️⃣ "  # Keycap 2 
NUM_3 = "3️⃣ "  # Keycap 3
NUM_4 = "4️⃣ "  # Keycap 4
NUM_5 = "5️⃣ "  # Keycap 5
NUM_6 = "6️⃣ "  # Keycap 6
NUM_7 = "7️⃣ "  # Keycap 7
NUM_8 = "8️⃣ "  # Keycap 8
NUM_9 = "9️⃣ "  # Keycap 9
NUM_10 = "🔟 "  # Keycap 10

# Examples of usage
EXAMPLES = {
    "initialization": f"{STATE_START} Initializing application...",
    "model_loading": f"{STATE_RUNNING} Loading model from disk...",
    "success": f"{STATE_SUCCESS} Operation completed successfully",
    "warning": f"{STATE_WARNING} Missing optional configuration",
    "error": f"{STATE_ERROR} Failed to connect to database",
    "ai_operation": f"{AI_BRAIN} Processing query with LLM...",
    "data_save": f"{DATA_SAVE} Saving FAISS index to disk...",
    "patent_search": f"{PATENT_SEARCH} Searching for similar patents..."
}

def print_examples():
    """Print examples of emoji usage"""
    print("\nEmoji Usage Examples:")
    print("-" * 50)
    for name, example in EXAMPLES.items():
        print(f"{name.ljust(20)}: {example}")

if __name__ == "__main__":
    # When run directly, this will show all available emojis with examples
    print("\nAvailable Emojis by Category:")
    print("-" * 50)
    
    print(f"{NUM_1} Searching text fields in parquet_patents...")
    print(f"{NUM_2} Fetching spif_publication_number from google_patents_us...")
    print(f"{NUM_3} Building final results...")

    # Print process states
    print("Process States:")
    print(f"{STATE_START} STATE_START - Starting a process")
    print(f"{STATE_RUNNING} STATE_RUNNING - Process in progress")
    print(f"{STATE_SUCCESS} STATE_SUCCESS - Process completed successfully")
    print(f"{STATE_WARNING} STATE_WARNING - Warning occurred")
    print(f"{STATE_ERROR} STATE_ERROR - Error occurred")
    print(f"{STATE_RETRY} STATE_RETRY - Retrying operation\n")
    
    # Print data operations
    print("Data Operations:")
    print(f"{DATA_SEARCH} DATA_SEARCH - Search operation")
    print(f"{DATA_SAVE} DATA_SAVE - Saving data")
    print(f"{DATA_LOAD} DATA_LOAD - Loading data")
    print(f"{DATA_ANALYZE} DATA_ANALYZE - Analyzing data\n")
    
    # Print AI operations
    print("AI Operations:")
    print(f"{AI_BRAIN} AI_BRAIN - AI model operations")
    print(f"{AI_TRAIN} AI_TRAIN - Training a model")
    print(f"{AI_INFER} AI_INFER - Model inference")
    print(f"{AI_EMBEDDINGS} AI_EMBEDDINGS - Working with embeddings\n")
    
    # Print system operations
    print("System Operations:")
    print(f"{SYS_CONFIG} SYS_CONFIG - Configuration")
    print(f"{SYS_PERF} SYS_PERF - Performance optimization")
    print(f"{SYS_GPU} SYS_GPU - GPU operations\n")
    
    # Print patent operations
    print("Patent Operations:")
    print(f"{PATENT_SEARCH} PATENT_SEARCH - Patent search")
    print(f"{PATENT_DOCUMENT} PATENT_DOCUMENT - Patent document")
    print(f"{PATENT_INNOVATION} PATENT_INNOVATION - Innovation/invention\n")
    
    # Print usage examples
    print_examples()