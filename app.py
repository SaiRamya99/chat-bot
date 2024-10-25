import os
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from PIL import Image
import requests
from io import BytesIO

app = Flask(__name__)

user_sessions = {}

PERSON_IMAGE_PATH = "person_image.jpg"
GARMENT_IMAGE_PATH = "garment_image.jpg"

def combine_images(person_image_path, garment_image_path, output_image_path="output_image.jpg"):
    try:
        # Opening both images to combine
        person_image = Image.open(person_image_path)
        garment_image = Image.open(garment_image_path)
        
        # trying to paste the 2 images together by adjusting the positions
        person_image.paste(garment_image, (0, 0), garment_image)  
        
        # Saving the combined image
        person_image.save(output_image_path)
        return output_image_path
    except Exception as e:
        print(f"Error combining images: {e}")
        return None

@app.route("/whatsapp", methods=['POST'])
def whatsapp():
    incoming_msg = request.values.get('Body', '').lower()
    user_id = request.values.get('From', '')
    media_url = request.values.get('MediaUrl0', None)
    media_type = request.values.get('MediaContentType0', None)

    if user_id not in user_sessions:
        user_sessions[user_id] = {'step': 0, 'person_image': None, 'garment_image': None}

    session = user_sessions[user_id]
    step = session['step']

    # If image is received
    if media_url and media_type.startswith('image'):
        response = requests.get(media_url)
        img = Image.open(BytesIO(response.content))
        
        if step == 0:
            resp = MessagingResponse()
            session['person_image'] = img
            session['step'] = 1  
            resp.message("Specify whether uploaded image is 'Person' or 'Garment'?")
            return str(resp)

        elif step == 1: 
            resp = MessagingResponse()
            session['garment_image'] = img
            session['step'] = 2 
            resp.message("Specify whether uploaded image is 'Person' or 'Garment'?")
            return str(resp)
    
    # Understanding User response for Person and Garment
    if incoming_msg.lower() in ['p', 'person']:
        resp = MessagingResponse()
        session['step'] = 1
        session['person_image'].save(PERSON_IMAGE_PATH)
        resp.message("Image saved. Now share Garment image you wanna virtually try. then type 'Garment'")
        return str(resp)

    if incoming_msg.lower() in ['g', 'garment']:
        resp = MessagingResponse()
        session['garment_image'].save(GARMENT_IMAGE_PATH)
        resp.message("Image saved. Processing image, wait for few seconds")

        # trying to combining the 2 images together
        output_image_path = combine_images(PERSON_IMAGE_PATH, GARMENT_IMAGE_PATH)
        if output_image_path:
            resp.message("Here is your virtual try-on:")
            resp.message(f"Image: {output_image_path}")  
        else:
            resp.message("Error in combining images. Please try again.")
        
        # Resetting the session after the process is completed
        user_sessions[user_id] = {'step': 0, 'person_image': None, 'garment_image': None}
        return str(resp)

    # Default response to User
    resp = MessagingResponse()
    resp.message("Please upload an image to start the virtual try-on process.")
    return str(resp)

# Run the server
if __name__ == "__main__":
    app.run(debug=True)
