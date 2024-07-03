import streamlit as st
from google.cloud import vision
import io
from PIL import Image
import re

# Initialize the Vision API client
client = vision.ImageAnnotatorClient()

def validate_image(content):
    # Example validation logic
    required_texts = [
        "KINGDOM OF SAUDI ARABIA", 
        "MINISTRY OF INTERIOR", 
        "VEHICLES REGISTRATION",
        "هوية المستخدم",  # User ID
        "رقم الهيكل",  # Chassis number
        "رقم اللوحة",  # Plate number
        "نوع التسجيل",  # Registration type
        "طراز المركبة",  # Vehicle model
        "حمولة المركبة",  # Vehicle load
        "سنة الصنع"  # Year of manufacture
    ]
    
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if response.error.message:
        st.error('Error: {}'.format(response.error.message))
        return False

    detected_text = " ".join([text.description for text in texts])
    
    for required_text in required_texts:
        if required_text not in detected_text:
            return False
    
    return True

st.title('Tikna Project')
st.image('logo.png')

uploaded_file = st.file_uploader("Choose an image...", type=["png", "jpeg", "jpg"])

if uploaded_file is not None:
    content = uploaded_file.read()
    
    if validate_image(content):
        st.success("Image format validated successfully.")
        
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        texts = response.text_annotations

        st.write('Texts:')
        for text in texts:
            st.write('\n"{}"'.format(text.description))

        if response.error.message:
            st.error('Error: {}'.format(response.error.message))
    else:
        st.error("The uploaded image does not match the required format or is missing necessary information.")
