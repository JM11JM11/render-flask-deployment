import os
import random
from flask import Flask, render_template_string, request, redirect, url_for
# Import the Google GenAI SDK for the LLM call
from google import genai
from google.genai.errors import APIError
from waitress import serve as waitress_serve # Rename to avoid conflict with 'serve()' function

# -------------------------------------------------------------------------
# Configuration & Client Setup (Refactored for faster startup)
# -------------------------------------------------------------------------

# IMPORTANT: Set your API Key as an environment variable (best practice)
# In your terminal, use: export GEMINI_API_KEY="YOUR_API_KEY"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)

# Global variables to hold the client and readiness state
_GEMINI_CLIENT = None
_GEMINI_READY = None # Will be determined lazily

def get_gemini_client():
    """
    Initializes and returns the Gemini client lazily (only when first called).
    This speeds up the application's startup time significantly.
    """
    global _GEMINI_CLIENT, _GEMINI_READY
    
    # Check if we've already tried to initialize it
    if _GEMINI_READY is not None:
        return _GEMINI_CLIENT
        
    # First time calling: attempt initialization
    if GEMINI_API_KEY:
        try:
            # The client setup might involve network checks or configuration loading.
            _GEMINI_CLIENT = genai.Client()
            _GEMINI_READY = True
            # Print success message only once upon first use or explicit check
            print("Gemini client initialized successfully.")
        except Exception as e:
            _GEMINI_CLIENT = None
            _GEMINI_READY = False
            print(f"Error initializing Gemini client: {e}")
    else:
        _GEMINI_CLIENT = None
        _GEMINI_READY = False
        # Only print warning if key is missing and we haven't already
        # printed it (controlled by _GEMINI_READY)
        if _GEMINI_READY is None:
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
                <!-- Removed "General Research Hub" text here -->
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
            
            {% if not gemini_active %}
            <div class="mt-8 p-4 bg-yellow-100 border border-yellow-400 text-yellow-800 rounded-lg text-sm text-center">
                ⚠️ **Gemini API Key Missing:** The search results will use static mock data. Set your `GEMINI_API_KEY` environment variable to enable AI features.
            </div>
            {% endif %}
        </div>
    </div>
""" + COMMON_FOOTER # Append the common footer here

# --- Search Results Page - Uses standard triple quotes for Jinja compatibility ---
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
        }
        .result-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 25px -5px rgba(0, 0, 0, 0.1), 0 5px 10px -5px rgba(0, 0, 0, 0.04);
        }
        .ai-card {
            border-left: 6px solid #1E40AF; /* Blue-800 */
            background-color: #F0F9FF; /* Blue-50 */
        }
    </style>
</head>
<body class="bg-gray-50 min-h-screen font-sans">
    <div class="container mx-auto p-4 md:p-8">
        
        <!-- Header & Search Bar -->
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
            ❌ **API Inactive:** Gemini could not be initialized. No AI results generated.
        </div>
        {% endif %}

        <div class="space-y-8">
            {% if results %}
                {% set featured_ai_result = results[0] %}
                
                <!-- FEATURED AI RESULT (Always the first one if present) -->
                {% if featured_ai_result and featured_ai_result.source == 'Gemini' %}
                    <div class="p-6 rounded-xl shadow-lg result-card ai-card">
                        <div class="flex items-center mb-3">
                            <span class="px-3 py-1 bg-blue-600 text-white text-xs font-bold rounded-full mr-3">
                                GEMINI AI
                            </span>
                            <h3 class="text-2xl font-bold text-gray-800">{{ featured_ai_result.title }}</h3>
                        </div>
                        <p class="text-gray-700 whitespace-pre-wrap leading-relaxed">{{ featured_ai_result.summary }}</p>
                        {% if featured_ai_result.url %}
                            <a href="{{ featured_ai_result.url }}" target="_blank" class="mt-4 inline-block text-blue-600 hover:text-blue-800 font-medium text-sm transition duration-150">
                                View Source: {{ featured_ai_result.url }}
                            </a>
                        {% endif %}
                    </div>

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
""" + COMMON_FOOTER # Append the common footer here

# -------------------------------------------------------------------------
# Utility Functions
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
# Flask Routes
# -------------------------------------------------------------------------

@app.route('/')
def home():
    """Renders the home page with the search form."""
    client = get_gemini_client()
    gemini_active = client is not None
    # Pass gemini_active to HOME_HTML to show the API warning if needed
    return render_template_string(HOME_HTML, gemini_active=gemini_active)


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
def search():
    """
    Handles the search query, calls Gemini, and renders the results page.
    """
    query = request.args.get('query', '').strip()
    if not query:
        return redirect(url_for('home'))

    client = get_gemini_client()
    gemini_active = client is not None
    
    gemini_result = None
    if gemini_active:
        # Call Gemini for the research summary
        gemini_result = generate_gemini_result(client, query)

    # all_results now only contains the single Gemini result, or is empty.
    all_results = [gemini_result] if gemini_result else []
    
    # Ensure a maximum of 1 result is displayed (the Gemini result)
    final_results = all_results[:1]

    return render_template_string(
        SEARCH_RESULTS_HTML,
        query=query,
        results=final_results,
        gemini_active=gemini_active # Pass the local state
    )


# -------------------------------------------------------------------------
# Deployment and Application Run (Modified)
# -------------------------------------------------------------------------

def serve_app():
    """Function to serve the app using Waitress for deployment."""
    # Check the final readiness state before serving
    initial_client = get_gemini_client()
    initial_ready = initial_client is not None
    print("----------------------------------------------------------")
    print("Flask Application Starting:")
    print(f"Gemini Status: {'✅ Active' if initial_ready else '❌ Inactive (Set GEMINI_API_KEY)'}")
    print("----------------------------------------------------------")
    
    # Waitress is used here to serve the application in a production-like way
    waitress_serve(app, host='0.0.0.0', port=os.environ.get('PORT', 5000))

if __name__ == '__main__':
    # When running locally via 'python app.py'
    serve_app()
