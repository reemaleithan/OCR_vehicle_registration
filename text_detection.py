from typing import Sequence
from google.cloud import vision
from PIL import Image
import io
import re
from google.cloud import translate_v2 as translate
import cv2
import numpy as np
def check_sn_format(text):
    pattern = r'^[A-Z0-9]{17}$'
    if re.match(pattern, text):
        return True
    else:
        return False

def check_pn_pattern(text):
    pattern = r"^\d{4}[a-zA-Z]{3}$"
    if re.match(pattern, text):
        return True
    else:
        return False


# arabic_number = ["٠", "١", "٢", "٣", "٤", "٥", "٦", "٧", "٨", "٩"]
# def check_arabic_numeral(text):
#     flag = 1
#     for letter in text:
#         if letter not in arabic_number:
#             flag = 0
#             break
#     if flag:
#         return True
#     else:
#         return False
    # Pattern to match both Arabic-Indic and Eastern Arabic-Indic numerals

def check_arabic_numeral(text):
    # Pattern to match both Arabic-Indic and Eastern Arabic-Indic numerals
    pattern = r'^[\u0660-\u0669\u06F0-\u06F9]+$'
    if re.match(pattern, text):
        return True
    else:
        return False

def analyze_image_from_uri(image_uri: str, feature_types: Sequence) -> vision.AnnotateImageResponse:
    client = vision.ImageAnnotatorClient()

    # Loads the image into memory
    with io.open(image_uri, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content = content)
    # image.source.image_uri = image_uri
    features = [vision.Feature(type_=feature_type) for feature_type in feature_types]
    request = vision.AnnotateImageRequest(image=image, features=features)

    response = client.annotate_image(request=request)

    return response

def analyze_image_from_uri_prep(image_uri: str, feature_types: Sequence) -> vision.AnnotateImageResponse:
    client = vision.ImageAnnotatorClient()

    # Loads the image into memory
    with io.open(image_uri, 'rb') as image_file:
        content = image_file.read()

    np_array = np.frombuffer(content, np.uint8)

    # Decode the image using OpenCV
    decoded_image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    # Apply preprocessing techniques
    # Example: Convert to grayscale
    gray_image = cv2.cvtColor(decoded_image, cv2.COLOR_BGR2GRAY)

    # Example: Resize the image
    resized_image = cv2.resize(gray_image, (958, 602))

    # Example: Normalize the pixel values
    # normalized_image = cv2.normalize(resized_image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)

    # Convert the preprocessed image back to bytes
    _, preprocessed_content = cv2.imencode('.jpg', resized_image)
    preprocessed_bytes = preprocessed_content.tobytes()
    image = vision.Image(content=preprocessed_bytes)
    # image = vision.Image(content = content)
    # image.source.image_uri = image_uri
    features = [vision.Feature(type_=feature_type) for feature_type in feature_types]
    request = vision.AnnotateImageRequest(image=image, features=features)

    response = client.annotate_image(request=request)

    return response


# def print_text(response: vision.AnnotateImageResponse):
#     print("=" * 80)
        
#     for annotation in response.text_annotations:
#         vertices = [f"({v.x},{v.y})" for v in annotation.bounding_poly.vertices]
#         print(
#             f"{repr(annotation.description):42}",
#             ",".join(vertices),
#             sep=" | ",
#         )


image_uri = "1.jpeg"
# img = Image.open(image_uri)
# img.show()
features = [vision.Feature.Type.TEXT_DETECTION]

response = analyze_image_from_uri_prep(image_uri, features)

# print(response.text_annotations[0].description)
total_words = response.text_annotations[0].description.split('\n')
translate_client = translate.Client()
flag_ui = 0
flag_sn = 0
flag_pn = 0
flag_rt = 0
total_rt = ""
total_ui = ""
total_sn = ""
total_pn = ""
# print(total_words)
for i in range(len(total_words)):
    print(total_words[i])
    result = translate_client.detect_language(total_words[i])
    language = result["language"]
    # print("Detected language:", language)
    translation = translate_client.translate(total_words[i], target_language='en')
    translated_text = translation['translatedText']
    print("Translated text:", translated_text)
    if translated_text == "User ID":
        for j in range(len(total_words)):
            if check_arabic_numeral(total_words[j]):
                flag_ui = 1
                total_ui = total_words[j] + " " + total_words[i]
                break

    len_ui_num = 0
    words_ui = "هوية المستخدم"
    if not flag_ui:
        if "User ID" in translated_text:
            re_words = total_words[i].split(' ')
            words_ar = ''
            words_nm = ''
            for word in re_words:
                if check_arabic_numeral(word):
                    len_ui_num = len(word)
                    words_nm = word
                    break

            for j in range(len(total_words)):
                if check_arabic_numeral(total_words[j]):
                    if len_ui_num < len(total_words[j]):
                        words_nm = total_words[j]
                    break

            flag_ui = 1
            total_ui = words_nm + " " + words_ui

    words_sn = "رقم الهيكل"
    if translated_text == "Structure No" or translated_text == "Chassis number":
        for j in range(len(total_words)):
            if check_sn_format(total_words[j]):
                flag_sn = 1
                total_sn = total_words[j] + " " + total_words[i]
                break

    if not flag_sn:
        if "Chassis number" in translated_text or "Structure No" in translated_text:
            re_words = translated_text.replace("Chassis number", "")
            re_words = re_words.replace("Structure No", "")
            re_words = re_words.replace(" ", "")
            if check_sn_format(re_words):
                flag_sn = 1
                total_sn = total_words[i]

    if not flag_sn:
        if check_sn_format(total_words[i]):
            flag_sn = 1
            total_sn = total_words[i] + " " + words_sn

    if translated_text == "Plate Number":
        for j in range(len(total_words)):
            re_words = total_words[j].replace(" ", "")
            if check_pn_pattern(re_words):
                digital_part = re_words[:-3]
                string_part = re_words[-3:]
                flag_pn = 1
                total_pn = digital_part + " " + string_part + " " + total_words[i]
                break


    if "Registration" in translated_text or "registration" in translated_text:
        flag_rt = 1
        if flag_pn:
            total_rt = total_words[i]
        else:
            total_rt = total_words[i]

words_pn = "رقم اللوحة"
if not flag_pn:
    for j in range(len(total_words)):
        re_words = total_words[j].replace(" ", "")
        if check_pn_pattern(re_words):
            digital_part = re_words[:-3]
            string_part = re_words[-3:]
            flag_pn = 1
            total_pn = digital_part + " " + string_part + " " + words_pn
            break

if not flag_pn:
    cnt = 0
    while not flag_pn:
        if cnt > 4:
            break
        cnt = cnt + 1
        response = analyze_image_from_uri(image_uri, features)
        total_words = response.text_annotations[0].description.split('\n')
        for j in range(len(total_words)):
            re_words = total_words[j].replace(" ", "")
            if check_pn_pattern(re_words):
                digital_part = re_words[:-3]
                string_part = re_words[-3:]
                flag_pn = 1
                total_pn = digital_part + " " + string_part + " " + words_pn
                break

if flag_ui:
    print(total_ui)

if flag_sn:
    print(total_sn)

if flag_pn:
    print(total_pn)

if flag_rt:
    print(total_rt)
