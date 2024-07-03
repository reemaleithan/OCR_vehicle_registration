# backend.py
from typing import Sequence
from google.cloud import vision
from PIL import Image, ImageEnhance
import io
import re
from google.cloud import translate_v2 as translate
import cv2
import numpy as np

# Helper functions
def check_sn_format(text):
    pattern = r'^[A-Z0-9]{17}$'
    return bool(re.match(pattern, text))

def check_pn_pattern(text):
    pattern = r'^\d{4}[a-zA-Z]{3}$'
    return bool(re.match(pattern, text))

def check_arabic_numeral(text):
    pattern = r'^[\u0660-\u0669\u06F0-\u06F9]+$'
    return bool(re.match(pattern, text))

# Image processing functions
def adjust_brightness(image, brightness):
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(brightness / 50.0)  # Normalize brightness from 0 to 2

def convert_to_grayscale(image):
    return image.convert("L")

def enhance_image_contrast(image):
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(2.0)

def detect_image_edges(image):
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    edges = cv2.Canny(image_cv, 100, 200)
    return Image.fromarray(edges)

def apply_image_processing(image, grayscale, enhance_contrast, detect_edges, brightness):
    # Apply grayscale conversion if needed
    if grayscale:
        image = convert_to_grayscale(image)
    
    # Enhance contrast if needed
    if enhance_contrast:
        image = enhance_image_contrast(image)
    
    # Detect edges if needed
    if detect_edges:
        image = detect_image_edges(image)
    
    # Adjust brightness if needed
    if brightness != 50:  # Assuming 50 is the default/neutral brightness value
        image = adjust_brightness(image, brightness)
    
    return image

def analyze_image_from_bytes(image_bytes, feature_types: Sequence) -> vision.AnnotateImageResponse:
    client = vision.ImageAnnotatorClient()

    # Convert image bytes to OpenCV format
    np_array = np.frombuffer(image_bytes, np.uint8)
    decoded_image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    resized_image = cv2.resize(decoded_image, (958, 602))

    _, preprocessed_content = cv2.imencode('.jpg', resized_image)
    preprocessed_bytes = preprocessed_content.tobytes()
    image = vision.Image(content=preprocessed_bytes)
    features = [vision.Feature(type_=feature_type) for feature_type in feature_types]
    request = vision.AnnotateImageRequest(image=image, features=features)

    response = client.annotate_image(request=request)
    return response

def start(image, grayscale=False, enhance_contrast=False, detect_edges=False, brightness=50):
    features = [vision.Feature.Type.TEXT_DETECTION]
    processed_image = apply_image_processing(image, grayscale, enhance_contrast, detect_edges, brightness)
    
    # Convert PIL image to bytes
    img_byte_arr = io.BytesIO()
    processed_image.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    response = analyze_image_from_bytes(img_byte_arr, features)
    total_words = response.text_annotations[0].description.split('\n')
    translate_client = translate.Client()

    all_text = ""
    for word in total_words:
        result = translate_client.detect_language(word)
        translation = translate_client.translate(word, target_language='en')['translatedText']
        all_text += f"{word} ({translation})\n"
        
    return all_text

