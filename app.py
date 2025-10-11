import os
from flask import Flask, render_template_string, request, redirect, url_for

# -------------------------------------------------------------------------
# Flask Application Setup
# -------------------------------------------------------------------------

app = Flask(__name__)

# --- Simplified HTML Strings for New Routes ---

LOGIN_FORM_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindWork: Login</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen">
    <div class="w-full max-w-md p-8 space-y-6 bg-white rounded-xl shadow-2xl">
        <h2 class="text-3xl font-extrabold text-center text-[#1f4e79]">Log In to MindWork</h2>
        <form method="POST" action="/login" class="space-y-4">
            <div>
                <label for="email" class="block text-sm font-medium text-gray-700">Email Address</label>
                <input type="email" id="email" name="email" required 
                       class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-[#1f4e79] focus:border-[#1f4e79] sm:text-sm">
            </div>
            <div>
                <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
                <input type="password" id="password" name="password" required 
                       class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-[#1f4e79] focus:border-[#1f4e79] sm:text-sm">
            </div>
            <button type="submit" class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-[#1f4e79] hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#1f4e79]">
                Log In
            </button>
        </form>
        <div class="text-center">
            <a href="/register" class="text-sm text-[#1f4e79] hover:text-blue-700">Don't have an account? Register</a>
        </div>
        <hr class="my-4">
        <button onclick="alert('Google OAuth flow started...')" class="w-full flex items-center justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
            <img class="h-5 w-5 mr-2" src="https://upload.wikimedia.org/wikipedia/commons/4/4a/Logo_and_wordmark_of_Google.svg" alt="Google logo">
            Log In with Google
        </button>
    </div>
</body>
</html>
"""

REGISTER_FORM_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindWork: Register</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen">
    <div class="w-full max-w-md p-8 space-y-6 bg-white rounded-xl shadow-2xl">
        <h2 class="text-3xl font-extrabold text-center text-[#1f4e79]">Create a MindWork Account</h2>
        <form method="POST" action="/register" class="space-y-4">
            <div>
                <label for="name" class="block text-sm font-medium text-gray-700">Full Name</label>
                <input type="text" id="name" name="name" required 
                       class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-[#1f4e79] focus:border-[#1f4e79] sm:text-sm">
            </div>
            <div>
                <label for="email" class="block text-sm font-medium text-gray-700">Email Address</label>
                <input type="email" id="email" name="email" required 
                       class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-[#1f4e79] focus:border-[#1f4e79] sm:text-sm">
            </div>
            <div>
                <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
                <input type="password" id="password" name="password" required 
                       class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-[#1f4e79] focus:border-[#1f4e79] sm:text-sm">
            </div>
            <button type="submit" class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-[#1f4e79] hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#1f4e79]">
                Register Account
            </button>
        </form>
        <div class="text-center">
            <a href="/login" class="text-sm text-[#1f4e79] hover:text-blue-700">Already have an account? Log In</a>
        </div>
        <hr class="my-4">
        <button onclick="alert('Google OAuth flow started...')" class="w-full flex items-center justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
            <img class="h-5 w-5 mr-2" src="https://upload.wikimedia.org/wikipedia/commons/4/4a/Logo_and_wordmark_of_Google.svg" alt="Google logo">
            Sign Up with Google
        </button>
    </div>
</body>
</html>
"""

# --- Updated Homepage HTML (MINDWORK_HOMEPAGE_HTML) ---

# Replicating the previous version, but updated to direct CTAs to /login and /register
MINDWORK_HOMEPAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindWork: Academic Research & Discovery Platform</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                    },
                    // Using a deep, authoritative blue for primary focus
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
        /* Apply the Inter font globally */
        body {
            font-family: 'Inter', sans-serif;
            background-color: #ffffff;
        }
         /* --- Subtle Background Pattern for Hero Section --- */
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

    <main>
        <div class="relative overflow-hidden bg-secondary-gray">
            <div class="hero-background-pattern"></div>
            <div class="max-w-7xl mx-auto">
                <div class="relative z-10 pb-8 bg-secondary-gray bg-opacity-90 sm:pb-16 md:pb-20 lg:max-w-2xl lg:w-full lg:pb-28 xl:pb-32">
                    <div class="mt-10 mx-auto max-w-7xl px-4 sm:mt-12 sm:px-6 md:mt-16 lg:mt-20 lg:px-8 xl:mt-28">
                        <div class="sm:text-center lg:text-left">
                            <h1 class="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
                                <span class="block xl:inline">Accelerate Academic Discovery</span>
                                <span class="block text-primary-blue xl:inline"> with AI & Library Integration.</span>
                            </h1>
                            <p class="mt-3 text-base text-gray-600 sm:mt-5 sm:text-lg sm:max-w-xl sm:mx-auto md:mt-5 md:text-xl lg:mx-0">
                                **MindWork** is the unified research platform designed for students and professors, integrating real-time library access with Google Gemini's advanced analytical capabilities.
                            </p>
                              
                            <div class="mt-8 lg:mt-10 mx-auto max-w-lg lg:mx-0">
                                <label for="site-search" class="sr-only">Search the MindWork Research Hub</label>
                                <div class="relative flex items-center">
                                    <input type="text" id="site-search" placeholder="Search academic papers, concepts, or Gemini prompts..."
                                            class="w-full py-3 pl-5 pr-16 border border-gray-300 rounded-xl shadow-xl focus:ring-primary-blue focus:border-primary-blue text-lg text-black transition duration-200">
                                    <button type="submit" class="absolute right-0 top-0 bottom-0 px-4 flex items-center text-primary-blue hover:text-blue-800 transition duration-200">
                                        <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                            <div class="mt-5 sm:mt-8 sm:flex sm:justify-center lg:justify-start flex-col sm:flex-row">
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
                                    <button onclick="window.location.href='/oauth/google'" class="w-full flex items-center justify-center px-8 py-3 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 md:py-4 md:text-lg md:px-10 transition duration-300">
                                        <img class="h-5 w-5 mr-2" src="https://upload.wikimedia.org/wikipedia/commons/4/4a/Logo_and_wordmark_of_Google.svg" alt="Google logo">
                                        Sign Up with Google
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="lg:absolute lg:inset-y-0 lg:right-0 lg:w-1/2">
                <img class="h-56 w-full object-cover sm:h-72 md:h-96 lg:w-full lg:h-full" 
                    src="https://placehold.co/900x600/1f4e79/ffffff?text=Academic+Research+Hub" 
                    alt="Mockup of the MindWork research dashboard with graphs and text analysis.">
            </div>
        </div>

        <div class="py-12 bg-white">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="lg:text-center">
                    <h2 class="text-base text-primary-blue font-semibold tracking-wide uppercase">Methodology</h2>
                    <p class="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
                        Tools to Elevate Your Thesis and Papers.
                    </p>
                    <p class="mt-4 max-w-2xl text-xl text-gray-600 lg:mx-auto">
                        Seamlessly transition from discovery to final draft with integrated search, AI analysis, and citation management.
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
                                Leverage Google Gemini to summarize dense articles, outline complex arguments, and generate initial research questions from source material.
                            </dd>
                        </div>
                        
                        <div class="relative">
                            <dt>
                                <div class="absolute flex items-center justify-center h-12 w-12 rounded-lg bg-primary-blue text-white">
                                    <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-library"><path d="m16 2 4 4-4 4"></path><path d="M4.5 13.5h7c.8 0 1.5-.7 1.5-1.5v-7c0-.8-.7-1.5-1.5-1.5h-7c-.8 0-1.5.7-1.5 1.5v7c0 .8.7 1.5 1.5 1.5Z"></path><path d="M9 13v6"></path><path d="M12 19h9"></path></svg>
                                </div>
                                <p class="ml-16 text-lg leading-6 font-medium text-gray-900">Integrated Library Search</p>
                            </dt>
                            <dd class="mt-2 ml-16 text-base text-gray-600">
                                Connect directly to your university's digital library databases and public academic journals, streamlining source retrieval.
                            </dd>
                        </div>

                        <div class="relative">
                            <dt>
                                <div class="absolute flex items-center justify-center h-12 w-12 rounded-lg bg-primary-blue text-white">
                                    <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-clipboard-list"><rect width="8" height="4" x="8" y="2"></rect><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><path d="m10 13 2 2 4-4"></path></svg>
                                </div>
                                <p class="ml-16 text-lg leading-6 font-medium text-gray-900">Automated Citation & Export</p>
                            </dt>
                            <dd class="mt-2 ml-16 text-base text-gray-600">
                                Automatically generate citations (MLA, APA, Chicago) and export your research notes and drafts into common word processor formats.
                            </dd>
                        </div>
                    </dl>
                </div>
            </div>
        </div>

    </main>

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
                &copy; 2025 MindWork, Inc. Research tools for the modern academic.
            </p>
        </div>
    </footer>

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
    </script>

</body>
</html>
"""

# -------------------------------------------------------------------------
# Flask Routes
# -------------------------------------------------------------------------

@app.route('/')
def home():
    """Renders the MindWork homepage."""
    return render_template_string(MINDWORK_HOMEPAGE_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login with form submission."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # --- Authentication Logic Placeholder ---
        # In a real app, you would:
        # 1. Look up the user by email in the database.
        # 2. Verify the hashed password.
        # 3. Create a session (e.g., using flask_login or setting a cookie).
        # For this example, we just redirect.
        print(f"Attempting to log in with: {email}")
        return redirect(url_for('home')) 
        # return render_template_string(LOGIN_FORM_HTML, error="Invalid credentials") 
    
    return render_template_string(LOGIN_FORM_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles new user registration with form submission."""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # --- Registration Logic Placeholder ---
        # In a real app, you would:
        # 1. Validate email format and check if the user already exists.
        # 2. Hash the password (CRITICAL: NEVER store plain passwords).
        # 3. Save the new user record to the database.
        # 4. Log the user in or redirect to the login page.
        print(f"Attempting to register new user: {name} ({email})")
        return redirect(url_for('login')) 
        
    return render_template_string(REGISTER_FORM_HTML)

@app.route('/oauth/google')
def google_oauth():
    """
    Placeholder route for initiating the Google OAuth flow.
    
    In a real application, this route would:
    1. Construct the Google Authorization URL with required scopes.
    2. Store a state token in the user's session to prevent CSRF.
    3. Redirect the user to the Google Authorization URL.
    """
    oauth_url_placeholder = "https://accounts.google.com/o/oauth2/v2/auth?..."
    
    # For demonstration, we'll just redirect to the home page with a message
    return redirect(url_for('home'))

# -------------------------------------------------------------------------
# Application Run
# -------------------------------------------------------------------------

if __name__ == '__main__':
    print("----------------------------------------------------------")
    print("Flask Application Running Locally (via Waitress):")
    # Note the updated port in the print statement
    print("Homepage: http://0.0.0.0:5001/") 
    print("----------------------------------------------------------")
    
    # Import Waitress here
    from waitress import serve
    
    # *** THIS IS THE CRITICAL CHANGE ***
    serve(app, host='0.0.0.0', port=5001)