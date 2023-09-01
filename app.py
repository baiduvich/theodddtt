from flask import Flask, request, send_file, jsonify
from flask_restful import Resource, Api
from werkzeug.utils import secure_filename
import subprocess
import os
import tempfile
from threading import Timer
from waitress import serve

def delete_file_after_delay(delay, file_path):
    Timer(delay, os.remove, [file_path]).start()

app = Flask(__name__)
api = Api(app)

class Convert(Resource):
    def post(self, format):
        if 'file' not in request.files:
            return {'error': 'file not provided'}, 400

        file = request.files['file']
        if file.filename == '':
            return {'error': 'file not provided'}, 400

        if format not in ['docx', 'pdf', 'txt']:
            return {'error': 'invalid format'}, 400

        # Create a temporary directory using tempfile
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Check if temporary directories are created
            if not os.path.exists(tmpdirname):
                return {'error': 'Temp directories were not created!'}, 500

            unique_filename = secure_filename(file.filename)
            input_file_path = os.path.join(tmpdirname, f'input-{unique_filename}.odt')
            output_file_path = os.path.join(tmpdirname, f'output-{unique_filename}.{format}')

            file.save(input_file_path)

            try:
                subprocess.run([
                    'libreoffice',
                    '--headless',
                    '--convert-to',
                    format,
                    '--outdir',
                    tmpdirname,
                    input_file_path
                ], check=True)
            except subprocess.CalledProcessError:
                return {'error': 'conversion failed'}, 500

            return send_file(
                output_file_path,
                as_attachment=True,
                download_name=f'converted-{unique_filename}.{format}'
            )

api.add_resource(Convert, '/convert/<string:format>')

if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=8080)
