import os
import argparse
from google import genai
from google.genai import types
from google.genai.errors import APIError

# --- Configuration and Initialization ---

# Define the model to use. gemini-2.5-pro is excellent for complex research and analysis.
MODEL_NAME = "gemini-2.5-pro"

def initialize_client():
    """
    Initializes and returns the Gemini API client.
    Requires the GEMINI_API_KEY environment variable to be set.
    """
    try:
        # The client automatically picks up the API key from the GEMINI_API_KEY environment variable.
        client = genai.Client()
        return client
    except Exception as e:
        print("Error: Could not initialize the Gemini Client.")
        print(f"Please ensure you have set the GEMINI_API_KEY environment variable correctly.")
        print(f"Details: {e}")
        return None

def run_research_app(client: genai.Client, prompt: str):
    """
    Generates content based on the prompt using the specified model,
    enabling Google Search as a grounding tool for up-to-date information.
    """
    print(f"\n--- Research Assistant Active (Model: {MODEL_NAME}) ---\n")
    print(f"Query: {prompt}\n")
    print("Searching the web for grounding information...")

    # 1. Define the Google Search tool for grounding (real-time information)
    google_search_tool = types.Tool.google_search()

    # 2. Configure the generation request
    config = types.GenerateContentConfig(
        tools=[google_search_tool],
        # Add a system instruction to define the persona and output style
        system_instruction=(
            "You are an expert AI Research Analyst. Your task is to provide comprehensive, "
            "well-structured, and factual answers based on your knowledge and the provided search results. "
            "Always cite your sources clearly if external knowledge is used."
        )
    )

    try:
        # 3. Call the API
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt],
            config=config,
        )

        # 4. Process and display the generated content
        print("\n--- Generated Analysis ---")
        print(response.text)

        # 5. Extract and display grounding sources (citations)
        if (response.candidates and
            response.candidates[0].grounding_metadata and
            response.candidates[0].grounding_metadata.grounding_attributions):

            print("\n--- Grounding Sources (Citations) ---")
            sources = response.candidates[0].grounding_metadata.grounding_attributions
            
            # Use a set to store unique URIs to avoid duplicates
            unique_sources = {} 
            for attribution in sources:
                if attribution.web:
                    uri = attribution.web.uri
                    title = attribution.web.title
                    if uri not in unique_sources:
                         unique_sources[uri] = title

            for i, (uri, title) in enumerate(unique_sources.items()):
                print(f"{i+1}. {title} - {uri}")
        
        print("\n--------------------------------------\n")

    except APIError as e:
        print(f"\nAn API Error occurred: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")


if __name__ == "__main__":
    # Setup command-line argument parser
    parser = argparse.ArgumentParser(
        description="A simple command-line AI Research Application using the Gemini API."
    )
    parser.add_argument(
        "prompt",
        type=str,
        help="The research query or prompt you want the AI to analyze."
    )
    args = parser.parse_args()

    # Check for API Key before starting
    if "GEMINI_API_KEY" not in os.environ:
        print("CRITICAL ERROR: The GEMINI_API_KEY environment variable is not set.")
        print("Please set your API key to run the application.")
    else:
        # Run the application
        gemini_client = initialize_client()
        if gemini_client:
            run_research_app(gemini_client, args.prompt)
