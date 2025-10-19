import os
import random
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
if GEMINI_API_KEY:
    try:
        client = genai.Client()
        GEMINI_CLIENT_READY = True
        print("Gemini client initialized successfully.")
    except Exception as e:
        client = None
        GEMINI_CLIENT_READY = False
        print(f"Error initializing Gemini client: {e}")
else:
    client = None
    GEMINI_CLIENT_READY = False
    print("Warning: GEMINI_API_KEY not found. Search will use static mock data.")

# -------------------------------------------------------------------------
# HTML Template Strings (DEFINED BEFORE USE TO RESOLVE PYLANCE ERROR)
# -------------------------------------------------------------------------

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
        <button onclick="console.log('Google OAuth flow started...')" class="w-full flex items-center justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
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
        <button onclick="console.log('Google OAuth flow started...')" class="w-full flex items-center justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
            <img class="h-5 w-5 mr-2" src="https://upload.wikimedia.org/wikipedia/commons/4/4a/Logo_and_wordmark_of_Google.svg" alt="Google logo">
            Sign Up with Google
        </button>
    </div>
</body>
</html>
"""

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
                                                    
                                                    <!-- Option 2: Take Photo -->
                                                    <a href="#" class="flex items-center px-4 py-3 text-sm text-gray-700 hover:bg-gray-100 hover:text-primary-blue rounded-b-xl" role="menuitem" onclick="alert('Note: This would integrate your device camera for a direct search!'); toggleUploadMenu(); return false;">
                                                        <svg class="mr-3 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-camera"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>
                                                        Take Photo
                                                    </a>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Search Input: Note the increased left padding (pl-16) -->
                                        <input type="text" id="site-search" name="query" placeholder="Search academic papers, concepts, or Gemini prompts..."
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

    </script>

</body>
</html>
"""

SEARCH_RESULTS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindWork: Search Results for '{{ query }}'</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .result-card { border-left: 4px solid #1f4e79; }
        .ai-notice { background-color: #e6f7ff; border-color: #b3e0ff; }
    </style>
</head>
<body class="bg-gray-50 antialiased min-h-screen">
    <header class="bg-white shadow-lg">
        <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
            <a href="/" class="text-2xl font-extrabold text-[#1f4e79]">MindWork</a>
            <a href="/login" class="text-sm font-medium text-white bg-[#1f4e79] hover:bg-blue-800 px-4 py-2 rounded-lg">Login / Sign Up</a>
        </div>
    </header>

    <main class="max-w-4xl mx-auto mt-10 p-6 bg-white shadow-xl rounded-xl">
        <h1 class="text-3xl font-bold text-gray-900 mb-6">
            Search Results for: "<span class="text-[#1f4e79]">{{ query }}</span>"
        </h1>
        
        {% if gemini_active %}
        <div class="ai-notice p-4 rounded-lg border mb-8 text-gray-700">
            🤖 Results include **AI-generated summaries** from Google Gemini and mock academic citations.
        </div>
        {% endif %}

        <p class="mb-8 text-lg text-gray-600">
            Found **{{ results|length }}** relevant academic entries and AI analyses.
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
                    ⚠️ No academic or AI results were found for "{{ query }}".
                </p>
                <p class="mt-2 text-gray-600">
                    Try a different query or check the console for Gemini API errors.
                </p>
            </div>
        {% endif %}

    </main>

</body>
</html>
"""


# -------------------------------------------------------------------------
# Helper Function for Gemini Search
# -------------------------------------------------------------------------

def generate_gemini_result(client, query):
    """
    Calls the Gemini API to generate a mock academic paper result.
    """
    if not client:
        return None
    
    # Check if the query indicates a file/image analysis
    if query.lower().startswith("analyze file:"):
        # For a mock, we'll pretend the analysis happened
        file_name = query.split(":")[1].strip()
        mock_title = f"Preliminary Analysis of '{file_name}'"
        mock_summary = f"An initial AI-driven summary suggesting key concepts and potential research applications based on the content of the uploaded file/image. Further interactive prompting is recommended."
        return {
            "title": mock_title,
            "author": "Gemini AI",
            "year": 2025,
            "source": "Multimodal Analysis (AI-Generated)",
            "summary": mock_summary
        }


    prompt = (
        f"Generate a mock academic paper for a research platform based on the user's query: '{query}'. "
        "The response must be in the format: "
        "TITLE: [Title]\nAUTHOR: [Author Name]\nYEAR: [Year]\nSOURCE: [Source/Journal Name]\nSUMMARY: [Abstract/Summary of the paper]"
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
# Flask Routes
# -------------------------------------------------------------------------

@app.route('/')
def home():
    """Renders the MindWork homepage. The HTML variable is now defined globally."""
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
    return redirect(url_for('home'))


@app.route('/search', methods=['GET'])
def search():
    """
    Handles academic search queries, including a call to Google Gemini.
    """
    query = request.args.get('query', '').strip()
    all_results = []
    
    if not query:
        # Return to homepage if query is empty
        return redirect(url_for('home'))
    
    # --- 1. Library Simulation (Mock Data) ---
    MOCK_DATABASE = [
        {"title": "The Evolutionary Basis of Consciousness and Life", "author": "Dr. E. Hamilton", "year": 2021, "source": "Journal of Bio-Philosophy", "summary": "An analysis of the conditions required for self-sustaining biological systems and the emergence of sentience, bridging physics and biology."},
        {"title": "The Meaning of Life: A Comparative Philosophical Study", "author": "P. M. Reynolds", "year": 2018, "source": "Oxford University Press", "summary": "Examines existential, nihilistic, and religious perspectives on purpose, focusing on texts from 19th-century Europe to modern-day Asia."},
        {"title": "A Guide to Sustainable Urban Life: Planning for 2050", "author": "J. K. Singh", "year": 2023, "source": "Future Studies Quarterly", "summary": "Proposes actionable steps for municipalities to create eco-friendly, energy-efficient, and socially equitable urban environments."}
    ]
    
    # Filter mock data based on query (a real app would use a database)
    filtered_mock_results = [
        r for r in MOCK_DATABASE
        if query.lower() in r['title'].lower() or query.lower() in r['summary'].lower()
    ]
    all_results.extend(filtered_mock_results)

    # --- 2. Gemini Generative Result ---
    if GEMINI_CLIENT_READY:
        gemini_result = generate_gemini_result(client, query)
        if gemini_result:
            all_results.insert(0, gemini_result) # Add the AI result at the top
        
    # Shuffle the results (for non-critical results) or keep the AI one at the top
    if len(all_results) > 1 and GEMINI_CLIENT_READY:
        # Keep the Gemini result at index 0 and shuffle the rest
        library_results = all_results[1:]
        random.shuffle(library_results)
        all_results = [all_results[0]] + library_results
    elif len(all_results) > 0 and not GEMINI_CLIENT_READY:
        # If no Gemini, shuffle all mock results
        random.shuffle(all_results)


    return render_template_string(
        SEARCH_RESULTS_HTML,
        query=query,
        results=all_results,
        gemini_active=GEMINI_CLIENT_READY
    )


# -------------------------------------------------------------------------
# Application Run
# -------------------------------------------------------------------------

if __name__ == '__main__':
    print("----------------------------------------------------------")
    print("Flask Application Running Locally (via Waitress):")
    print("Homepage: https://mind-work.onrender.com/")
    print(f"Gemini Status: {'✅ Active' if GEMINI_CLIENT_READY else '❌ Inactive (Set GEMINI_API_KEY)'}")
    print("----------------------------------------------------------")
    
    from waitress import serve
    serve(app, host='0.0.0.0', port=5001)
