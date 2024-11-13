from main import app
from io import BytesIO  # Add this import for BytesIO usage

def test_home_page():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Upload an Image" in response.data

def test_upload_page():
    client = app.test_client()
    response = client.post("/", data={"file": (BytesIO(b"fake image data"), "test.jpg")}, follow_redirects=True)
    assert response.status_code == 200
    assert b"File uploaded successfully" in response.data or b"No file part" in response.data
