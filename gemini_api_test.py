import os
import google.generativeai as genai
from llama_index.multi_modal_llms.gemini import GeminiMultiModal
from llama_index.core.multi_modal_llms.generic_utils import load_image_urls
from PIL import Image
import requests
from io import BytesIO
import matplotlib.pyplot as plt

# Set up the Google API key
GOOGLE_API_KEY = "AIzaSyCQcuwNvtCg5YIVUcAkp-ZcF8ozw7v71gY"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Image URL to be tested
image_urls = [
    "https://storage.googleapis.com/my-image-upload-bucket123456/Golden%2BRetrievers%2Bdans%2Bpet%2Bcare.jpeg",
]

# Load image URLs into documents
image_documents = load_image_urls(image_urls)

# Initialize the GeminiMultiModal model with the latest model version
gemini_flash = GeminiMultiModal(model_name="models/gemini-1.5-flash")

# Display the image using matplotlib
img_response = requests.get(image_urls[0])
print(f"Image URL: {image_urls[0]}")
img = Image.open(BytesIO(img_response.content))
plt.imshow(img)
plt.axis('off')  # Hide axes
plt.show()

# Generate description using the updated Gemini API
def generate_image_description_gemini(image_url):
    """Generates a description for the image using the updated Gemini API."""
    try:
        response = gemini_flash.complete(
            prompt="Describe the content of the image.",
            image_documents=image_documents,
        )

        description = response.text
        print("Generated Description:", description)
        return description
    except Exception as e:
        print(f"Error generating description: {e}")
        return None

# Generate the image description
description = generate_image_description_gemini(image_urls[0])

# Print the description if it was successfully generated
if description:
    print("Image Description:", description)
else:
    print("No description was generated.")
