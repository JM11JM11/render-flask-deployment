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

# -------------------------------------------------------------------------
# HTML Template Strings (Replacement Logic)
# -------------------------------------------------------------------------

# The replacement logic now works because the variables are defined above.
LOGIN_FORM_HTML = LOGIN_FORM_HTML.replace("</body>", f"{BASE_FOOTER_HTML}</body>")
REGISTER_FORM_HTML = REGISTER_FORM_HTML.replace("</body>", f"{BASE_FOOTER_HTML}</body>")
ARTICLE_PAGE_HTML = ARTICLE_PAGE_HTML.replace("</body>", f"{BASE_FOOTER_HTML}</body>")
# MINDWORK_HOMEPAGE_HTML and SEARCH_RESULTS_HTML will be handled in the final code block.


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

@app.route('/')
def home():
    """Renders the MindWork homepage."""
    # Ensure MINDWORK_HOMEPAGE_HTML is defined or imported before use
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

                <div class="-mr-2 -my-2 md:hidden">
                    <button id="mobile-menu-open-btn" type="button" onclick="toggleMenu()" class="bg-white rounded-md p-2 inline-flex items-center justify-center text-gray-700 hover:text-primary-blue hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-blue" aria-expanded="false" aria-controls="mobile-menu-panel">
                        <span class="sr-only">Open menu</span>
                        <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                    </button>
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

        <div id="mobile-menu-panel" class="md:hidden transition-all duration-300 ease-out max-h-0 overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="mobile-menu-open-btn">
            <div class="rounded-b-lg shadow-2xl ring-1 ring-black ring-opacity-5 bg-white divide-y-2 divide-gray-50">
                <div class="pt-5 pb-6 px-5">
                    <div class="flex items-center justify-between">
                        <div>
                            <span class="text-xl font-extrabold text-primary-blue">MindWork</span>
                        </div>
                        <div class="-mr-2">
                            <button type="button" onclick="toggleMenu()" class="bg-white rounded-md p-2 inline-flex items-center justify-center text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-blue">
                                <span class="sr-only">Close menu</span>
                                <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                    </div>
                    <div class="mt-6">
                        <nav class="grid gap-y-8">
                            <a href="#" class="-m-3 p-3 flex items-center rounded-lg hover:bg-gray-50">Features</a>
                            <a href="#" class="-m-3 p-3 flex items-center rounded-lg hover:bg-gray-50">News</a>
                            <a href="#" class="-m-3 p-3 flex items-center rounded-lg hover:bg-gray-50">About</a>
                            <a href="#" class="-m-3 p-3 flex items-center rounded-lg hover:bg-gray-50">Support</a>
                        </nav>
                    </div>
                </div>
                <div class="py-6 px-5 space-y-6">
                    <div>
                        <a href="/login" class="w-full flex items-center justify-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-base font-medium text-white bg-primary-blue hover:bg-blue-800">
                            Login / Sign Up
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <main class="bg-white">
        <div class="relative overflow-hidden bg-white">
            <div class="hero-background-pattern"></div>
            <div class="max-w-7xl mx-auto py-12 sm:py-24 lg:py-32">
                <div class="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    
                    <h1 class="text-5xl tracking-tight font-extrabold text-gray-900 sm:text-6xl md:text-7xl">
                        <span class="block text-primary-blue">MindWork Research</span>
                        <span class="block text-gray-900 mt-2">AI-Powered Discovery</span> 
                    </h1>
                    <p class="mt-4 text-xl text-gray-600 sm:mt-5 sm:max-w-xl sm:mx-auto">
                        Your universal platform for research, combining general web search with Google Gemini's analytical capabilities.
                    </p>
                      
                    <div class="mt-10 mx-auto max-w-4xl">
                        <form method="GET" action="/search">
                            <label for="site-search" class="sr-only">Search the MindWork Research Hub</label>
                            <div class="relative flex items-center">
                                <div class="absolute left-0 top-0 bottom-0 z-10">
                                    <div class="h-full flex items-center pl-3">
                                        <button type="button" id="upload-menu-button" onclick="toggleUploadMenu(event)" 
                                                class="p-1 text-primary-blue rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-blue transition duration-200">
                                            <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                                            </svg>
                                        </button>
                                    </div>

                                    <div id="upload-menu" class="origin-top-left absolute left-0 mt-1 w-64 rounded-xl shadow-2xl bg-white ring-1 ring-black ring-opacity-5 divide-y divide-gray-100 hidden z-20" role="menu" aria-orientation="vertical" aria-labelledby="upload-menu-button">
                                        <div class="py-1" role="none">
                                            <input type="file" id="file-upload-input" accept="image/*, .pdf, .docx, .txt" class="hidden" onchange="handleFileUpload(event)">
                                            
                                            <a href="#" class="flex items-center px-4 py-3 text-sm text-gray-700 hover:bg-gray-100 hover:text-primary-blue rounded-t-xl" role="menuitem" onclick="document.getElementById('file-upload-input').click(); toggleUploadMenu(); return false;">
                                                <svg class="mr-3 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-upload"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
                                                Upload Pictures/Files
                                            </a>
                                            
                                            <a href="#" class="flex items-center px-4 py-3 text-sm text-gray-700 hover:bg-gray-100 hover:text-primary-blue rounded-b-xl" role="menuitem" onclick="alert('Accessing device camera... (Implementation needed)'); toggleUploadMenu(); return false;">
                                                <svg class="mr-3 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-camera"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>
                                                Camera: Give Access
                                            </a>
                                        </div>
                                    </div>
                                </div>

                                <input type="text" id="site-search" name="query" placeholder="Search anything: general topics, media, concepts, or ask Gemini..."
                                        class="w-full py-3 pl-16 pr-16 border border-gray-300 rounded-xl shadow-xl focus:ring-primary-blue focus:border-primary-blue text-lg text-black transition duration-200"
                                        required>
                                
                                <button type="submit" class="absolute right-0 top-0 bottom-0 px-4 flex items-center text-primary-blue hover:text-blue-800 transition duration-200">
                                    <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                    </svg>
                                </button>
                            </div>
                        </form>
                    </div>
                    
                    <div class="mt-8 sm:mt-12 flex flex-col sm:flex-row justify-center space-y-3 sm:space-y-0 sm:space-x-3">
                        <div class="rounded-lg shadow-xl w-full sm:w-auto">
                            <a href="/login" class="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-primary-blue hover:bg-blue-800 md:py-4 md:text-lg md:px-10 transition duration-300">
                                Log In to MindWork
                            </a>
                        </div>
                        <div class="mt-3 sm:mt-0 sm:ml-3 rounded-lg shadow-xl w-full sm:w-auto">
                            <a href="/register" class="w-full flex items-center justify-center px-8 py-3 border border-gray-300 text-base font-medium rounded-lg text-primary-blue bg-white hover:bg-gray-50 md:py-4 md:text-lg md:px-10 transition duration-300">
                                Create Account
                            </a>
                        </div>
                        <div class="mt-3 sm:mt-0 sm:ml-3 rounded-lg shadow-xl w-full sm:w-auto">
                            <a href="/oauth/google" class="w-full flex items-center justify-center px-8 py-3 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 md:py-4 md:text-lg md:px-10 transition duration-300">
                                <img class="h-5 w-5 mr-2" src="https://upload.wikimedia.org/wikipedia/commons/4/4a/Logo_and_wordmark_of_Google.svg" alt="Google logo">
                                Sign Up with Google
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="py-12 bg-white">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="lg:text-center">
                    <h2 class="text-base text-primary-blue font-semibold tracking-wide uppercase">Methodology</h2>
                    <p class="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
                        Tools to Explore Any Topic.
                    </p>
                    <p class="mt-4 max-w-2xl text-xl text-gray-600 lg:mx-auto">
                        Seamlessly transition from broad discovery to deep analysis with integrated search, AI synthesis, and high-volume results.
                    </p>
                </div>

                <div class="mt-10">
                    <dl class="space-y-10 md:space-y-0 md:grid md:grid-cols-3 md:gap-x-8 md:gap-y-10">
                        <div class="relative">
                            <dt>
                                <div class="absolute flex items-center justify-center h-12 w-12 rounded-lg bg-primary-blue text-white">
                                    <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-brain"><path d="M15.5 17a5 5 0 0 0-5 5H4a2 2 0 0 1-2-2v-1A7 7 0 0 1 9 10a7 7 0 0 0 6.5-3.5 6 6 0 0 0-11-2.5 6 6 0 0 0-2.5 7.7.7.7 0 0 1-.7.2 2 2 0 0 0-1.7 1.5 5 5 0 0 0 6.7 3.6 5 5 0 0 0 5-5z"></path></svg>
                                </div>
                                <p class="ml-16 text-lg leading-6 font-medium text-gray-900">AI-Powered Synthesis</p>
                            </dt>
                            <dd class="mt-2 ml-16 text-base text-gray-600">
                                Leverage Google Gemini to summarize dense topics, outline complex arguments, and generate initial research questions, **providing the same results as Google Gemini for research purposes**.
                            </dd>
                        </div>
                        
                        <div class="relative">
                            <dt>
                                <div class="absolute flex items-center justify-center h-12 w-12 rounded-lg bg-primary-blue text-white">
                                    <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-globe"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"></path><path d="M2 12h20"></path></svg>
                                </div>
                                <p class="ml-16 text-lg leading-6 font-medium text-gray-900">High-Volume Web Search</p>
                            </dt>
                            <dd class="mt-2 ml-16 text-base text-gray-600">
                                Get access to 100+ simulated results for every query, covering news, media, tutorials, and general information.
                            </dd>
                        </div>

                        <div class="relative">
                            <dt>
                                <div class="absolute flex items-center justify-center h-12 w-12 rounded-lg bg-primary-blue text-white">
                                    <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-upload-cloud"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"></path><path d="M12 12v6"></path><path d="m15 15-3 3-3-3"></path></svg>
                                </div>
                                <p class="ml-16 text-lg leading-6 font-medium text-gray-900">Multimodal Input</p>
                            </dt>
                            <dd class="mt-2 ml-16 text-base text-gray-600">
                                Upload pictures or files to kickstart your research, allowing Gemini to analyze visual or document content directly.
                            </dd>
                        </div>
                    </dl>
                </div>
            </div>
        </div>

    </main>

    <script>
        function toggleMenu() {
            const menuPanel = document.getElementById('mobile-menu-panel');
            const menuButton = document.getElementById('mobile-menu-open-btn');

            if (menuPanel.classList.contains('max-h-0')) {
                menuPanel.classList.remove('max-h-0', 'overflow-hidden');
                menuPanel.classList.add('max-h-screen');
                menuButton.setAttribute('aria-expanded', 'true');
            } else {
                menuPanel.classList.add('max-h-0', 'overflow-hidden');
                menuPanel.classList.remove('max-h-screen');
                menuButton.setAttribute('aria-expanded', 'false');
            }
        }

        function toggleUploadMenu(event) {
            // Stops the click from bubbling up and immediately closing the menu
            if (event) event.stopPropagation(); 
            const menu = document.getElementById('upload-menu');
            menu.classList.toggle('hidden');
        }

        function handleFileUpload(event) {
            const file = event.target.files[0];
            if (file) {
                // The search query now only reflects the file name
                const searchInput = document.getElementById('site-search');
                searchInput.value = `${file.name}`;
                searchInput.focus();
                // We'll rely on the user to hit 'Enter' to submit the form for simplicity.
            }
        }
        
        // Closes the menu if the user clicks anywhere outside of the button or the menu itself
        document.addEventListener('click', function(event) {
            const menu = document.getElementById('upload-menu');
            const button = document.getElementById('upload-menu-button');
            if (menu && button && !menu.contains(event.target) && !button.contains(event.target) && !menu.classList.contains('hidden')) {
                menu.classList.add('hidden');
            }
        });

    </script>

</body>
</html>
"""
    MINDWORK_HOMEPAGE_HTML = MINDWORK_HOMEPAGE_HTML.replace("</body>", f"{BASE_FOOTER_HTML}</body>")
    return render_template_string(MINDWORK_HOMEPAGE_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login with form submission."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"Attempting to log in with: {email}")
        return redirect(url_for('home'))
    
    return render_template_string(LOGIN_FORM_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles new user registration with form submission."""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"Attempting to register new user: {name} ({email})")
        return redirect(url_for('login'))
        
    return render_template_string(REGISTER_FORM_HTML)

@app.route('/oauth/google')
def google_oauth():
    """Placeholder route for initiating the Google OAuth flow."""
    # This now acts as the destination for the "Sign Up with Google" link
    print("Initiating Google OAuth/Sign Up flow...")
    return redirect(url_for('home'))


@app.route('/search', methods=['GET'])
def search():
    """
    Handles general search queries, returning 100+ mock results and a Gemini summary.
    """
    query = request.args.get('query', '').strip()
    
    if not query:
        # Return to homepage if query is empty
        return redirect(url_for('home'))
    
    # Clear the cache to prevent overflow if the app runs for a long time
    global MOCK_RESULT_CACHE
    MOCK_RESULT_CACHE = {} 

    # --- 1. General Search Simulation (Generates 100+ Diverse Results) ---
    all_results = generate_general_results(query, count=105)

    # --- 2. Gemini Generative Result (The main, featured result) ---
    if GEMINI_CLIENT_READY:
        gemini_result = generate_gemini_result(client, query)
        if gemini_result:
            # Insert the single AI result at the very top (index 0)
            all_results.insert(0, gemini_result)
        
    # Shuffle the mock results for variety (excluding the first one if it's the AI result)
    if GEMINI_CLIENT_READY and len(all_results) > 1:
        featured_ai = all_results[0]
        general_results = all_results[1:]
        random.shuffle(general_results)
        all_results = [featured_ai] + general_results
    else:
        # If no Gemini, shuffle all general results
        random.shuffle(all_results)
    
    # Ensure a maximum of 100 results are displayed to keep the page size manageable
    final_results = all_results[:100]

    return render_template_string(
        SEARCH_RESULTS_HTML,
        query=query,
        results=final_results,
        gemini_active=GEMINI_CLIENT_READY
    )

@app.route('/article/<slug>', methods=['GET'])
def article(slug):
    """
    Simulates a full article page by looking up the result in the cache.
    """
    original_query = request.args.get('query', 'research')
    article_data = MOCK_RESULT_CACHE.get(slug)
    
    if not article_data:
        # If the slug is not found (e.g., page refresh or not generated in the current session)
        # We can try to generate a fallback mock article based on the slug's title part
        fallback_title = slug.rsplit('-', 1)[0].replace('-', ' ').title()
        article_data = {
            "title": f"Error: Article Not Found (Mock Title: {fallback_title})",
            "author": "System Error",
            "year": 2025,
            "source": "Fallback Cache Miss",
            "summary": "The full article content could not be retrieved from the cache. Please return to the search results page and click the link again to reload the content.",
        }

    return render_template_string(
        ARTICLE_PAGE_HTML,
        article=article_data,
        original_query=original_query
    )


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
