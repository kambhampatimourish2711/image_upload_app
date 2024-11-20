import os
import base64
import requests
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from google.cloud import storage
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Add a secret key for Flash messages

# Replace with your correct credentials and bucket details
PROJECT_ID = 'cotproject1-436018'
BUCKET_NAME = 'my-image-upload-bucket123456'
GEMINI_API_KEY = 'AIzaSyCQcuwNvtCg5YIVUcAkp-ZcF8ozw7v71gY'
GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-001:generateContent?key={GEMINI_API_KEY}'

# Initialize Google Cloud Storage client and bucket
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

def generate_caption_and_description(image_path):
    """Generate a caption and description for an image using the Gemini API."""
    try:
        with open(image_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": image_data
                            }
                        }
                    ]
                }
            ]
        }

        headers = {'Content-Type': 'application/json'}
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for unsuccessful responses

        api_response = response.json()
        print(f"Gemini API response: {api_response}")

        caption = api_response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No caption available')
        description = "Detailed description not available in response"  # Placeholder if description is not explicit

        return caption, description
    except Exception as e:
        print(f"Error generating caption and description with Gemini API: {e}")
        return None, None

def generate_signed_url(blob):
    """Generates a signed URL for accessing the file privately."""
    try:
        url = blob.generate_signed_url(
            version='v4',
            expiration=3600,  # 1 hour expiration
            method='GET'
        )
        return url
    except Exception as e:
        print(f"Error generating signed URL: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash("No file selected. Please choose an image.")
            return redirect(request.url)

        # Save file locally for processing
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        local_file_path = os.path.join('/tmp', unique_filename)
        file.save(local_file_path)

        try:
            # Upload the file to Google Cloud Storage
            blob = bucket.blob(unique_filename)
            blob.upload_from_filename(local_file_path, content_type=file.content_type)
            print(f"Uploaded image to Cloud Storage: {unique_filename}")

            # Generate caption and description
            caption, description = generate_caption_and_description(local_file_path)
            if caption:
                text_content = f"Caption: {caption}\nDescription: {description}"
                text_blob = bucket.blob(f"{unique_filename}.txt")
                text_blob.upload_from_string(text_content, content_type='text/plain')
                print(f"Text file {unique_filename}.txt saved successfully with content:\n{text_content}")
            else:
                flash("Caption and description could not be generated.")

        except Exception as e:
            print(f"Error during file upload or caption/description generation: {e}")
            flash("An error occurred. Please try again.")
            return redirect(request.url)

        return redirect(url_for('upload_file'))

    # Fetch image and description data to display in the gallery
    blobs = bucket.list_blobs()
    image_data_list = []

    for blob in blobs:
        if not blob.name.endswith('.txt'):
            # Use signed URL for secure access
            image_url = generate_signed_url(blob)
            description_blob = bucket.blob(f"{blob.name}.txt")
            description = description_blob.download_as_text() if description_blob.exists() else "No description available"
            image_data_list.append({'image_url': image_url, 'description': description})

    return render_template('index.html', images=image_data_list, bucket_name=BUCKET_NAME)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
