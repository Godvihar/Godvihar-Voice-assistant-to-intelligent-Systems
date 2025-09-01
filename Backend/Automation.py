from AppOpener import close, open as appopen  # Import functions to open and close apps.
from webbrowser import open as webopen        # Import web browser functionality.
try:
    from pywhatkit import search, playonyt         # Import functions for Google search and YouTube playback.
    from pywhatkit.core.exceptions import InternetException
except ImportError:
    search = None
    playonyt = None
    InternetException = None
    print("[WARNING] pywhatkit not available. Some features may not work without internet connection.")
from dotenv import dotenv_values               # Import dotenv to manage environment variables.
from bs4 import BeautifulSoup                  # Import BeautifulSoup for parsing HTML content.
from rich import print                         # Import rich for styled console output.
from groq import Groq                          # Import Groq for AI chat functionalities.
import webbrowser                              # Import webbrowser for opening URLs.
import subprocess                              # Import subprocess for interacting with the system.
import requests                                # Import requests for making HTTP requests.
import keyboard                                # Import keyboard for keyboard-related actions.
import asyncio                                 # Import asyncio for asynchronous programming.
import os                                      # Import os for operating system functionalities.
from fpdf import FPDF                          # Import FPDF for PDF creation.

# Load environment variables from the env file.
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")        # Retrieve the Groq API key.

# Define CSS classes for parsing specific elements in HTML content.
classes = [
    "zCubwf", "hgKElc", "LTKOO sY7ric", "ZOLcW", "gsrt vk_bk FzvWSb YwPhnf", "pclqee",
    "tw-Data-text tw-text-small tw-ta", "IZ6rdc", "05uR6d LTKOO", "vlzY6d",
    "webanswers-webanswers_table_webanswers-table", "dDoNo ikb4Bb gsrt", "sXLa0e",
    "LWkfKe", "VQF4g", "qv3Wpe", "kno-rdesc", "SPZz6b"
]

# Define a user-agent for making web requests.
useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'
client = Groq(api_key=GroqAPIKey)

# Predefined professional responses for user interactions.
professional_responses = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need—don't hesitate to ask."
]

# List to store chatbot messages.
messages = []

# System message to provide context to the chatbot.
SystemChatBot = [{
    "role": "system",
    "content": f"Hello, I am {os.environ['Username']}, You're a content writer. You have to write content like letters, codes, applications, essays, notes, songs, poems etc."
}]

# Function to perform a Google search.
def GoogleSearch(Topic):
    search(Topic)  # Use pywhatkit's search function to perform a Google search.
    return True    # Indicate success.

# Function to generate content using AI and save it to a file.
def Content(Topic):

    # Nested function to open a file in Notepad.
    def OpenNotepad(File):
        default_text_editor = 'notepad.exe'
        subprocess.Popen([default_text_editor, File])  # Open the file in Notepad.

    # Nested function to generate content using the AI chatbot.
    def ContentWriterAI(prompt):
        messages.append({"role": "user", "content": f"{prompt}"})  # Add the user's prompt to messages.

        completion = client.chat.completions.create(
           model="llama3-8b-8192",  # Specify the AI model.
            messages=SystemChatBot + messages,  # Include system instructions and chat history.
            max_tokens=2048,  # Limit the maximum tokens in the response.
            temperature=0.7,  # Adjust response randomness.
            top_p=1,  # Use nucleus sampling for response diversity.
            stream=True,  # Enable streaming response.
            stop=None  # Allow the model to determine stopping conditions.
        )

        Answer = ""  # Initialize an empty string for the response.

        # Process streamed response chunks.
        for chunk in completion:
            if chunk.choices[0].delta.content:  # Check for content in the current chunk.
                Answer += chunk.choices[0].delta.content  # Append the content to the answer.

        Answer = Answer.replace("</s>", "")  # Remove unwanted tokens from the response.
        messages.append({"role": "assistant", "content": Answer})  # Add the AI's response to messages.
        return Answer

    Topic = Topic.replace("Content", "")  # Remove "Content" from the topic.
    ContentByAI = ContentWriterAI(Topic)  # Generate content using AI.

    # Save the generated content to a text file.
    with open(rf"Data\{Topic.lower().replace(' ', '')}.txt", "w", encoding="utf-8") as file:
        file.write(ContentByAI)  # Write the content to the file.
        file.close()

    OpenNotepad(rf"Data\{Topic.lower().replace(' ', '')}.txt")  # Open the file in Notepad.
    return True  # Indicate success.

# Function to search for a topic on YouTube.
def YouTubeSearch(Topic):
    Url4Search = f"https://www.youtube.com/results?search_query={Topic}"  # Construct the YouTube search URL.
    webbrowser.open(Url4Search)  # Open the search URL in a web browser.
    return True  # Indicate success.

# Function to play a video on YouTube.
def PlayYoutube(query):
    playonyt(query)  # Use pywhatkit's playonyt function to play the video.
    return True  # Indicate success.

def OpenApp(app, sess=requests.session()):
    try:
        # Attempt to open the app using AppOpener
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True  

    except:
        def extract_links(html):
            if html is None:
                return []
            soup = BeautifulSoup(html, 'html.parser')  # Parse the HTML content
            links = soup.find_all('a', {'jsname': 'UwckNb'})  # Find relevant links
            return [link.get('href') for link in links]  # Return the links

        # Nested function to perform a Google search and retrieve HTML
        def search_google(query):
            # Construct the Google search URL
            url = f"https://www.google.com/search?q={query}"
            headers = {"User-Agent": useragent}  # Use the predefined user-agent
            response = sess.get(url, headers=headers)  # Perform the GET request

            if response.status_code == 200:
                return response.text  # Return the HTML content
            else:
                print("[ERROR] Failed to retrieve search results for {query}")
                return None

        html = search_google(app)  # Perform the Google search

        if html:
            links = extract_links(html)
            if links:
                link = links[0]  # Get the first valid link
                webbrowser.open(link)  # Open the link in the browser
                return True  # Successfully opened the link
            else:
                print(f"[ERROR] No links found when searching for: {app}")
                return False  # No links found
        else:
            print(f"[ERROR] Failed to get HTML for: {app}")
            return False  # Failed to retrieve search results

# Function to close an application.
def CloseApp(app):
    if "chrome" in app:
        pass  # Skip if the app is Chrome.
    else:
        try:
            close(app, match_closest=True, output=True, throw_error=True)  # Attempt to close the app.
            return True  # Indicate success.
        except:
            return False  # Indicate failure.

# Function to execute system-level commands.
def System(command):

    # Nested function to mute the system volume.
    def mute():
        keyboard.press_and_release("volume mute")  # Simulate the mute key press.

    # Nested function to unmute the system volume.
    def unmute():
        keyboard.press_and_release("volume mute")  # Simulate the unmute key press.

    # Nested function to increase the system volume.
    def volume_up():
        keyboard.press_and_release("volume up")  # Simulate the volume up key press.

    # Nested function to decrease the system volume.
    def volume_down():
        keyboard.press_and_release("volume down")  # Simulate the volume down key press.

    # Execute the appropriate command.
    if command == "mute":
        mute()
    elif command == "unmute":
        unmute()
    elif command == "volume up":
        volume_up()
    elif command == "volume down":
        volume_down()

    return True  # Indicate success.

def ConvertToPDF(command):
    topic = command.replace("convert to pdf", "").strip()
    if not topic:
        print("[ERROR] No topic provided to convert into PDF.")
        return False

    filename_txt = rf"Data\{topic.lower().replace(' ', '')}.txt"

    # Check if content file exists
    if not os.path.exists(filename_txt):
        print(f"[ERROR] No content file found for '{topic}'. Please create content first.")
        return False

    # Read text content from file
    with open(filename_txt, "r", encoding="utf-8") as file:
        content = file.read()

    # Create PDF from the content
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    lines = content.split('\n')
    for line in lines:
        pdf.multi_cell(0, 10, line)

    filename_pdf = rf"Data\{topic.lower().replace(' ', '')}.pdf"
    os.makedirs("Data", exist_ok=True)
    pdf.output(filename_pdf)

    subprocess.Popen(['start', '', filename_pdf], shell=True)
    print(f"[SUCCESS] PDF created: {filename_pdf}")
    return True

async def TranslateAndExecute(commands: list[str]):

    funcs = []  

    for command in commands:
       
        if command.startswith("open"):  # Handle "open" commands.
            if "open it" in command:  # Ignore "open it" commands.
                pass
            elif "open file" in command:  # Ignore "open file" commands.
                pass
            else:
                fun = asyncio.to_thread(OpenApp, command.removeprefix("open"))  # Schedule app opening.
                funcs.append(fun)

        elif command.startswith("general"):  # Placeholder for general commands.
            pass

        elif command.startswith("realtime "):  # Placeholder for real-time commands.
            pass

        elif command.startswith("close"):  # Handle "close" commands.
            fun = asyncio.to_thread(CloseApp, command.removeprefix("close"))  # Schedule app closing.
            funcs.append(fun)

        elif command.startswith("play "):  # Handle "play" commands.
            fun = asyncio.to_thread(PlayYoutube, command.removeprefix("play"))  # Schedule YouTube playback.
            funcs.append(fun)

        elif command.startswith("content"):  # Handle content commands.
            fun = asyncio.to_thread(Content, command.removeprefix("content"))  # Schedule content creation.
            funcs.append(fun)

        elif command.startswith("google search"):  # Handle Google search commands.
            fun = asyncio.to_thread(GoogleSearch, command.removeprefix("google search"))  # Schedule Google search.
            funcs.append(fun)

        elif command.startswith("youtube search"):  # Handle YouTube search commands.
            fun = asyncio.to_thread(YouTubeSearch, command.removeprefix("youtube search"))  # Schedule YouTube search.
            funcs.append(fun)

        elif command.startswith("convert to pdf"):  # Handle PDF conversion command.
            fun = asyncio.to_thread(ConvertToPDF, command)
            funcs.append(fun)

        elif command.startswith("system"):  # Handle system commands.
            fun = asyncio.to_thread(System, command.removeprefix("system"))  # Schedule system command.
            funcs.append(fun)
        # ... other elif blocks ...

        elif "send_email" in command:
            from Backend.EmailSender import send_email
            from SpeechToText import get_audio   # Your speech to text function
            from TextToSpeech import speak       # Your text to speech function

            speak("To whom do you want to send the email?")
            recipient = get_audio().lower()

            speak("What is the subject?")
            subject = get_audio()

            speak("What is the message?")
            message = get_audio()

            success = send_email(recipient, subject, message)

            if success:
                speak(f"Email sent to {recipient} successfully.")
            else:
                speak("Sorry, I could not send the email.")

        else:
            print(f"No Function Found for {command}")

    results = await asyncio.gather(*funcs)  # Execute all tasks concurrently.
            
    for result in results:  # Process the results.
        if isinstance(result, str):
             yield result
        else:
             yield result

# Asynchronous function to automate command execution.
async def Automation(commands: list[str]):
    async for result in TranslateAndExecute(commands):  # Translate and execute commands.
        pass
    return True  # Indicate success.

