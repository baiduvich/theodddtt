from flask import Flask, request, send_file, jsonify, url_for
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

@app.route('/uploads/<path:filename>', methods=['GET'])
def download(filename):
    return send_file(f'/app/uploads/{filename}', as_attachment=True)

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

                # Strip original file extension
                unique_filename = secure_filename(os.path.splitext(file.filename)[0])

                # Create input and output file paths
                input_file_path = os.path.join(tmpdirname, f'input-{unique_filename}.odt')
                output_file_path = os.path.join(tmpdirname, f'input-{unique_filename}.{format}')

                print(f"Debug: Input file path is {input_file_path}")
                print(f"Debug: Output file path is {output_file_path}")

                file.save(input_file_path)

                subprocess.run([
                    'libreoffice',
                    '--headless',
                    '--convert-to',
                    format,
                    '--outdir',
                    tmpdirname,
                    input_file_path
                ], check=True)

                if not os.path.exists(output_file_path):
                    return {'error': 'output file was not created'}, 500

                new_output_path = os.path.join('/app/uploads', f'output-{unique_filename}.{format}')
                os.rename(output_file_path, new_output_path)

                download_url = url_for('download', filename=f'output-{unique_filename}.{format}')

                return {'message': 'Converted successfully', 'download_url': download_url}, 200
        except subprocess.CalledProcessError:
            return {'error': 'conversion failed'}, 500

api.add_resource(Convert, '/convert/<string:format>')

if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=8080)
