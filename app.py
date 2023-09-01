from flask import Flask, request, send_file, jsonify
from flask_restful import Resource, Api
from werkzeug.utils import secure_filename
import subprocess
import os
import tempfile
from threading import Timer
from waitress import serve

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

        try:
            with tempfile.TemporaryDirectory() as tmpdirname:
                if not os.path.exists(tmpdirname):
                    return {'error': 'Temp directories were not created!'}, 500

                unique_filename = secure_filename(file.filename)
                input_file_path = os.path.join(tmpdirname, f'input-{unique_filename}.odt')
                output_file_path = os.path.join(tmpdirname, f'output-{unique_filename}.{format}')
                
                # Log to debug input_file_path and output_file_path
                print(f"Debug: Input file path is {input_file_path}")
                print(f"Debug: Output file path is {output_file_path}")
                
                file.save(input_file_path)
                
                libreoffice_command = [
                    'libreoffice',
                    '--headless',
                    '--convert-to',
                    format,
                    '--outdir',
                    tmpdirname,
                    input_file_path
                ]

                print(f"Running command: {' '.join(libreoffice_command)}")

                try:
                    subprocess.run(libreoffice_command, check=True)
                except subprocess.CalledProcessError:
                    return {'error': 'conversion failed'}, 500

                if not os.path.exists(output_file_path):
                    return {'error': 'output file was not created'}, 500

                return send_file(
                    output_file_path,
                    as_attachment=True,
                    download_name=f'converted-{unique_filename}.{format}'
                )
        except Exception as e:
            print(f"An exception occurred: {e}")
            return {'error': str(e)}, 500

api.add_resource(Convert, '/convert/<string:format>')

if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=8080)
