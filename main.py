from flask import Flask, render_template, request, redirect, url_for, flash, session
from google.cloud import storage
import os
import requests
from io import BytesIO
from PIL import Image
from datetime import timedelta
from llama_index.multi_modal_llms.gemini import GeminiMultiModal
from llama_index.core.multi_modal_llms.generic_utils import load_image_urls

app = Flask(__name__)
app.secret_key = 'supersecretkey'

bucket_name = 'my-image-upload-bucket123456'
API_KEY = 'AIzaSyCQcuwNvtCg5YIVUcAkp-ZcF8ozw7v71gY'
os.environ["GOOGLE_API_KEY"] = API_KEY

storage_client = storage.Client()
bucket = storage_client.bucket(bucket_name)

gemini_pro = GeminiMultiModal(model_name="models/gemini-1.5-flash")

def generate_image_description(image_url):
    """Generates a description for the image using the Gemini API."""
    try:
        image_documents = load_image_urls([image_url])
        response = gemini_pro.complete(
            prompt="Describe the content of the image.",
            image_documents=image_documents,
        )
        description = response.text
        return description
    except Exception as e:
        print(f"Error generating description: {e}")
        return None

def save_description_to_bucket(file_name, description):
    """Saves the description to a text file in the same bucket as the image."""
    try:
        text_blob = bucket.blob(file_name + '.txt')
        text_blob.upload_from_string(description)
        print(f"Description saved for {file_name}.txt")
    except Exception as e:
        print(f"Error saving description to bucket: {e}")

@app.route("/", methods=["GET", "POST"])
def index():
    image_url = None
    description = None
    uploaded_files = []

    # Retrieve the list of previously uploaded files
    blobs = bucket.list_blobs()
    for blob in blobs:
        uploaded_files.append({
            "name": blob.name,
            "url": blob.public_url
        })

    if request.method == "POST":
        # Handle file upload
        if 'file' not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash("No selected file")
            return redirect(request.url)
        if file:
            # Upload file to Google Cloud Storage
            blob = bucket.blob(file.filename)
            blob.upload_from_file(file)
            blob.make_public()  # Make the file public (optional)
            image_url = blob.public_url

            # Generate image description using Gemini API
            description = generate_image_description(image_url)
            if description:
                save_description_to_bucket(file.filename, description)
                flash(f"File {file.filename} uploaded successfully with description.")
            else:
                flash("Error generating description.")

    return render_template("index.html", image_url=image_url, description=description, uploaded_files=uploaded_files)

@app.route("/clear", methods=["POST"])
def clear_bucket():
    blobs = bucket.list_blobs()
    for blob in blobs:
        blob.delete()
    flash("Bucket cleared successfully.")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
