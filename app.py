import os
import random
from flask import Flask, render_template_string, request, redirect, url_for
# Import the Google GenAI SDK for the LLM call
from google import genai
from google.genai.errors import APIError

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
            print("Gemini client initialized successfully upon first request.")
        except Exception as e:
            _GEMINI_CLIENT = None
            _GEMINI_READY = False
            # Print failure message only once upon first use or explicit check
            print(f"Error initializing Gemini client: {e}")
    else:
        _GEMINI_CLIENT = None
        _GEMINI_READY = False
        # Only print a warning if the key is missing
        print("Warning: GEMINI_API_KEY not found. Search will use static mock data.")

    return _GEMINI_CLIENT

# -------------------------------------------------------------------------
# HTML Template Strings (UPDATED LOGO SPACING)
# -------------------------------------------------------------------------

# --- Common Footer Component (for reuse) ---
COMMON_FOOTER = """
    <footer class="bg-gray-800 mt-10">
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
            <!-- New Contact/Report Section -->
            <div class="mt-8 text-center text-base text-gray-400">
                <p>
                    For feedback, support, or to report an issue, please contact:
                    <a href="mailto:Mesadieujohnm01@gmail.com" class="text-accent-gold hover:text-yellow-300 transition duration-150 font-medium">
                        Mesadieujohnm01@gmail.com
                    </a>
                </p>
            </div>
            <p class="mt-4 text-center text-base text-gray-400">
                &copy; 2025 MindWork, Inc. Research tools for the modern explorer.
            </p>
        </div>
    </footer>
"""

# --- MODIFIED: LOGIN_FORM_HTML (Updated mr-3) ---
LOGIN_FORM_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindWork: Login</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        'primary-blue': '#1f4e79', /* Deep Navy */
                        'secondary-gray': '#f3f4f6',
                        'accent-gold': '#d9a400', /* Gold for academic accent */
                    }
                }
            }
        }
        function startMockGoogleAuth(action) {
            console.log(`Starting mock Google ${action} flow...`);
            window.location.href = '/oauth/google';
        }
    </script>
</head>
<body class="bg-gray-100 flex flex-col items-center justify-center min-h-screen">
    <div class="w-full max-w-md p-8 space-y-6 bg-white rounded-xl shadow-2xl mt-10 mb-10">
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
        <!-- MODIFIED: Log In with Google Button - Logo aligned and using mr-3 -->
        <button onclick="startMockGoogleAuth('Log In')" class="w-full flex items-center justify-center py-2 px-4 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
            <img class="h-5 w-5 mr-3" src="https://upload.wikimedia.org/wikipedia/commons/4/4a/Logo_and_wordmark_of_Google.svg" alt="Google logo">
            Log In with Google
        </button>
    </div>
"""
LOGIN_FORM_HTML += COMMON_FOOTER + "</body></html>"

# --- MODIFIED: REGISTER_FORM_HTML (Updated mr-3) ---
REGISTER_FORM_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindWork: Register</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        'primary-blue': '#1f4e79', /* Deep Navy */
                        'secondary-gray': '#f3f4f6',
                        'accent-gold': '#d9a400', /* Gold for academic accent */
                    }
                }
            }
        }
        function startMockGoogleAuth(action) {
            console.log(`Starting mock Google ${action} flow...`);
            window.location.href = '/oauth/google';
        }
    </script>
</head>
<body class="bg-gray-100 flex flex-col items-center justify-center min-h-screen">
    <div class="w-full max-w-md p-8 space-y-6 bg-white rounded-xl shadow-2xl mt-10 mb-10">
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
        <!-- MODIFIED: Sign Up with Google Button - Logo aligned and using mr-3 -->
        <button onclick="startMockGoogleAuth('Sign Up')" class="w-full flex items-center justify-center py-2 px-4 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
            <img class="h-5 w-5 mr-3" src="https://upload.wikimedia.org/wikipedia/commons/4/4a/Logo_and_wordmark_of_Google.svg" alt="Google logo">
            Sign Up with Google
        </button>
    </div>
"""
REGISTER_FORM_HTML += COMMON_FOOTER + "</body></html>"

# --- MODIFIED: MINDWORK_HOMEPAGE_HTML (Confirming logo alignment) ---
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
        /* New styles for the camera modal */
        .camera-modal-backdrop {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.75);
            z-index: 1000;
            display: none; /* Controlled by JS */
            justify-content: center;
            align-items: center;
        }
        .camera-modal-content {
            background: white;
            border-radius: 1rem;
            max-width: 90%;
            max-height: 90%;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        #camera-stream {
            display: block;
            width: 100%;
            max-height: 70vh;
            object-fit: contain; /* Ensures the whole video is visible */
        }
    </style>
</head>
<body class="antialiased flex flex-col min-h-screen">

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

    <main class="flex-grow">
        <div class="relative overflow-hidden bg-secondary-gray">
            <div class="hero-background-pattern"></div>
            <div class="max-w-7xl mx-auto">
                <div class="relative z-10 pb-8 bg-secondary-gray bg-opacity-90 sm:pb-16 md:pb-20 lg:max-w-2xl lg:w-full lg:pb-28 xl:pb-32">
                    <div class="mt-10 mx-auto max-w-7xl px-4 sm:mt-12 sm:px-6 md:mt-16 lg:mt-20 lg:px-8 xl:mt-28">
                        <div class="sm:text-center lg:text-left">
                            <h1 class="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
                                <span class="block xl:inline">Find Everything. Analyze Anything.</span>
                                <!-- Updated: Decreased text size to sm:text-4xl md:text-5xl -->
                                <span class="block text-primary-blue xl:inline sm:text-4xl md:text-5xl"> General & AI-Powered Research.</span> 
                            </h1>
                            <p class="mt-3 text-base text-gray-600 sm:mt-5 sm:text-lg sm:max-w-xl sm:mx-auto md:mt-5 md:text-xl lg:mx-0">
                                **MindWork** is your universal discovery platform, combining wide-ranging web search results with Google Gemini's powerful analytical capabilities for every query.
                            </p>
                              
                            <div class="mt-8 lg:mt-10 mx-auto max-w-lg lg:mx-0">
                                <form method="GET" action="/search">
                                    <label for="site-search" class="sr-only">Search the MindWork Research Hub</label>
                                    <div class="relative flex items-center">
                                        <!-- Plus Button (Absolute Left) and Dropdown Container -->
                                        <div class="absolute left-0 top-0 bottom-0 z-10">
                                            <div class="h-full flex items-center pl-3">
                                                <button type="button" id="upload-menu-button" onclick="toggleUploadMenu(event)" 
                                                        class="p-1 text-primary-blue rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-blue transition duration-200">
                                                    <!-- Plus Symbol SVG -->
                                                    <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                                                    </svg>
                                                </button>
                                            </div>

                                            <!-- Dropdown Menu -->
                                            <div id="upload-menu" class="origin-top-left absolute left-0 mt-1 w-56 rounded-xl shadow-2xl bg-white ring-1 ring-black ring-opacity-5 divide-y divide-gray-100 hidden z-20" role="menu" aria-orientation="vertical" aria-labelledby="upload-menu-button">
                                                <div class="py-1" role="none">
                                                    <!-- Option 1: Upload Pictures/Files -->
                                                    <!-- Hidden file input for actual selection -->
                                                    <input type="file" id="file-upload-input" accept="image/*, .pdf, .docx, .txt" class="hidden" onchange="handleFileUpload(event)">
                                                    
                                                    <a href="#" class="flex items-center px-4 py-3 text-sm text-gray-700 hover:bg-gray-100 hover:text-primary-blue rounded-t-xl" role="menuitem" onclick="document.getElementById('file-upload-input').click(); toggleUploadMenu(); return false;">
                                                        <svg class="mr-3 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-upload"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
                                                        Upload Pictures/Files
                                                    </a>
                                                    
                                                    <!-- Option 2: Take Photo (calls new JS function) -->
                                                    <a href="#" class="flex items-center px-4 py-3 text-sm text-gray-700 hover:bg-gray-100 hover:text-primary-blue rounded-b-xl" role="menuitem" onclick="startCameraModal(); toggleUploadMenu(); return false;">
                                                        <svg class="mr-3 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-camera"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>
                                                        Take Photo
                                                    </a>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Search Input: Note the increased left padding (pl-16) -->
                                        <input type="text" id="site-search" name="query" placeholder="Search anything: general topics, media, concepts, or ask Gemini..."
                                                class="w-full py-3 pl-16 pr-16 border border-gray-300 rounded-xl shadow-xl focus:ring-primary-blue focus:border-primary-blue text-lg text-black transition duration-200"
                                                required>
                                        
                                        <!-- Search Icon Button -->
                                        <button type="submit" class="absolute right-0 top-0 bottom-0 px-4 flex items-center text-primary-blue hover:text-blue-800 transition duration-200">
                                            <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                            </svg>
                                        </button>
                                    </div>
                                </form>
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
                                    <!-- CONFIRMED: Sign Up with Google Button with correct flex/logo alignment (mr-3) -->
                                    <button onclick="startMockGoogleAuth('Sign Up')" class="w-full flex items-center justify-center px-8 py-3 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 md:py-4 md:text-lg md:px-10 transition duration-300">
                                        <img class="h-5 w-5 mr-3" src="https://upload.wikimedia.org/wikipedia/commons/4/4a/Logo_and_wordmark_of_Google.svg" alt="Google logo">
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
                    src="https://placehold.co/900x600/1f4e79/ffffff?text=General+Research+Hub" 
                    alt="Mockup of the MindWork research dashboard with graphs and text analysis.">
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
                                Leverage Google Gemini to summarize dense topics, outline complex arguments, and generate initial research questions from any source.
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
        
        <!-- HIDDEN CAMERA VIDEO AND CANVAS ELEMENTS -->
        <video id="camera-stream" autoplay playsinline class="hidden"></video>
        <canvas id="camera-canvas" class="hidden"></canvas>

        <!-- CAMERA MODAL (Hidden by default) -->
        <div id="camera-modal" class="camera-modal-backdrop">
            <div class="camera-modal-content">
                <div class="p-4 bg-primary-blue text-white flex justify-between items-center rounded-t-xl">
                    <h3 class="text-xl font-semibold">Live Camera Feed</h3>
                    <button onclick="stopCamera()" class="text-white hover:text-gray-300">
                        <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                </div>
                <!-- The camera stream will play in this video tag -->
                <video id="camera-live-feed" autoplay playsinline class="w-full h-full bg-gray-900"></video>
                <div class="p-4 flex justify-center bg-white rounded-b-xl">
                    <!-- Capture Button -->
                    <button onclick="capturePhoto()" class="py-3 px-6 bg-accent-gold text-white font-bold rounded-full shadow-lg hover:bg-yellow-600 transition duration-200 flex items-center">
                        <svg class="mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M3 3h18a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zm9 4a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0 2a3 3 0 1 1 0 6 3 3 0 0 1 0-6z"/></svg>
                        Capture Photo
                    </button>
                </div>
            </div>
        </div>

    </main>
    
    <script>
        let currentStream; // Global variable to hold the MediaStream object

        // --- NEW/MODIFIED: Authentication Mock Function ---
        function startMockGoogleAuth(action) {
            console.log(`MOCK: Initiating Google ${action} flow. Redirecting to home...`);
            // This URL hits the Flask route which just logs and redirects back to home
            window.location.href = '/oauth/google';
        }
        
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
                // In a real application, this file would be uploaded for Gemini vision/document analysis.
                const searchInput = document.getElementById('site-search');
                // Use a placeholder query to signify an analysis request
                searchInput.value = `Analyze file: ${file.name}`;
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
        
        // --- CAMERA FUNCTIONALITY ---

        function startCameraModal() {
            const modal = document.getElementById('camera-modal');
            const video = document.getElementById('camera-live-feed');
            
            // 1. Check for camera support
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                console.error('Camera API not supported in this browser.');
                // Fallback to a custom message (not using alert() per instructions)
                document.getElementById('site-search').value = "Error: Camera access required but not supported by device.";
                return;
            }

            // 2. Request access and start stream
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(stream => {
                    currentStream = stream;
                    video.srcObject = stream;
                    modal.style.display = 'flex'; // Show the modal
                })
                .catch(err => {
                    console.error('Failed to access camera: ', err);
                    document.getElementById('site-search').value = "Error: Camera access denied or unavailable. Please check permissions.";
                });
        }
        
        function stopCamera() {
            const modal = document.getElementById('camera-modal');
            
            if (currentStream) {
                currentStream.getTracks().forEach(track => track.stop());
                currentStream = null;
            }
            modal.style.display = 'none'; // Hide the modal
        }
        
        function capturePhoto() {
            const video = document.getElementById('camera-live-feed');
            const canvas = document.getElementById('camera-canvas');
            const context = canvas.getContext('2d');
            const searchInput = document.getElementById('site-search');
            
            // 1. Set canvas dimensions to match the video feed dimensions
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            // 2. Draw the current video frame onto the canvas
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // 3. Convert the canvas image to a data URL (base64)
            // In a real app, this data URL would be sent to the backend for Gemini Vision analysis.
            const imageDataUrl = canvas.toDataURL('image/jpeg'); 
            
            // 4. Stop the camera and close the modal
            stopCamera();
            
            // 5. Simulate submission by populating the search bar and submitting
            // Note: Since we can't send the image data to the server easily in this structure,
            // we submit a query signaling an image was captured.
            searchInput.value = "Analyze captured image (JPEG)"; 
            document.querySelector('form').submit(); 
        }

    </script>
"""
MINDWORK_HOMEPAGE_HTML += COMMON_FOOTER + "</body></html>"


SEARCH_RESULTS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindWork: Search Results for '{{ query }}'</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
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
        .result-card { border-left: 4px solid #1f4e79; }
        .ai-notice { background-color: #e6f7ff; border-color: #b3e0ff; }
    </style>
</head>
<body class="bg-gray-50 antialiased min-h-screen flex flex-col">
    <header class="bg-white shadow-lg">
        <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
            <a href="/" class="text-2xl font-extrabold text-[#1f4e79]">MindWork</a>
            <a href="/login" class="text-sm font-medium text-white bg-[#1f4e79] hover:bg-blue-800 px-4 py-2 rounded-lg">Login / Sign Up</a>
        </div>
    </header>

    <main class="max-w-4xl mx-auto mt-10 p-6 bg-white shadow-xl rounded-xl flex-grow w-full">
        <h1 class="text-3xl font-bold text-gray-900 mb-6">
            Search Results for: "<span class="text-[#1f4e79]">{{ query }}</span>"
        </h1>
        
        {% if gemini_active %}
        <div class="ai-notice p-4 rounded-lg border mb-8 text-gray-700">
            🤖 Results include **AI-generated summaries** from Google Gemini and **100+ mock web links and analysis**.
        </div>
        {% endif %}

        <p class="mb-8 text-lg text-gray-600">
            Found **{{ results|length }}** relevant entries and AI analyses.
        </p>

        {% if results %}
            <div class="space-y-6">
                {% for result in results %}
                    <div class="p-4 bg-white shadow-md rounded-lg result-card border-l-4">
                        <h2 class="text-xl font-semibold text-gray-900 hover:text-blue-700">
                            <a href="#">{{ result.title }}</a>
                        </h2>
                        <p class="text-sm text-gray-500 mt-1">
                            {{ result.author }} | {{ result.year }} | {{ result.source }}
                        </p>
                        <p class="text-base text-gray-700 mt-2">
                            {{ result.summary }}
                        </p>
                    </div>
                {% endfor %}
            </div>
        {% else %}
            <div class="p-8 text-center bg-yellow-50 rounded-lg border border-yellow-200">
                <p class="text-xl text-yellow-800">
                    ⚠️ No results were found for "{{ query }}".
                </p>
                <p class="mt-2 text-gray-600">
                    Try a different query or check the console for Gemini API errors.
                </p>
            </div>
        {% endif %}

    </main>
"""
SEARCH_RESULTS_HTML += COMMON_FOOTER + "</body></html>"


# -------------------------------------------------------------------------
# Helper Functions for Search Simulation (Updated to use get_gemini_client)
# -------------------------------------------------------------------------

def generate_general_results(query, count=105):
    """
    Generates a large, diverse list of mock search results based on the query.
    """
    common_subjects = ["Photography", "Cooking", "Travel Guides", "History", "Coding Tutorials", "Fitness", "Personal Finance", "Gardening", "Science News", "Music Theory", "World Events", "Home Decor", "Gaming", "DIY Projects"]
    common_formats = ["How to", "Best 10", "A Deep Dive into", "The Ultimate Guide to", "Review:", "Top 5 Mistakes in", "Beginner's Guide to", "Quick Start:", "Comprehensive FAQ on"]
    common_authors = ["Jane Doe", "John Smith", "The Daily Explorer", "Tech Guru", "Culinary Arts", "Historian Guy", "DIY Master", "Financial Freedom Blog"]
    
    results = []
    for i in range(count):
        subject = random.choice(common_subjects)
        format_type = random.choice(common_formats)
        year = random.randint(2015, 2025)
        
        # Create a title that includes the query
        if i < 5:
             # Ensure the first few results are highly relevant to the core query
            title = f"The Essential Guide to {query}: History, Use, and Future"
            source = f"Top-Tier Site {random.randint(1, 3)}"
        elif i % 5 == 0:
            title = f"{format_type} {subject}: The Impact of '{query}'"
            source = f"Specialist Blog {random.randint(1, 10)}"
        else:
            title = f"{format_type} {query} in {subject}"
            source = f"Web Source {random.randint(11, 50)}"
        
        results.append({
            "title": title,
            "author": random.choice(common_authors),
            "year": year,
            "source": source,
            "summary": f"This article discusses the wide-ranging implications and applications of {query} within the domain of {subject}, providing comprehensive examples and case studies. This is result number {i+1}."
        })
    # Remove duplicates which can happen in the first 5 entries
    return list({v['title']:v for v in results}.values())


def generate_gemini_result(client, query):
    """
    Calls the Gemini API to generate a mock general search result.
    """
    if not client:
        return None
    
    # Check if the query indicates a file/image analysis
    if query.lower().startswith("analyze file:") or query.lower().startswith("analyze captured image"):
        # For a mock, we'll pretend the analysis happened
        mock_title = "AI Vision Analysis: Detailed Object Identification"
        
        if query.lower().startswith("analyze captured image"):
            mock_summary = "An initial AI-driven analysis suggesting key objects, text, and visual context captured by the device camera. Further interactive prompting is recommended for deeper insights."
        else:
            file_name = query.split(":")[1].strip()
            mock_summary = f"An initial AI-driven summary suggesting key concepts, visual elements, and potential research applications based on the content of the uploaded file/image '{file_name}'. Further interactive prompting is highly recommended."
            
        return {
            "title": mock_title,
            "author": "Gemini AI",
            "year": 2025,
            "source": "Multimodal Analysis (AI-Generated)",
            "summary": mock_summary
        }


    prompt = (
        f"Generate a mock general web search result for a research platform based on the user's query: '{query}'. "
        "The result should be highly informative and non-academic (like a Wikipedia entry or a detailed blog post summary). "
        "The response must be in the exact format: "
        "TITLE: [Webpage Title]\nAUTHOR: [Website/Creator Name]\nYEAR: [Year]\nSOURCE: [Website URL/Domain]\nSUMMARY: [Snippet/Summary of the content]"
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
            return {
                "title": data['TITLE'],
                "author": data['AUTHOR'],
                "year": data['YEAR'],
                "source": data['SOURCE'] + " (AI-Generated)", # Mark it as AI
                "summary": data['SUMMARY']
            }
            
    except APIError as e:
        print(f"Gemini API Error: {e}")
        return None
    except Exception as e:
        print(f"General Error during Gemini call: {e}")
        return None
        
    return None

# -------------------------------------------------------------------------
# Flask Routes (Unchanged)
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
    # Simulate a brief OAuth handshake before redirecting to home
    print("MOCK: Successful Google OAuth handshake simulated.")
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

    # Get the client instance (initializes only on first call)
    client = get_gemini_client()
    gemini_active = client is not None

    # --- 1. General Search Simulation (Generates 100+ Diverse Results) ---
    all_results = generate_general_results(query, count=105) 

    # --- 2. Gemini Generative Result (The main, featured result) ---
    if gemini_active:
        gemini_result = generate_gemini_result(client, query)
        if gemini_result:
            # Insert the single AI result at the very top (index 0)
            all_results.insert(0, gemini_result) 
        
    # Shuffle the mock results for variety (excluding the first one if it's the AI result)
    if gemini_active and len(all_results) > 1:
        featured_ai = all_results[0]
        general_results = all_results[1:]
        random.shuffle(general_results)
        all_results = [featured_ai] + general_results
    else:
        # If no Gemini, shuffle all general results
        random.shuffle(all_results)
    
    # Ensure a maximum of 100 results are displayed to keep the page size manageable,
    # though the mock generator produces more than 100.
    final_results = all_results[:100]

    return render_template_string(
        SEARCH_RESULTS_HTML,
        query=query,
        results=final_results,
        gemini_active=gemini_active # Pass the local state
    )


# -------------------------------------------------------------------------
# Application Run
# -------------------------------------------------------------------------

if __name__ == '__main__':
    print("----------------------------------------------------------")
    print("Flask Application Running Locally (via Waitress):")
    print("Homepage: https://mind-work.onrender.com/")
    
    # Check the final readiness state before serving
    initial_client = get_gemini_client()
    initial_ready = initial_client is not None
    print(f"Gemini Status: {'✅ Active' if initial_ready else '❌ Inactive (Set GEMINI_API_KEY)'}")
    print("----------------------------------------------------------")
    
    from waitress import serve
    serve(app, host='0.0.0.0', port=5001)
