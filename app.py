import os
import random
import re
from flask import Flask, render_template_string, request, redirect, url_for
from google import genai
from google.genai.errors import APIError

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------

# IMPORTANT: Set your API Key as an environment variable (best practice)
# In your terminal, use: export GEMINI_API_KEY="YOUR_API_KEY"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)

# Initialize the Gemini Client
client = None
GEMINI_CLIENT_READY = False
if GEMINI_API_KEY:
    try:
        client = genai.Client()
        GEMINI_CLIENT_READY = True
        print("Gemini client initialized successfully.")
    except Exception as e:
        print(f"Error initializing Gemini client: {e}")
else:
    print("Warning: GEMINI_API_KEY not found. Search will use static mock data.")

# Global contact email
CONTACT_EMAIL = "Mesadieujohnm01@gmail.com"

# Global list to hold mock results temporarily for the /article route
# WARNING: This is NOT safe for production! It can fail in multi-threaded environments.
MOCK_RESULT_CACHE = {} 


# -------------------------------------------------------------------------
# HTML Template Components
# -------------------------------------------------------------------------

BASE_HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Gemini Research Mock</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
    <style>
        body { background-color: #f8f9fa; }
        .navbar { background-color: #3f51b5 !important; }
        .navbar-brand, .nav-link { color: #ffffff !important; }
        .card-result { margin-bottom: 1.5rem; border: 1px solid #dee2e6; box-shadow: 0 0.5rem 1rem rgba(0,0,0,.05); }
        .card-result:hover { box-shadow: 0 0.75rem 1.5rem rgba(0,0,0,.1); }
        .footer-copyright { background-color: rgba(0, 0, 0, 0.05); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark fixed-top">
        <div class="container">
            <a class="navbar-brand" href="/">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-gem me-2" viewBox="0 0 16 16">
                    <path d="M3.197 3.639L5.344.606A.525.525 0 0 1 6.1.488l2.642 1.94c.373.273.475.76.24 1.135L6.37 8.016 3.197 3.639zm6.815 0L6.37 8.016l2.527 3.593a.524.524 0 0 0 .736.195l2.457-1.782c.38-.277.485-.772.25-1.157L9.948 3.639zM.795 6.649a.525.525 0 0 1 .49-.444h3.916c.49 0 .89.34.89.75v3.136a.75.75 0 0 1-.75.75H.913a.525.525 0 0 1-.49-.444L.795 6.649zm14.41 0a.525.525 0 0 0-.49-.444h-3.916c-.49 0-.89.34-.89.75v3.136a.75.75 0 0 0 .75.75h4.156a.525.525 0 0 0 .49-.444l-.266-3.75z"/>
                </svg>
                Gemini Research Mock
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="/">Home</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="mailto:{{ CONTACT_EMAIL }}">Contact</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
    <main class="container" style="padding-top: 5rem; padding-bottom: 4rem;">
        {% block content %}{% endblock %}
    </main>
    <footer class="bg-dark text-center text-white fixed-bottom">
        <div class="container p-1">
            <section class="mb-1">
                <small>Disclaimer: This is a mock-up application to demonstrate research-style results using the Gemini API.</small>
            </section>
        </div>
        <div class="text-center p-2 footer-copyright">
            © 2025 Copyright: <a class="text-white" href="/">Gemini Research Mock</a>
        </div>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
</body>
</html>
"""

INDEX_PAGE_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
{% block content %}
    <div class="row justify-content-center">
        <div class="col-lg-8">
            <h1 class="text-center mb-4">Gemini Research Search</h1>
            <p class="text-center text-muted">Enter a research topic to generate a mock, in-depth Gemini-style result.</p>
            
            <form action="{{ url_for('index') }}" method="get" class="mb-5">
                <div class="input-group">
                    <input type="text" class="form-control form-control-lg" name="query" placeholder="E.g., The role of quantum computing in pharmacology" value="{{ query if query else '' }}" required>
                    <button class="btn btn-primary btn-lg" type="submit">Search</button>
                </div>
            </form>
            
            {% if results %}
                <h2 class="mb-4">Results for "{{ original_query }}"</h2>
                {% for result in results %}
                    <div class="card card-result">
                        <div class="card-body">
                            <h5 class="card-title">
                                <a href="{{ url_for('article', slug=result['slug']) }}?query={{ original_query | urlencode }}" class="text-decoration-none text-primary">{{ result['title'] }}</a>
                            </h5>
                            <p class="card-subtitle mb-2 text-muted">
                                {{ result['author'] }} &bull; {{ result['year'] }} &bull; {{ result['source'] }}
                            </p>
                            <p class="card-text">{{ result['summary'][:300] }}...</p>
                        </div>
                    </div>
                {% endfor %}
            {% elif query and not results %}
                <div class="alert alert-warning text-center" role="alert">
                    No results found for **"{{ original_query }}"**. Please try a different query.
                </div>
            {% endif %}
        </div>
    </div>
{% endblock %}
""")

ARTICLE_PAGE_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
{% block content %}
    <a href="{{ url_for('index') }}?query={{ original_query | urlencode }}" class="btn btn-outline-primary mb-3">
        &larr; Back to Results
    </a>

    <div class="card p-4">
        <h1 class="card-title">{{ article['title'] }}</h1>
        <p class="text-muted mb-4">
            By **{{ article['author'] }}** | **{{ article['source'] }}** ({{ article['year'] }})
        </p>

        <div class="card-body bg-light rounded p-3 mb-4">
            <h5 class="card-subtitle mb-2">In-Depth Summary (Gemini AI Research Abstract):</h5>
            <p class="card-text">{{ article['summary'] | replace('\\n', '<br>') | safe }}</p>
        </div>

        <p class="mt-4">
            <small class="text-secondary">This content is an AI-generated mock research result based on the query: **"{{ original_query }}"**. It demonstrates how the Gemini API can be used to generate structured, informative abstracts for a research-focused application.</small>
        </p>
    </div>
{% endblock %}
""")


# -------------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------------

def generate_url_slug(title):
    """Converts a title into a URL-friendly slug."""
    slug = re.sub(r'[^\w\s-]', '', title).strip().lower()
    slug = re.sub(r'[-\s]+', '-', slug)
    # Add a random hash to ensure uniqueness even if titles are identical
    return f"{slug}-{random.getrandbits(16):x}"

def generate_static_mock_result(query, index):
    """Generates a predictable static mock result when the API key is missing."""
    mock_title = f"Static Mock Result #{index}: Analysis of '{query}'"
    mock_summary = (
        "This is a fallback result because the **GEMINI_API_KEY** environment variable "
        "is not set. The content is static and does not reflect a live AI response. "
        "To get dynamic results, please ensure the API key is configured correctly."
    )
    
    slug = generate_url_slug(mock_title)
    result = {
        "title": mock_title,
        "author": "Static Mock System",
        "year": 2024,
        "source": "Local System Cache",
        "summary": mock_summary,
        "slug": slug
    }
    MOCK_RESULT_CACHE[slug] = result
    return result

def generate_gemini_result(client, query):
    """
    Calls the Gemini API to generate a mock general search result with a structured output.
    """
    if not client:
        return None
    
    prompt = (
        f"Generate a mock general search research result for a research platform based on the user's query: '{query}'. "
        "The result should be highly informative, in-depth, and written in a research/analytical style, similar to a detailed Gemini summary. "
        "The response must be in the exact format: "
        "TITLE: [Research Summary Title]\nAUTHOR: [AI-Analyst Name]\nYEAR: [Year]\nSOURCE: [Domain/Research Type]\nSUMMARY: [In-depth research summary/abstract of the content]"
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        # --- Robust Parsing Logic ---
        text = response.text.strip()
        data = {}
        for line in text.split('\n'):
            if ':' in line:
                # Use split(':', 1) to ensure only the first colon separates key and value
                key, value = line.split(':', 1)
                data[key.strip().upper()] = value.strip()
        
        # Check that all required keys are present
        required_keys = ['TITLE', 'AUTHOR', 'YEAR', 'SOURCE', 'SUMMARY']
        if not all(k in data for k in required_keys):
            print(f"Parsing failed. Missing keys in LLM output: {set(required_keys) - set(data.keys())}")
            return None # Return None if parsing failed

        # Convert parsed data into the expected result format
        slug = generate_url_slug(data['TITLE'])
        result = {
            "title": data['TITLE'],
            "author": "Gemini AI", # Overriding the generated author to ensure it's always 'Gemini AI'
            "year": data['YEAR'],
            "source": data['SOURCE'] + " (AI-Generated)", # Mark it as AI
            "summary": data['SUMMARY'],
            "slug": slug
        }
        # Add to the global cache for the /article route to use
        MOCK_RESULT_CACHE[slug] = result
        return result
            
    except APIError as e:
        print(f"Gemini API Error: {e}")
        return None
    except Exception as e:
        # Catch any other error (e.g., network, unexpected data type, index errors during parsing)
        print(f"General Error during Gemini call or processing: {e}")
        return None


# -------------------------------------------------------------------------
# Flask Routes
# -------------------------------------------------------------------------

@app.route('/')
def index():
    """Handles the main search page and search results."""
    query = request.args.get('query')
    results = []
    
    if query:
        if GEMINI_CLIENT_READY:
            # Clear the cache for a new search
            MOCK_RESULT_CACHE.clear()
            
            # Generate one main result using the LLM
            llm_result = generate_gemini_result(client, query)
            if llm_result:
                results.append(llm_result)
            
            # Add two static mock results to fill the page
            results.append(generate_static_mock_result(query, 2))
            results.append(generate_static_mock_result(query, 3))
            
            # Filter out any None results
            results = [r for r in results if r is not None]

        else:
            # Fallback to only static mock data if the API is not ready
            for i in range(1, 4):
                results.append(generate_static_mock_result(query, i))

    # Pass the original query back to the template for display
    original_query = query if query else ""
    
    return render_template_string(
        INDEX_PAGE_HTML,
        query=original_query,
        results=results,
        original_query=original_query # Used for passing to the article link
    )


# --- FIX APPLIED HERE ---
@app.route('/article/<slug>')
def article(slug):
    """
    Renders a detailed article page for a specific result identified by a slug.
    Retrieves the article data from the temporary cache.
    """
    original_query = request.args.get('query', 'Recent Gemini Search')
    
    # 1. Attempt to retrieve data from the cache
    article_data = MOCK_RESULT_CACHE.get(slug)

    if not article_data:
        # 2. Handle Cache Miss: Log and create a fallback result
        print(f"Warning: Article cache miss for slug: {slug}. Providing fallback.")
        
        fallback_title = None
        try:
            # Attempt to generate a clean title from the slug for the fallback message
            fallback_title = slug.rsplit('-', 1)[0].replace('-', ' ').title()
        except IndexError:
            # Handles slugs without a dash separator (unlikely but safe)
            fallback_title = slug.replace('-', ' ').title()
            
        # 3. Create a robust fallback article dictionary
        article_data = {
            "title": f"Error: Article Not Found (Mock Title: {fallback_title})",
            "author": "System Error",
            "year": 2025,
            "source": "Fallback Cache Miss (Session Expired or Process Died)",
            "summary": "The full article content could not be retrieved from the current session cache. This typically happens if the server process restarted or if the session expired. Please return to the search results page and click the link again.",
            "slug": slug # Keep the slug for consistent data structure
        }
    
    # 4. Render the page using the data (either from cache or the fallback)
    return render_template_string(
        ARTICLE_PAGE_HTML,
        article=article_data,
        original_query=original_query
    )
# --- FIX APPLIED HERE ---


# -------------------------------------------------------------------------
# Application Run (FIXED FOR FASTER LOCAL DEVELOPMENT)
# -------------------------------------------------------------------------

if __name__ == '__main__':
    print("----------------------------------------------------------")
    print("Flask Application Running Locally (via built-in server):")
    print("Homepage: https://mind-work.onrender.com")
    print(f"Gemini Status: {'✅ Active' if GEMINI_CLIENT_READY else '❌ Inactive (Set GEMINI_API_KEY)'}")
    print("----------------------------------------------------------")
    
    app.run(host='0.0.0.0', port=5002, debug=True)
