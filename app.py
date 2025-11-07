import os
import random
import re # Added for slug generation
from flask import Flask, render_template_string, request, redirect, url_for
# Import the Google GenAI SDK for the LLM call
from google import genai
from google.genai.errors import APIError

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------

# IMPORTANT: Set your API Key as an environment variable (best practice)
# In your terminal, use: export GEMINI_API_KEY="YOUR_API_KEY"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)
# Set debug mode to True to see the traceback in the browser
app.config['DEBUG'] = True

# Initialize the Gemini Client
client = None
GEMINI_CLIENT_READY = False
if GEMINI_API_KEY:
    try:
        # client = genai.Client() is implicit when no API key is provided, but we set it here for explicit control
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
# In a real app, this would be a database or cache
MOCK_RESULT_CACHE = {} 


# -------------------------------------------------------------------------
# HTML Template Components (Updated Footer)
# -------------------------------------------------------------------------

# CONTACT/REPORT SECTION TEMPLATE (Used in all main HTML pages)
CONTACT_FOOTER_SECTION = f"""
    <div class="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 bg-gray-900">
        <div class="text-center">
            <h3 class="text-xl font-semibold text-white mb-2">Contact / Report an Issue</h3>
            <p class="text-base text-gray-400">
                For support, feature requests, or to report an issue, please contact:
                <a href="mailto:{CONTACT_EMAIL}" class="text-blue-400 hover:text-blue-300 transition duration-150">
                    {CONTACT_EMAIL}
                </a>
            </p>
        </div>
    </div>
"""

# The existing footer is placed after the new contact section for aesthetic separation.
BASE_FOOTER_HTML = f"""
    {CONTACT_FOOTER_SECTION}
    <footer class="bg-gray-800">
        <div class="max-w-7xl mx-auto py-8 px-4 overflow-hidden sm:px-6 lg:px-8">
            <nav class="-mx-5 -my-2 flex flex-wrap justify-center" aria-label="Footer">
                <div class="px-5 py-2">
                    <a href="#" class="text-base text-gray-300 hover:text-white transition duration-150">Terms of Use</a>
                </div>
                <div class="px-5 py-2">
                    <a href="#" class="text-base text-gray-300 hover:text-white transition duration-150">Privacy Policy</a>
                </div>
                <div class="px-5 py-2">
                    <a href="#" class="text-base text-gray-300 hover:text-white transition duration-150">Support</a>
                </div>
                <div class="px-5 py-2">
                    <a href="#" class="text-base text-gray-300 hover:text-white transition duration-150">Accessibility</a>
                </div>
            </nav>
            <p class="mt-8 text-center text-base text-gray-400">
                &copy; 2025 MindWork, Inc. Research tools for the modern explorer.
            </p>
        </div>
    </footer>
"""

# -------------------------------------------------------------------------
# HTML Template Strings (DEFINITIONS ADDED TO FIX PYLANCE ERRORS)
# -------------------------------------------------------------------------

# Placeholder/Original content for LOGIN form. The key part is having the </body> tag.
LOGIN_FORM_HTML = """
<!DOCTYPE html>
<html lang="en"><head><title>Login</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="antialiased bg-gray-100">
    <div class="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div class="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-2xl">
            <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">Sign in to your account</h2>
            <form class="mt-8 space-y-6" action="/login" method="POST">
                <input type="hidden" name="remember" value="true">
                <div class="rounded-md shadow-sm -space-y-px">
                    <div><label for="email-address" class="sr-only">Email address</label><input id="email-address" name="email" type="email" autocomplete="email" required class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" placeholder="Email address"></div>
                    <div><label for="password" class="sr-only">Password</label><input id="password" name="password" type="password" autocomplete="current-password" required class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" placeholder="Password"></div>
                </div>
                <div><button type="submit" class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">Sign in</button></div>
            </form>
            <div class="mt-6"><a href="/oauth/google" class="group relative w-full flex justify-center py-2 px-4 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"><img class="h-5 w-5 mr-2" src="https://upload.wikimedia.org/wikipedia/commons/4/4a/Logo_and_wordmark_of_Google.svg" alt="Google logo">Sign in with Google</a></div>
            <div class="text-center text-sm"><a href="/register" class="font-medium text-blue-600 hover:text-blue-500">Don't have an account? Sign up</a></div>
        </div>
    </div>
</body>
</html>
"""

# Placeholder/Original content for REGISTER form. The key part is having the </body> tag.
REGISTER_FORM_HTML = """
<!DOCTYPE html>
<html lang="en"><head><title>Register</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="antialiased bg-gray-100">
    <div class="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div class="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-2xl">
            <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">Create your account</h2>
            <form class="mt-8 space-y-6" action="/register" method="POST">
                <div class="rounded-md shadow-sm -space-y-px">
                    <div><label for="full-name" class="sr-only">Full Name</label><input id="full-name" name="name" type="text" required class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" placeholder="Full Name"></div>
                    <div><label for="email-address-reg" class="sr-only">Email address</label><input id="email-address-reg" name="email" type="email" autocomplete="email" required class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" placeholder="Email address"></div>
                    <div><label for="password-reg" class="sr-only">Password</label><input id="password-reg" name="password" type="password" autocomplete="new-password" required class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" placeholder="Password"></div>
                </div>
                <div><button type="submit" class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">Sign up</button></div>
            </form>
            <div class="mt-6"><a href="/oauth/google" class="group relative w-full flex justify-center py-2 px-4 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"><img class="h-5 w-5 mr-2" src="https://upload.wikimedia.org/wikipedia/commons/4/4a/Logo_and_wordmark_of_Google.svg" alt="Google logo">Sign Up with Google</a></div>
            <div class="text-center text-sm"><a href="/login" class="font-medium text-blue-600 hover:text-blue-500">Already have an account? Sign in</a></div>
        </div>
    </div>
</body>
</html>
"""

# Placeholder/Original content for SEARCH RESULTS page.
SEARCH_RESULTS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Results for {{ query }} - MindWork</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                    },
                    colors: {
                        'primary-blue': '#1f4e79', /* Deep Navy */
                        'secondary-gray': '#f3f4f6',
                        'accent-gold': '#d9a400', /* Gold for academic accent */
                    }
                }
            }
        }
    </script>
</head>
<body class="antialiased">

    <header class="sticky top-0 z-50 bg-white shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center py-4 md:justify-start md:space-x-10">
                <div class="flex justify-start lg:w-0 lg:flex-1">
                    <a href="/" class="text-2xl font-extrabold text-primary-blue">
                        MindWork
                    </a>
                </div>
                <div class="hidden md:flex items-center justify-end md:flex-1 lg:w-0">
                    <a href="/login" class="ml-8 whitespace-nowrap inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-lg shadow-lg text-base font-medium text-white bg-primary-blue hover:bg-blue-800 transition duration-300">
                        Login / Sign Up
                    </a>
                </div>
            </div>
        </div>
    </header>

    <main class="bg-gray-50 min-h-screen">
        <div class="max-w-7xl mx-auto py-8 sm:py-12 px-4 sm:px-6 lg:px-8">
            <div class="mb-8 max-w-4xl mx-auto">
                <form method="GET" action="/search">
                    <label for="results-search" class="sr-only">Search MindWork</label>
                    <div class="relative">
                        <input type="text" id="results-search" name="query" value="{{ query }}" placeholder="Search anything: general topics, media, concepts, or ask Gemini..."
                                class="w-full py-3 pl-4 pr-12 border border-gray-300 rounded-xl shadow-md focus:ring-primary-blue focus:border-primary-blue text-lg text-black transition duration-200"
                                required>
                        <button type="submit" class="absolute right-0 top-0 bottom-0 px-4 flex items-center text-primary-blue hover:text-blue-800">
                            <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                        </button>
                    </div>
                </form>
            </div>
            
            <h1 class="text-2xl font-bold text-gray-900 mb-6 border-b pb-2">Search Results for: "<span class="text-primary-blue">{{ query }}</span>"</h1>
            
            {% if results %}
                <div class="space-y-8">
                    {% for result in results %}
                        <div class="bg-white p-6 rounded-xl shadow-lg {% if result.author == 'Gemini AI' %}border-l-4 border-accent-gold{% endif %}">
                            
                            <h2 class="text-xl font-semibold {% if result.author == 'Gemini AI' %}text-accent-gold{% else %}text-primary-blue{% endif %} mb-1">
                                <a href="{{ url_for('article', slug=result.slug, query=query) }}" class="hover:underline">
                                    {{ result.title }}
                                </a>
                            </h2>
                            
                            <p class="text-gray-700 leading-relaxed">
                                {{ result.summary }}
                            </p>
                        </div>
                    {% endfor %}
                </div>
                
                <div class="mt-8 text-center text-gray-600">
                    Displaying {{ results|length }} results. Total mock results are 105.
                </div>
            {% else %}
                <div class="text-center py-10 bg-white rounded-xl shadow-lg">
                    <p class="text-xl text-gray-600">No results found for your query. Please try searching for something else.</p>
                </div>
            {% endif %}

        </div>
    </main>

</body>
</html>
"""

# New HTML template for the simulated full article page.
ARTICLE_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ article.title }} - MindWork</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                    },
                    colors: {
                        'primary-blue': '#1f4e79', /* Deep Navy */
                        'secondary-gray': '#f3f4f6',
                        'accent-gold': '#d9a400', /* Gold for academic accent */
                    }
                }
            }
        }
    </script>
</head>
<body class="antialiased bg-gray-50">

    <header class="sticky top-0 z-50 bg-white shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center py-4 md:justify-start md:space-x-10">
                <div class="flex justify-start lg:w-0 lg:flex-1">
                    <a href="/" class="text-2xl font-extrabold text-primary-blue">
                        MindWork
                    </a>
                </div>
                <div class="hidden md:flex items-center justify-end md:flex-1 lg:w-0">
                    <a href="/login" class="ml-8 whitespace-nowrap inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-lg shadow-lg text-base font-medium text-white bg-primary-blue hover:bg-blue-800 transition duration-300">
                        Login / Sign Up
                    </a>
                </div>
            </div>
        </div>
    </header>

    <main class="min-h-screen">
        <div class="max-w-5xl mx-auto py-12 sm:py-16 px-4 sm:px-6 lg:px-8">
            
            <a href="{{ url_for('search', query=original_query) }}" class="text-primary-blue hover:text-blue-700 transition duration-150 flex items-center mb-6">
                <svg class="h-4 w-4 mr-1 transform rotate-180" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
                Back to Search Results for "{{ original_query }}"
            </a>
            
            <article class="bg-white p-8 sm:p-10 rounded-xl shadow-2xl">
                <header>
                    <h1 class="text-4xl font-extrabold text-gray-900 leading-tight mb-4">
                        {{ article.title }}
                    </h1>
                    <p class="text-lg text-gray-600 mb-6 border-b pb-4">
                        <span class="font-medium text-primary-blue">Source: {{ article.source }}</span> | 
                        Author: {{ article.author }} | 
                        Published: {{ article.year }}
                    </p>
                </header>

                <div class="prose max-w-none text-gray-700 space-y-6">
                    <p class="text-xl font-semibold text-gray-800">Abstract:</p>
                    
                    <p>{{ article.summary }}</p>

                    <p class="pt-4 border-t mt-6 text-xl font-semibold text-primary-blue">
                        Simulated Full Content:
                    </p>
                    
                    {% if article.author == 'Gemini AI' %}
                        <p>
                            **In-depth Analysis by Gemini AI:** Expanding upon the initial summary, the research reveals that the core finding, *{{ article.title }}*, demonstrates a significant deviation from previous models. Specifically, the data suggests that the variable 'Complexity Index' has an inverse correlation with 'User Engagement' across 85% of documented case studies. This contradicts the traditional 'Information Density Model' widely accepted until {{ article.year|int - 1 }}. The next section will detail the mathematical model used for this calculation.
                        </p>
                        <p>
                            **Section 1: Methodological Approach.** The analysis employed a novel Recursive Cluster Sampling (RCS) technique. This allowed for the efficient processing of large, unstructured datasets (the 100+ simulated results) to identify emergent themes related to the query "{{ original_query }}".
                        </p>
                        <p>
                            **Section 2: Key Findings.** The three most prominent emergent sub-topics were: (1) Ethical implications in design, (2) Scalability challenges in global markets, and (3) Unanticipated cultural adoption vectors. Each of these areas requires dedicated future research.
                        </p>
                        <p>
                            **Conclusion:** The findings presented in this AI-generated research summary provide a strong foundation for further human-led investigation into "{{ original_query }}".
                        </p>
                    {% else %}
                        <p>
                            This is the full, expanded article content which elaborates on the abstract. The primary focus of this text is to provide a detailed, step-by-step examination of the concepts introduced in the summary: "{{ article.summary }}".
                        </p>
                        <p>
                            The author, **{{ article.author }}**, uses a didactic approach to explain the practical applications and theoretical underpinnings. For instance, the discussion on 'implementation challenges' spans over three thousand words and includes a glossary of technical terms related to **{{ original_query }}**.
                        </p>
                        <p>
                            Furthermore, this resource is highly cited in the simulated academic community, appearing in **{{ random.randint(10, 50) }}** other mock documents generated for the MindWork platform.
                        </p>
                    {% endif %}
                </div>
            </article>
            
        </div>
    </main>

</body>
</html>
"""

# The following is the correct definition for MINDWORK_HOMEPAGE_HTML, 
# which was incomplete or missing in your previous post and could cause a render error.
MINDWORK_HOMEPAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindWork: General Research & Discovery Platform</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                    },
                    colors: {
                        'primary-blue': '#1f4e79', /* Deep Navy */
                        'secondary-gray': '#f3f4f6',
                        'accent-gold': '#d9a400', /* Gold for academic accent */
                    }
                }
            }
        }
    </script>
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #ffffff;
        }
        .hero-background-pattern {
            background-image: radial-gradient(#d4d4d8 1px, transparent 0);
            background-size: 30px 30px;
            opacity: 0.5;
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
        }
    </style>
</head>
<body class="antialiased">

    <header class="sticky top-0 z-50 bg-white shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center py-4 md:justify-start md:space-x-10">
                <div class="flex justify-start lg:w-0 lg:flex-1">
                    <a href="/" class="text-2xl font-extrabold text-primary-blue">
                        MindWork
                    </a>
                </div>

                <nav class="hidden md:flex space-x-10">
                    <a href="#" class="text-base font-medium text-gray-500 hover:text-primary-blue transition duration-150">Features</a>
                    <a href="#" class="text-base font-medium text-gray-500 hover:text-primary-blue transition duration-150">News</a>
                    <a href="#" class="text-base font-medium text-gray-500 hover:text-primary-blue transition duration-150">About</a>
                    <a href="#" class="text-base font-medium text-gray-500 hover:text-primary-blue transition duration-150">Support</a>
                </nav>

                <div class="hidden md:flex items-center justify-end md:flex-1 lg:w-0">
                    <a href="/login" class="ml-8 whitespace-nowrap inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-lg shadow-lg text-base font-medium text-white bg-primary-blue hover:bg-blue-800 transition duration-300">
                        Login / Sign Up
                    </a>
                </div>
            </div>
        </div>
    </header>

    <main class="relative isolate pt-14">
        <div class="absolute inset-x-0 -top-40 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80" aria-hidden="true">
            <div class="hero-background-pattern"></div>
        </div>

        <div class="py-24 sm:py-32 lg:pb-40">
            <div class="mx-auto max-w-7xl px-6 lg:px-8">
                <div class="mx-auto max-w-2xl text-center">
                    <h1 class="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
                        Research Simplified. <span class="text-primary-blue">AI Enhanced.</span>
                    </h1>
                    <p class="mt-6 text-lg leading-8 text-gray-600">
                        Search anything: academic papers, media analysis, concepts, or use Gemini's powerful analytical capabilities.
                    </p>
                    
                    <div class="mt-10">
                        <form method="GET" action="/search" class="max-w-xl mx-auto">
                            <label for="main-search" class="sr-only">Search MindWork</label>
                            <div class="relative">
                                <input type="text" id="main-search" name="query" placeholder="Search anything: general topics, media, concepts, or ask Gemini..."
                                       class="w-full py-4 pl-6 pr-16 border border-gray-300 rounded-full shadow-2xl focus:ring-primary-blue focus:border-primary-blue text-xl text-black transition duration-300"
                                       required>
                                <button type="submit" class="absolute right-0 top-0 bottom-0 px-6 flex items-center bg-primary-blue rounded-r-full text-white hover:bg-blue-800 transition duration-300">
                                    <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                    </svg>
                                </button>
                            </div>
                        </form>
                    </div>

                    <div class="mt-4 text-sm text-gray-500">
                        Try queries like: "future of renewable energy", "analysis of the latest space telescope images", or "how to make sourdough bread".
                    </div>
                </div>
            </div>
        </div>
    </main>
</body>
</html>
"""


# -------------------------------------------------------------------------
# HTML Template Strings (Replacement Logic)
# -------------------------------------------------------------------------

# The replacement logic now works because the variables are defined above.
LOGIN_FORM_HTML = LOGIN_FORM_HTML.replace("</body>", f"{BASE_FOOTER_HTML}</body>")
REGISTER_FORM_HTML = REGISTER_FORM_HTML.replace("</body>", f"{BASE_FOOTER_HTML}</body>")
ARTICLE_PAGE_HTML = ARTICLE_PAGE_HTML.replace("</body>", f"{BASE_FOOTER_HTML}</body>")
MINDWORK_HOMEPAGE_HTML = MINDWORK_HOMEPAGE_HTML.replace("</body>", f"{BASE_FOOTER_HTML}</body>")


# -------------------------------------------------------------------------
# Helper Functions for Search Simulation (Updated)
# -------------------------------------------------------------------------

def generate_url_slug(title):
    """
    Creates a URL-friendly slug (ID) from a title.
    """
    # Convert to lowercase
    s = title.lower()
    # Remove non-word characters (except spaces and hyphens)
    s = re.sub(r'[^\w\s-]', '', s)
    # Replace whitespace with a single hyphen
    s = re.sub(r'[\s]+', '-', s)
    # Ensure it's not starting or ending with a hyphen
    s = s.strip('-')
    # Add a random unique 4-digit hex string to ensure uniqueness
    unique_id = hex(random.randint(0x1000, 0xffff))[2:]
    return f"{s}-{unique_id}"


def generate_general_results(query, count=105):
    """
    Generates a large, diverse list of mock search results based on the query,
    formatted as AI-style abstracts/summaries.
    """
    common_subjects = ["Photography", "Cooking", "Travel Guides", "History", "Coding Tutorials", "Fitness", "Personal Finance", "Gardening", "Science News", "Music Theory", "World Events", "Home Decor", "Gaming", "DIY Projects"]
    common_formats = ["How to", "Best 10 Tips for", "A Deep Dive into", "The Ultimate Guide to", "Review of", "Top 5 Mistakes in", "Beginner's Guide to", "Quick Start:", "Comprehensive FAQ on"]
    common_authors = ["Jane Doe", "John Smith", "The Daily Explorer", "Tech Guru", "Culinary Arts", "Historian Guy", "DIY Master", "Financial Freedom Blog"]
    
    # New list of AI-style summary starters/structures
    ai_starters = [
        "Research Abstract: This study investigates the inverse correlation between",
        "Conceptual Synthesis: The key findings reveal a dependency between",
        "Analytical Overview: We present a comprehensive examination of the factors influencing",
        "Data-Driven Summary: A statistical analysis demonstrates the impact of",
        "Key Insights Report: Emerging patterns suggest a shift in the traditional approach to"
    ]

    results = []
    
    # Store results to check for title duplicates during generation
    generated_titles = set()
    
    while len(results) < count:
        subject = random.choice(common_subjects)
        format_type = random.choice(common_formats)
        year = random.randint(2015, 2025)
        
        # Create a title that includes the query
        if len(results) < 5:
             # Ensure the first few results are highly relevant to the core query
            title = f"The Essential Guide to {query}: History, Use, and Future - Entry {len(results)+1}"
            source = f"Top-Tier Site {random.randint(1, 3)}"
        elif len(results) % 5 == 0:
            title = f"{format_type} {subject}: The Impact of '{query}' - Analysis {len(results)+1}"
            source = f"Specialist Blog {random.randint(1, 10)}"
        else:
            title = f"{format_type} {query} in {subject} - Topic {len(results)+1}"
            source = f"Web Source {random.randint(11, 50)}"

        if title not in generated_titles:
            generated_titles.add(title)
            
            slug = generate_url_slug(title)
            
            # Generate the new abstract-like summary
            summary_starter = random.choice(ai_starters)
            new_summary = f"{summary_starter} {query} within the domain of {subject}, providing condensed insights and preliminary conclusions. This is result number {len(results)+1}."

            result = {
                "title": title,
                "author": random.choice(common_authors),
                "year": year,
                "source": source,
                "summary": new_summary, # Use the new abstract-like summary
                "slug": slug
            }
            results.append(result)
            # Add to the global cache for the /article route to use
            MOCK_RESULT_CACHE[slug] = result
            
    return results


def generate_gemini_result(client, query):
    """
    Calls the Gemini API to generate a mock general search result.
    The prompt is updated to reflect the request for Gemini-like research results.
    """
    if not client:
        return None
    
    # Check if the query indicates a file/image analysis
    if any(ext in query.lower() for ext in ['.jpg', '.png', '.pdf', '.docx', '.txt']):
        file_name = query
        mock_title = f"AI Research: Analysis of '{file_name}'" # Updated title
        mock_summary = f"An initial AI-driven summary suggesting key concepts, visual elements, and potential research applications based on the content of the uploaded file/image. This is a research-style summary, providing the same results as Google Gemini for research purposes."
        
        # Generate slug and cache the result
        slug = generate_url_slug(mock_title)
        result = {
            "title": mock_title,
            "author": "Gemini AI",
            "year": 2025,
            "source": "Multimodal Analysis (AI-Generated)",
            "summary": mock_summary,
            "slug": slug
        }
        MOCK_RESULT_CACHE[slug] = result
        return result


    prompt = (
        f"Generate a mock general search research result for a research platform based on the user's query: '{query}'. "
        "The result should be highly informative, in-depth, and written in a research/analytical style, similar to a detailed Gemini summary. "
        "The response must be in the exact format: "
        "TITLE: [Research Summary Title]\nAUTHOR: [AI-Analyst Name]\nYEAR: [Year]\nSOURCE: [Domain/Research Type]\nSUMMARY: [In-depth research summary/abstract of the content]"
    )

    try:
        # Using a fast model for this mock generation task
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        # Parse the structured text output
        text = response.text.strip()
        
        data = {}
        for line in text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip().upper()] = value.strip()
        
        # Convert parsed data into the expected result format
        if all(k in data for k in ['TITLE', 'AUTHOR', 'YEAR', 'SOURCE', 'SUMMARY']):
            
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
        print(f"General Error during Gemini call: {e}")
        return None
        
    return None

# -------------------------------------------------------------------------
# Flask Routes (Updated)
# -------------------------------------------------------------------------

# MOCK QUERY SUFFIXES: Use a list of suffixes to skip the Gemini call during development.
MOCK_QUERY_SUFFIXES = ['mock', 'static', 'test']

@app.route('/')
def home():
    """Renders the MindWork homepage."""
    return render_template_string(MINDWORK_HOMEPAGE_HTML)

@app.route('/login')
def login_page():
    """Renders the login page."""
    return render_template_string(LOGIN_FORM_HTML)

@app.route('/register')
def register_page():
    """Renders the register page."""
    return render_template_string(REGISTER_FORM_HTML)


@app.route('/search', methods=['GET'])
def search():
    """
    Handles the search request, attempts to call Gemini, and falls back to mock data.
    """
    # 1. Get the query from the URL parameters
    query = request.args.get('query', '').strip()
    
    if not query:
        # If the query is empty, redirect back to the home page
        return redirect(url_for('home')) 
    
    # 2. Determine if Gemini should be called
    should_call_gemini = (
        GEMINI_CLIENT_READY and 
        not query.lower().endswith(tuple(MOCK_QUERY_SUFFIXES))
    )
    
    gemini_result = None
    
    if should_call_gemini:
        print(f"Attempting Gemini search for: {query}")
        # Calls the function that hits the API
        gemini_result = generate_gemini_result(client, query)
        
    # 3. Generate the static/mock/web results
    static_results = generate_general_results(query)
    
    # 4. Combine the results. Place the Gemini result (if successful) at the top.
    results = []
    if gemini_result:
        results.append(gemini_result)
        
    # Add the static results
    results.extend(static_results)

    # 5. Render the search results template with the combined data
    return render_template_string(
        SEARCH_RESULTS_HTML, 
        query=query, 
        results=results
    )

@app.route('/article/<slug>')
def article(slug):
    """
    Simulates loading a full article based on the slug.
    Loads data from the MOCK_RESULT_CACHE.
    """
    # Grab the original query parameter used to generate the results
    original_query = request.args.get('query', 'General Research')

    article_data = MOCK_RESULT_CACHE.get(slug)
    
    if article_data:
        return render_template_string(
            ARTICLE_PAGE_HTML, 
            article=article_data, 
            original_query=original_query
        )
    else:
        # Handle case where article is not found (e.g., 404 page)
        return f"Article with slug '{slug}' not found.", 404


# Placeholder routes for login/register actions
@app.route('/login', methods=['POST'])
def handle_login():
    """Simulated login handler."""
    # In a real app, you would validate credentials here.
    return redirect(url_for('home'))

@app.route('/register', methods=['POST'])
def handle_register():
    """Simulated register handler."""
    # In a real app, you would create a new user here.
    return redirect(url_for('home'))

# Placeholder route for Google OAuth
@app.route('/oauth/google')
def handle_oauth():
    """Simulated Google OAuth handler."""
    return "Simulating Google login...", 200


if __name__ == '__main__':
    print("--- Starting MindWork Flask App ---")
    print("Visit http://127.0.0.1:5000/")
    # Running with debug=True to display tracebacks in the browser for easy debugging
    app.run(debug=True)
