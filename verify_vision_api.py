from google.cloud import vision
import os

# Set the environment variable for Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "tholol-368418-62f0ac950520.json"

def test_vision_api():
    try:
        client = vision.ImageAnnotatorClient()
        print("Google Cloud Vision API client created successfully.")
        image = vision.Image()
        image.source.image_uri = 'https://cloud.google.com/vision/docs/images/ferris-wheel.jpg'
        response = client.label_detection(image=image)
        labels = response.label_annotations
        print('Labels:')
        for label in labels:
            print(label.description)
        print("API is enabled and credentials are working correctly.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_vision_api()

