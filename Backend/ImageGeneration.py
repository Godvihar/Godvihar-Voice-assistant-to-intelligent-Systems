import asyncio
import os
import sys
import logging
from random import randint
from PIL import Image, ImageFile
from time import sleep
import requests
from dotenv import load_dotenv, get_key
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Enable PIL to load truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Get the base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Folder paths
folder_path = os.path.join(BASE_DIR, "Data")
status_file = os.path.join(BASE_DIR, "Frontend", "Files", "ImageGeneration.data")

# Create Data directory if it doesn't exist
os.makedirs(folder_path, exist_ok=True)
os.makedirs(os.path.dirname(status_file), exist_ok=True)

# Load environment variables
load_dotenv(os.path.join(BASE_DIR, '.env'))

# API details for the Hugging Face model
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
API_KEY = os.getenv("HuggingFaceAPIKey")

if not API_KEY:
    logger.error("HuggingFaceAPIKey not found in environment variables")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "image/png",
    "Content-Type": "application/json"
}

# Function to open and display images based on a given prompt
def open_images(prompt):
    """Open generated images for the given prompt."""
    prompt = prompt.replace(" ", "_")
    files = []
    
    # Try multiple extensions
    for ext in ['.jpg', '.png', '.jpeg']:
        for i in range(1, 5):
            files.append(f"{prompt}{i}{ext}")
    
    opened = 0
    for img_file in files:
        if opened >= 4:  # Only open up to 4 images
            break
            
        image_path = os.path.join(folder_path, img_file)
        if not os.path.exists(image_path):
            logger.debug(f"Image not found: {image_path}")
            continue
            
        try:
            img = Image.open(image_path)
            logger.info(f"Opening image: {image_path}")
            img.show()
            opened += 1
            sleep(1)  # Small delay between opening images
        except Exception as e:
            logger.warning(f"Unable to open {image_path}: {str(e)}")
    
    if opened == 0:
        logger.error(f"No images found for prompt: {prompt}")
        return False
    return True

# Async function to send a query to the API
async def query(payload, retry_count=3, timeout=30):
    """Send a query to the Hugging Face API with retry logic."""
    for attempt in range(retry_count):
        try:
            logger.debug(f"Sending request to {API_URL} (attempt {attempt + 1}/{retry_count})")
            logger.debug(f"Payload: {payload}")
            
            # Use aiohttp for better async performance
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    API_URL,
                    headers=headers,
                    json=payload,
                    timeout=timeout
                ) as response:
                    logger.debug(f"Response status: {response.status}")
                    
                    if response.status == 200:
                        content = await response.read()
                        logger.info(f"Image generated successfully. Size: {len(content)} bytes")
                        return content
                    elif response.status == 503:
                        wait_time = 10 * (attempt + 1)  # Exponential backoff
                        logger.info(f"Model is loading... waiting {wait_time} seconds.")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        error_text = await response.text()
                        logger.error(f"API Error {response.status}: {error_text}")
                        if attempt == retry_count - 1:  # Last attempt
                            return None
                        
        except asyncio.TimeoutError:
            logger.warning(f"Request timed out (attempt {attempt + 1}/{retry_count})")
            if attempt == retry_count - 1:
                return None
                
        except Exception as e:
            logger.error(f"Request failed: {str(e)}", exc_info=True)
            if attempt == retry_count - 1:  # Last attempt
                return None
                
        # Exponential backoff
        await asyncio.sleep(2 ** attempt)
    
    return None

# Async function to generate 4 images from prompt
def clean_prompt(prompt: str) -> str:
    """Clean and format the prompt for better results."""
    # Remove common command phrases
    phrases_to_remove = [
        "generate image of",
        "create image of",
        "generate an image of",
        "create an image of",
        "generate a picture of",
        "create a picture of"
    ]
    
    prompt = prompt.lower().strip()
    for phrase in phrases_to_remove:
        if phrase in prompt:
            prompt = prompt.replace(phrase, "").strip()
    
    # Remove extra whitespace
    prompt = ' '.join(prompt.split())
    
    # Add quality prompts if not present
    quality_terms = [
        "high quality", "detailed", "sharp focus", "high resolution",
        "4k", "8k", "professional photography"
    ]
    
    if not any(term in prompt for term in quality_terms):
        prompt = f"{prompt}, high quality, detailed, 4k, professional photography"
    
    return prompt

async def generate_images(prompt: str) -> bool:
    """Generate images based on the given prompt."""
    try:
        # Clean and prepare the prompt
        clean_prompt_text = clean_prompt(prompt)
        logger.info(f"Generating images for prompt: '{clean_prompt_text}'")
        
        # Create tasks for multiple images
        tasks = []
        for i in range(4):  # Generate 4 variations
            payload = {
                "inputs": (
                    f"{clean_prompt_text}, "
                    f"highly detailed, professional photography, "
                    f"sharp focus, studio lighting, "
                    f"seed {randint(0, 1000000)}"
                ),
                "options": {
                    "wait_for_model": True,
                    "use_cache": False
                }
            }
            tasks.append(query(payload))
        
        # Run all tasks concurrently
        image_bytes_list = await asyncio.gather(*tasks)
        
        # Save the images
        success_count = 0
        for i, image_bytes in enumerate(image_bytes_list):
            if not image_bytes:
                logger.warning(f"Failed to generate image {i+1}")
                continue
                
            try:
                # Create a safe filename
                safe_prompt = "".join(
                    c if c.isalnum() or c in (' ', '-', '_') else '_' 
                    for c in clean_prompt_text[:50]
                ).strip('_').replace(' ', '_')
                
                # Try multiple extensions
                for ext in ['.jpg', '.png']:
                    filename = os.path.join(folder_path, f"{safe_prompt}_{i+1}{ext}")
                    try:
                        with open(filename, "wb") as f:
                            f.write(image_bytes)
                        logger.info(f"Saved image: {filename}")
                        success_count += 1
                        break
                    except Exception as e:
                        logger.warning(f"Failed to save {filename}: {str(e)}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error processing image {i+1}: {str(e)}", exc_info=True)
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error in generate_images: {str(e)}", exc_info=True)
        return False

def GenerateImages(prompt: str) -> bool:
    """Generate and open images for the given prompt."""
    logger.info(f"Starting image generation for prompt: {prompt}")
    
    # Clean the prompt
    clean_prompt_text = clean_prompt(prompt)
    logger.info(f"Cleaned prompt: {clean_prompt_text}")
    
    # Run the async function
    try:
        success = asyncio.run(generate_images(clean_prompt_text))
        if success:
            logger.info("Image generation completed successfully")
            open_images(clean_prompt_text)
            return True
        else:
            logger.error("Image generation failed")
            return False
            
    except Exception as e:
        logger.error(f"Error in GenerateImages: {str(e)}", exc_info=True)
        return False

def read_status_file():
    """Read and parse the status file."""
    try:
        with open(status_file, 'r', encoding='utf-8') as f:
            data = f.read().strip()
            logger.debug(f"Read status file: {data}")
            
            # Handle different formats
            data = data.strip('[]\'\"')
            parts = [p.strip() for p in data.split(',', 1)]
            
            if len(parts) >= 2:
                return parts[0], parts[1].lower() == 'true'
            return None, False
            
    except FileNotFoundError:
        logger.warning(f"Status file not found: {status_file}")
        return None, False
    except Exception as e:
        logger.error(f"Error reading status file: {str(e)}")
        return None, False

def write_status_file(prompt: str, status: bool):
    """Write to the status file."""
    try:
        with open(status_file, 'w', encoding='utf-8') as f:
            f.write(f"{prompt}, {status}")
        logger.debug(f"Updated status file: {prompt}, {status}")
        return True
    except Exception as e:
        logger.error(f"Error writing to status file: {str(e)}")
        return False

async def ImageGenerationLoop():
    """Main loop for the image generation service."""
    logger.info("Starting Image Generation Service")
    
    while True:
        try:
            # Read the status file
            prompt, should_generate = read_status_file()
            
            if should_generate and prompt:
                logger.info(f"Processing image generation request: {prompt}")
                
                # Reset the status file first to prevent duplicate processing
                write_status_file("", False)
                
                # Generate images
                success = GenerateImages(prompt)
                
                if not success:
                    logger.error("Image generation failed")
                    # Reset status on failure
                    write_status_file("", False)
                
                # Small delay before next check
                await asyncio.sleep(1)
                
            else:
                # Sleep for a bit before checking again
                await asyncio.sleep(0.5)
                
        except KeyboardInterrupt:
            logger.info("Image Generation Service stopped by user")
            break
            
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {str(e)}", exc_info=True)
            await asyncio.sleep(5)  # Prevent tight loop on error

if __name__ == "__main__":
    try:
        # Ensure the event loop is properly configured
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # Create and run the event loop
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(ImageGenerationLoop())
        finally:
            loop.close()
        
    except KeyboardInterrupt:
        logger.info("Image Generation Service stopped")
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
