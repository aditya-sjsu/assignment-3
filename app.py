from flask import Flask, request, jsonify, send_from_directory
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from dotenv import load_dotenv
import os
import time
from flask_cors import CORS
import tempfile

load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

# Azure Computer Vision credentials
SUBSCRIPTION_KEY = os.getenv('AZURE_VISION_KEY')
ENDPOINT = os.getenv('AZURE_VISION_ENDPOINT')

# Initialize the Computer Vision client
computervision_client = ComputerVisionClient(
    ENDPOINT, CognitiveServicesCredentials(SUBSCRIPTION_KEY)
) if SUBSCRIPTION_KEY and ENDPOINT else None

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    if not computervision_client:
        return jsonify({'error': 'Azure credentials not configured'}), 500

    try:
        image_file = request.files['image']
        
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_image:
            image_file.save(temp_image.name)
            
            # Read the image file
            with open(temp_image.name, 'rb') as image:
                # Submit the image to Azure's OCR
                read_response = computervision_client.read_in_stream(image, raw=True)
                read_operation_location = read_response.headers["Operation-Location"]
                operation_id = read_operation_location.split("/")[-1]

                # Wait for the operation to complete
                while True:
                    read_result = computervision_client.get_read_result(operation_id)
                    if read_result.status not in ['notStarted', 'running']:
                        break
                    time.sleep(1)

                # Extract and return the text
                if read_result.status == OperationStatusCodes.succeeded:
                    text_results = []
                    for text_result in read_result.analyze_result.read_results:
                        for line in text_result.lines:
                            text_results.append({
                                'text': line.text,
                                'confidence': 1.0  # Azure's Read API v3.2 doesn't provide confidence scores per line
                            })
                    return jsonify({
                        'success': True,
                        'results': text_results
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to process image'
                    }), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 