# Import the necessary modules
from flask import Flask, request, send_file, jsonify, url_for
from flask_restful import Resource, Api
from werkzeug.utils import secure_filename
import subprocess
import os
import tempfile
from threading import Timer
from waitress import serve

# Utility function to delete a file after a certain delay (unused in this code)
def delete_file_after_delay(delay, file_path):
    Timer(delay, os.remove, [file_path]).start()

# Initialize Flask app and API
app = Flask(__name__)
api = Api(app)

# Define a route for downloading files
@app.route('/uploads/<path:filename>', methods=['GET'])
def download(filename):
    return send_file(f'/app/uploads/{filename}', as_attachment=True)

# Create a Resource class for file conversion
class Convert(Resource):
    def post(self, format):
        # Check if a file was uploaded
        if 'file' not in request.files:
            return {'error': 'file not provided'}, 400
        file = request.files['file']

        # Check if a file was actually uploaded
        if file.filename == '':
            return {'error': 'file not provided'}, 400

        # Validate the conversion format
        if format not in ['docx', 'pdf', 'txt']:
            return {'error': 'invalid format'}, 400

        try:
            # Create a temporary directory to store files
            with tempfile.TemporaryDirectory() as tmpdirname:
                # Check if temp directory was created
                if not os.path.exists(tmpdirname):
                    return {'error': 'Temp directories were not created!'}, 500

                # Securely strip original file extension
                unique_filename = secure_filename(os.path.splitext(file.filename)[0])

                # Define the input and output file paths
                input_file_path = os.path.join(tmpdirname, f'input-{unique_filename}.odt')
                output_file_path = os.path.join(tmpdirname, f'input-{unique_filename}.{format}')

                # Debug prints (optional)
                print(f"Debug: Input file path is {input_file_path}")
                print(f"Debug: Output file path is {output_file_path}")

                # Save the uploaded file
                file.save(input_file_path)

                # Run the LibreOffice conversion command
                subprocess.run([
                    'libreoffice',
                    '--headless',
                    '--convert-to',
                    format,
                    '--outdir',
                    tmpdirname,
                    input_file_path
                ], check=True)

                # Check if the output file was created
                if not os.path.exists(output_file_path):
                    return {'error': 'output file was not created'}, 500

                # Move the output file to a permanent directory
                new_output_path = os.path.join('/app/uploads', f'output-{unique_filename}.{format}')
                import shutil
                shutil.move(output_file_path, new_output_path)

                # Generate the download URL
                download_url = url_for('download', filename=f'output-{unique_filename}.{format}')

                # Return a success message and download URL
                return {'message': 'Converted successfully', 'download_url': download_url}, 200
        except subprocess.CalledProcessError:
            return {'error': 'conversion failed'}, 500

# Add the Convert resource to the API
api.add_resource(Convert, '/convert/<string:format>')

# Run the Flask app
if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=8080)
