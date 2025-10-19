import os
from flask import Flask, render_template_string, request, redirect, url_for
# Import the Google GenAI SDK for the LLM call
from google import genai
from google.genai.errors import APIError

# -------------------------------------------------------------------------
# Configuration & Client Setup (CRITICAL: Lazy initialization)
# -------------------------------------------------------------------------

# IMPORTANT: Set your API Key as an environment variable (best practice)
# In your terminal, use: export GEMINI_API_KEY="YOUR_API_KEY"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize the Flask application object at the module level (Must be done here)
app = Flask(__name__)

# Global variables to hold the client and readiness state
_GEMINI_CLIENT = None
_GEMINI_READY = None # Will be determined lazily on first access

def get_gemini_client():
    """
    Initializes and returns the Gemini client lazily (only when first called).
    This prevents startup failures if client initialization encounters an error.
    """
    global _GEMINI_CLIENT, _GEMINI_READY
    
    # Return immediately if client status is already known
    if _GEMINI_READY is not None:
        return _GEMINI_CLIENT
        
    # First time calling: attempt initialization
    if GEMINI_API_KEY:
        try:
            # Client initialization
            _GEMINI_CLIENT = genai.Client()
            _GEMINI_READY = True
            print("Gemini client initialized successfully upon first access.")
        except Exception as e:
            _GEMINI_CLIENT = None
            _GEMINI_READY = False
            # Log the error, but the app is still running
            print(f"Error initializing Gemini client at runtime: {e}")
    else:
        _GEMINI_CLIENT = None
        _GEMINI_READY = False
        print("Warning: GEMINI_API_KEY not found. Search will use static mock data.")

    return _GEMINI_CLIENT

# -------------------------------------------------------------------------
# HTML Template Strings
# -------------------------------------------------------------------------

# --- Common Footer Component (for reuse) ---
COMMON_FOOTER = """
    <footer class="mt-12 text-center text-sm text-gray-500">
        <p>MindWork Research & Analysis Tool</p>
        <p>&copy; 2025 Google Gemini</p>
    </footer>
</body>
</html>
"""

# --- Login Page (Uses f-string to inject url_for, which is fine) ---
LOGIN_FORM_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindWork: Login</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .login-card {{
            transition: all 0.3s ease;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }}
        .login-card:hover {{
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            transform: translateY(-2px);
        }}
    </style>
</head>
<body class="bg-indigo-50 min-h-screen flex items-center justify-center font-sans">
    <div class="w-full max-w-md p-4">
        <div class="bg-white p-8 rounded-xl login-card">
            <h2 class="text-3xl font-extrabold text-center text-indigo-700 mb-6">
                MindWork Login
            </h2>
            <form action="{url_for('login')}" method="post">
                <div class="mb-4">
                    <label for="username" class="block text-sm font-medium text-gray-700 mb-1">Username</label>
                    <input type="text" id="username" name="username" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500" required>
                </div>
                <div class="mb-6">
                    <label for="password" class="block text-sm font-medium text-gray-700 mb-1">Password</label>
                    <input type="password" id="password" name="password" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500" required>
                </div>
                <button type="submit" class="w-full bg-indigo-600 text-white font-semibold py-2 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-4 focus:ring-indigo-500 focus:ring-opacity-50 transition duration-150 ease-in-out">
                    Sign In
                </button>
            </form>
            <p class="mt-4 text-sm text-gray-500 text-center">
                This is a mock login page for demonstration purposes.
            </p>
        </div>
    </div>
{COMMON_FOOTER}
"""

# --- Home Page (Search Form) - Uses standard triple quotes for Jinja compatibility ---
HOME_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindWork: Research Hub</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .search-container {
            max-width: 700px;
            padding: 2rem;
            background-color: white;
            border-radius: 1.5rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        .search-container:hover {
            box-shadow: 0 30px 40px -10px rgba(0, 0, 0, 0.15), 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
    </style>
</head>
<body class="bg-gray-50 min-h-screen flex items-center justify-center font-sans">
    <div class="w-full p-4 md:p-8">
        <div class="search-container mx-auto">
            <header class="text-center mb-12">
                <h1 class="text-6xl font-extrabold text-blue-800 tracking-tighter mb-2">
                    MindWork
                </h1>
            </header>

            <form action="/search" method="get" class="flex flex-col space-y-4">
                <div class="flex items-center border-2 border-blue-300 rounded-full bg-white shadow-lg focus-within:ring-4 focus-within:ring-blue-200 transition duration-300">
                    <input type="search" name="query" placeholder="Ask Gemini a research question..." 
                           class="flex-grow px-6 py-4 text-lg text-gray-700 bg-transparent focus:outline-none rounded-l-full"
                           required>
                    <button type="submit" class="bg-blue-600 text-white p-4 rounded-full hover:bg-blue-700 transition duration-150 ease-in-out focus:outline-none focus:ring-4 focus:ring-blue-400 m-1">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </button>
                </div>
            </form>
            
            <div class="mt-8 text-center">
                <a href="/capture" class="text-blue-600 hover:text-blue-800 font-medium transition duration-150 text-lg flex items-center justify-center space-x-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.218A2 2 0 0110.69 4h2.62a2 2 0 011.664.89l.812 1.218A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <span>Analyze an Image (Take Photo)</span>
                </a>
            </div>

            {% set active_client = get_gemini_client() %}
            {% if active_client is none and GEMINI_API_KEY %}
            <div class="mt-8 p-4 bg-red-100 border border-red-400 text-red-800 rounded-lg text-sm text-center">
                ❌ **Gemini API Error:** The client failed to initialize at runtime. Check server logs for details.
            </div>
            {% elif active_client is none %}
            <div class="mt-8 p-4 bg-yellow-100 border border-yellow-400 text-yellow-800 rounded-lg text-sm text-center">
                ⚠️ **Gemini API Key Missing:** The search results will use static mock data. Set your `GEMINI_API_KEY` environment variable to enable AI features.
            </div>
            {% endif %}
        </div>
    </div>
""" + COMMON_FOOTER # Append the common footer here

# --- Camera Capture Page ---
CAPTURE_PHOTO_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindWork: Image Capture</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .video-container {
            width: 100%;
            max-width: 600px;
            margin: 0 auto;
            aspect-ratio: 4/3; /* Standard camera aspect ratio */
            background-color: #333;
            border-radius: 1rem;
            overflow: hidden;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        #video-stream {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: none; /* Hidden until stream starts */
        }
        #canvas {
            display: none; /* Canvas is hidden by default */
        }
    </style>
</head>
<body class="bg-gray-50 min-h-screen font-sans p-4">
    <div class="container mx-auto max-w-4xl">
        <header class="mb-8 flex items-center justify-between">
            <a href="/" class="text-3xl font-extrabold text-blue-800 tracking-tighter hover:text-blue-600 transition duration-150">
                MindWork
            </a>
            <h1 class="text-xl font-semibold text-gray-700 hidden sm:block">
                Capture Image for Analysis
            </h1>
        </header>

        <div class="text-center mb-6">
            <p id="status-message" class="text-gray-600">Camera not started.</p>
        </div>

        <!-- Video and Canvas Container -->
        <div class="video-container relative">
            <video id="video-stream" autoplay playsinline></video>
            <canvas id="canvas" class="w-full h-full object-cover"></canvas>
            <!-- Overlay text when camera is off -->
            <div id="camera-off-overlay" class="absolute inset-0 flex items-center justify-center bg-gray-700 text-white transition-opacity">
                <span class="text-lg font-medium">Click "Start Camera" to begin</span>
            </div>
        </div>

        <!-- Controls -->
        <div class="flex flex-wrap justify-center gap-4 mt-6">
            <button id="start-stop-btn" class="bg-green-600 text-white font-semibold px-6 py-3 rounded-xl shadow-md hover:bg-green-700 transition duration-150">
                Start Camera
            </button>
            <button id="toggle-camera-btn" disabled class="bg-indigo-600 text-white font-semibold px-6 py-3 rounded-xl shadow-md hover:bg-indigo-700 transition duration-150 disabled:bg-indigo-300">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 inline-block mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Toggle Camera (Front/Back)
            </button>
            <button id="capture-btn" disabled class="bg-blue-600 text-white font-semibold px-6 py-3 rounded-xl shadow-md hover:bg-blue-700 transition duration-150 disabled:bg-blue-300">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 inline-block mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.218A2 2 0 0110.69 4h2.62a2 2 0 011.664.89l.812 1.218A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Take Photo
            </button>
        </div>
        
        <!-- Captured Image Preview & Download Button -->
        <div id="preview-area" class="mt-8 p-4 bg-white rounded-xl shadow-lg" style="display:none;">
            <h2 class="text-xl font-bold text-gray-800 mb-4">Captured Image</h2>
            <div class="flex flex-col sm:flex-row gap-4 items-center">
                <img id="image-preview" class="w-full sm:w-1/2 rounded-lg shadow-md max-h-64 object-contain" alt="Captured Image Preview">
                <a id="download-btn" download="mindwork-capture.png" class="bg-gray-700 text-white font-semibold px-6 py-3 rounded-xl shadow-md hover:bg-gray-800 transition duration-150 cursor-pointer">
                    Download Image
                </a>
            </div>
        </div>

    </div>

    <script>
        const video = document.getElementById('video-stream');
        const canvas = document.getElementById('canvas');
        const startStopBtn = document.getElementById('start-stop-btn');
        const captureBtn = document.getElementById('capture-btn');
        const toggleCameraBtn = document.getElementById('toggle-camera-btn');
        const statusMessage = document.getElementById('status-message');
        const cameraOffOverlay = document.getElementById('camera-off-overlay');
        const previewArea = document.getElementById('preview-area');
        const imagePreview = document.getElementById('image-preview');
        const downloadBtn = document.getElementById('download-btn');
        
        let currentStream = null;
        // Default to the front camera (user) but flip to back (environment) if available
        let currentFacingMode = 'user'; 

        // Utility to display status messages
        function updateStatus(message, color = 'gray-600') {
            statusMessage.textContent = message;
            statusMessage.className = \`text-\${color}\`;
        }

        // Stops the current camera stream
        function stopCamera() {
            if (currentStream) {
                currentStream.getTracks().forEach(track => track.stop());
                currentStream = null;
            }
            video.style.display = 'none';
            cameraOffOverlay.style.opacity = '1';
            startStopBtn.textContent = 'Start Camera';
            startStopBtn.classList.remove('bg-red-600', 'hover:bg-red-700');
            startStopBtn.classList.add('bg-green-600', 'hover:bg-green-700');
            captureBtn.disabled = true;
            toggleCameraBtn.disabled = true;
            updateStatus('Camera stopped.');
        }

        // Starts the camera stream with the selected facing mode
        async function startCamera(facingMode = currentFacingMode) {
            stopCamera(); // Stop any existing stream first
            currentFacingMode = facingMode;
            updateStatus('Requesting camera access...', 'yellow-600');

            // Set constraints for video, prioritizing the desired facingMode
            const constraints = {
                video: {
                    // This is the key line for camera switching
                    facingMode: currentFacingMode
                },
                audio: false
            };

            try {
                const stream = await navigator.mediaDevices.getUserMedia(constraints);
                currentStream = stream;
                video.srcObject = stream;
                video.style.display = 'block';
                cameraOffOverlay.style.opacity = '0';
                
                // Once stream is loaded, set canvas size to match video resolution
                video.onloadedmetadata = () => {
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                };

                startStopBtn.textContent = 'Stop Camera';
                startStopBtn.classList.remove('bg-green-600', 'hover:bg-green-700');
                startStopBtn.classList.add('bg-red-600', 'hover:bg-red-700');
                captureBtn.disabled = false;
                toggleCameraBtn.disabled = false;
                updateStatus(\`Camera started (\${currentFacingMode === 'user' ? 'Front' : 'Back'})\`, 'green-600');
            } catch (err) {
                console.error("Error accessing the camera: ", err);
                stopCamera();
                updateStatus('Camera access denied or device not found.', 'red-600');
            }
        }

        // Toggles between front and back camera
        async function toggleCamera() {
            const newMode = currentFacingMode === 'user' ? 'environment' : 'user';
            await startCamera(newMode);
        }

        // Captures a photo to the canvas
        function capturePhoto() {
            if (!currentStream) {
                updateStatus('Camera is not running.', 'red-600');
                return;
            }

            const context = canvas.getContext('2d');
            
            // Draw the current video frame onto the canvas
            context.drawImage(video, 0, 0, canvas.width, canvas.height);

            // Convert canvas content to image data URL
            const dataUrl = canvas.toDataURL('image/png');
            
            // Show preview and download button
            imagePreview.src = dataUrl;
            downloadBtn.href = dataUrl;
            previewArea.style.display = 'block';
            
            updateStatus('Photo captured! Scroll down to see the preview.', 'blue-600');
        }

        // Event Listeners
        startStopBtn.addEventListener('click', () => {
            if (currentStream) {
                stopCamera();
            } else {
                startCamera();
            }
        });

        toggleCameraBtn.addEventListener('click', toggleCamera);
        captureBtn.addEventListener('click', capturePhoto);

        // Ensure camera stops when navigating away from the page
        window.addEventListener('beforeunload', stopCamera);
        
    </script>
    
    <!-- Appending the common footer -->
    """ + COMMON_FOOTER
# -------------------------------------------------------------------------
# Utility Functions (Remain unchanged)
# -------------------------------------------------------------------------

def generate_gemini_result(client, query):
    """
    Calls the Gemini API to get a grounded answer for the query.
    """
    try:
        # We use the 'google_search' tool to ensure the results are grounded
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Provide a concise, detailed, and well-structured research summary for the query: '{query}'. Start with a clear title.",
            config={"tools": [{"google_search": {}}]}
        )
        
        # Check for grounding metadata to find the source URL
        source_url = None
        if response.candidates and response.candidates[0].grounding_metadata:
            # Safely extract the first available web URI
            attribution = response.candidates[0].grounding_metadata.grounding_attributions
            if attribution and attribution[0].web and attribution[0].web.uri:
                source_url = attribution[0].web.uri

        # Extract title and summary from the generated text
        text_content = response.text.strip()
        lines = text_content.split('\n', 2)
        
        title = lines[0].strip(' *#') # Clean up markdown formatting
        summary = text_content
        
        if len(lines) > 1:
            summary = "\n".join(lines[1:]).strip()
            if not summary:
                 summary = text_content # Fallback

        return {
            'title': title,
            'summary': summary,
            'url': source_url,
            'source': 'Gemini'
        }
    except APIError as e:
        print(f"Gemini API Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during Gemini call: {e}")
        return None

# -------------------------------------------------------------------------
# Flask Routes (Added /capture route)
# -------------------------------------------------------------------------

@app.route('/')
def home():
    """Renders the home page with the search form."""
    # We call get_gemini_client() here to trigger the lazy initialization
    client = get_gemini_client()
    gemini_active = client is not None
    # Pass get_gemini_client and GEMINI_API_KEY to the template for the status check display
    return render_template_string(HOME_HTML, get_gemini_client=get_gemini_client, GEMINI_API_KEY=GEMINI_API_KEY)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles mock login. On POST, redirects to the home page (simulating successful login).
    """
    if request.method == 'POST':
        # Mock login logic (in a real app, this would validate credentials)
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Mock Login Attempt: User={username}, Pass={'*' * len(password)}")
        # Redirect to the home page on "success"
        return redirect(url_for('home'))
        
    # On GET request, show the login form
    return render_template_string(LOGIN_FORM_HTML)


@app.route('/search', methods=['GET'])
# Using the original SEARCH_RESULTS_HTML defined in the previous exchange.
# (Note: For brevity, I've omitted the unchanged SEARCH_RESULTS_HTML here, but assume it's correctly defined in the full app).
# ...
def search():
    """
    Handles the search query, calls Gemini, and renders the results page.
    """
    # ... (search logic remains unchanged)
    
    query = request.args.get('query', '').strip()
    if not query:
        return redirect(url_for('home'))

    # Retrieve the client, triggering initialization if needed
    client = get_gemini_client()
    gemini_active = client is not None
    
    gemini_result = None
    if gemini_active:
        # Call Gemini for the research summary
        gemini_result = generate_gemini_result(client, query)

    all_results = [gemini_result] if gemini_result else []
    
    # Ensure a maximum of 1 result is displayed (the Gemini result)
    final_results = all_results[:1]

    # Re-using the SEARCH_RESULTS_HTML logic from the previous turn for completeness
    SEARCH_RESULTS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindWork: Results for "{{ query }}"</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .result-card {
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            position: relative; 
            cursor: pointer; 
        }
        .result-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 25px -5px rgba(0, 0, 0, 0.1), 0 5px 10px -5px rgba(0, 0, 0, 0.04);
        }
        .ai-card {
            border-left: 6px solid #1E40AF; 
            background-color: #F0F9FF;
        }
    </style>
</head>
<body class="bg-gray-50 min-h-screen font-sans">
    <div class="container mx-auto p-4 md:p-8">
        
        <header class="mb-8 flex items-center justify-between">
            <a href="/" class="text-3xl font-extrabold text-blue-800 tracking-tighter hover:text-blue-600 transition duration-150">
                MindWork
            </a>
            <form action="/search" method="get" class="w-2/3 max-w-xl hidden md:flex">
                <input type="search" name="query" value="{{ query }}" placeholder="Search again..." 
                       class="flex-grow px-4 py-2 border border-gray-300 rounded-l-lg focus:ring-blue-500 focus:border-blue-500 text-gray-700"
                       required>
                <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded-r-lg hover:bg-blue-700 transition duration-150">
                    Search
                </button>
            </form>
        </header>

        <h2 class="text-2xl font-semibold text-gray-800 mb-6">
            Search Results for: <span class="text-blue-600">"{{ query }}"</span>
        </h2>
        
        {% if not gemini_active %}
        <div class="mb-6 p-4 bg-red-100 border border-red-400 text-red-800 rounded-lg text-sm">
            ❌ **API Inactive:** Gemini is not active. Results may be limited.
        </div>
        {% endif %}

        <div class="space-y-8">
            {% if results %}
                {% set featured_ai_result = results[0] %}
                
                {% if featured_ai_result and featured_ai_result.source == 'Gemini' %}
                    
                    {% if featured_ai_result.url %}
                        <a href="{{ featured_ai_result.url }}" target="_blank" class="block no-underline">
                    {% endif %}

                    <div class="p-6 rounded-xl shadow-lg result-card ai-card group">
                        <div class="flex items-center mb-3">
                            <span class="px-3 py-1 bg-blue-600 text-white text-xs font-bold rounded-full mr-3">
                                GEMINI AI
                            </span>
                            <h3 class="text-2xl font-bold text-gray-800 group-hover:text-blue-700 transition duration-150">
                                {{ featured_ai_result.title }}
                            </h3>
                        </div>
                        <p class="text-gray-700 whitespace-pre-wrap leading-relaxed">{{ featured_ai_result.summary }}</p>
                        
                        {% if featured_ai_result.url %}
                            <div class="mt-4 flex justify-start items-center space-x-2">
                                <button class="bg-blue-500 text-white text-sm font-semibold px-4 py-2 rounded-lg shadow-md hover:bg-blue-600 transition duration-150 flex items-center">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                                        <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V3h-6z" />
                                        <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                                    </svg>
                                    View Source Article
                                </button>
                                <span class="text-xs text-gray-500 truncate max-w-xs md:max-w-md">
                                    {{ featured_ai_result.url | replace('https://', '') | replace('http://', '') }}
                                </span>
                            </div>
                        {% endif %}
                    </div>
                    
                    {% if featured_ai_result.url %}
                        </a>
                    {% endif %}


                {% else %}
                    <div class="p-6 rounded-xl shadow-lg result-card bg-white">
                         <h3 class="text-xl font-bold text-gray-800 mb-2">No Featured AI Result</h3>
                         <p class="text-gray-600">Your query did not return a featured AI result, or the Gemini API is inactive. Please try another query.</p>
                    </div>
                {% endif %}

            {% else %}
                <div class="p-6 rounded-xl shadow-lg bg-white">
                    <p class="text-lg text-gray-600 text-center">No results found for your query. Please try searching for something else.</p>
                </div>
            {% endif %}
        </div>
    </div>
""" + COMMON_FOOTER
    
    return render_template_string(
        SEARCH_RESULTS_HTML,
        query=query,
        results=final_results,
        gemini_active=gemini_active # Pass the local state
    )

@app.route('/capture')
def capture():
    """Renders the photo capture page with camera access."""
    return render_template_string(CAPTURE_PHOTO_HTML)


# -------------------------------------------------------------------------
# Application Run (Local Development Only)
# -------------------------------------------------------------------------

if __name__ == '__main__':
    # Print status check when running locally
    initial_client = get_gemini_client()
    initial_ready = initial_client is not None
    print("----------------------------------------------------------")
    print("Flask Application Running Locally (Development Server):")
    print(f"Gemini Status: {'✅ Active' if initial_ready else '❌ Inactive (Set GEMINI_API_KEY)'}")
    print("----------------------------------------------------------")
    # Use Flask's built-in development server
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
