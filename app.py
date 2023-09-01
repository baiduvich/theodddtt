from flask import Flask, request, send_file, jsonify, url_for
from flask_restful import Resource, Api
from werkzeug.utils import secure_filename
import subprocess
import os
import tempfile
import uuid  # Import the UUID library
from threading import Timer
from waitress import serve

# Function to delete files after a delay (unused in this example)
def delete_file_after_delay(delay, file_path):
    Timer(delay, os.remove, [file_path]).start()

# Initialize Flask and Flask-RESTful
app = Flask(__name__)
api = Api(app)

# Route for downloading files
@app.route('/uploads/<path:filename>', methods=['GET'])
def download(filename):
    return send_file(f'/app/uploads/{filename}', as_attachment=True)

# RESTful Resource for conversion
class Convert(Resource):
    def post(self, format):
        # List of supported formats
        supported_formats = ['docx', 'pdf', 'txt', 'jpg', 'mhtml', 'rtf', 'png', 'webp', 'xml', 'xps']
        
        # Check if file is present in the request
        if 'file' not in request.files:
            return {'error': 'file not provided'}, 400

        file = request.files['file']

        # Check if filename is empty
        if file.filename == '':
            return {'error': 'file not provided'}, 400

        # Check for valid conversion format
        if format not in supported_formats:
            return {'error': 'invalid format'}, 400

        try:
            # Create a temporary directory
            with tempfile.TemporaryDirectory() as tmpdirname:
                if not os.path.exists(tmpdirname):
                    return {'error': 'Temp directories were not created!'}, 500
                
                # Generate a UUID for unique identification
                unique_id = str(uuid.uuid4())

                # Create a unique filename using the UUID
                unique_filename = secure_filename(f"{unique_id}-{os.path.splitext(file.filename)[0]}")

                # Paths for the input and output files
                input_file_path = os.path.join(tmpdirname, f'input-{unique_filename}.odt')
                output_file_path = os.path.join(tmpdirname, f'input-{unique_filename}.{format}')

                # Save the uploaded file
                file.save(input_file_path)

                # Run LibreOffice for conversion
                subprocess.run([
                    'libreoffice',
                    '--headless',
                    '--convert-to',
                    format,
                    '--outdir',
                    tmpdirname,
                    input_file_path
                ], check=True)

                # Check if output file was created
                if not os.path.exists(output_file_path):
                    return {'error': 'output file was not created'}, 500

                # Move the output file to the uploads directory
                new_output_path = os.path.join('/app/uploads', f'output-{unique_filename}.{format}')
                import shutil
                shutil.move(output_file_path, new_output_path)

                # Generate a download URL
                download_url = url_for('download', filename=f'output-{unique_filename}.{format}')

                return {'message': 'Converted successfully', 'download_url': download_url}, 200
                
        except subprocess.CalledProcessError:
            return {'error': 'conversion failed'}, 500

# Add the Convert resource to the API
api.add_resource(Convert, '/convert/<string:format>')

# Main entry point
if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=8080)
