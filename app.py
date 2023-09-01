from flask import Flask, request, send_file, jsonify
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import subprocess
import os
import tempfile
from threading import Timer
from waitress import serve

# Initialize Flask and SQLAlchemy
app = Flask(__name__)
# Configure database URI (Replace these with your PostgreSQL credentials)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://odtdatabase_user:PAELaEqjZAdPgGJoaMsB2IjiNRW9qQGq@dpg-cjoqppr6fquc73fgtlo0-a/odtdatabase'
db = SQLAlchemy(app)
api = Api(app)

# Define SQLAlchemy model for files
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.LargeBinary)

# Function to delete file blob from database after delay
def delete_blob_after_delay(delay, blob_id):
    Timer(delay, lambda: db.session.query(File).filter(File.id == blob_id).delete()).start()

# Convert class (Resource)
class Convert(Resource):
    def post(self, format):
        if 'file' not in request.files:
            return {'error': 'file not provided'}, 400

        file = request.files['file']
        if file.filename == '':
            return {'error': 'file not provided'}, 400

        if format not in ['docx', 'pdf', 'txt']:
            return {'error': 'invalid format'}, 400

        # Step 1: Save the file blob to the database
        file_data = File(data=file.read())
        db.session.add(file_data)
        db.session.commit()

        # Step 2 and 3: Save the blob to a temp file and convert it
        with tempfile.TemporaryDirectory() as tmpdirname:
            unique_filename = secure_filename(file.filename)

            input_file_path = os.path.join(tmpdirname, f'input-{unique_filename}.odt')
            output_file_path = os.path.join(tmpdirname, f'output-{unique_filename}.{format}')

            with open(input_file_path, 'wb') as f:
                f.write(file_data.data)

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

            # Step 4: Read the converted file and save back to the database
            with open(output_file_path, 'rb') as f:
                converted_data = File(data=f.read())
                db.session.add(converted_data)
                db.session.commit()

            # Delete blobs from database after 30 seconds
            delete_blob_after_delay(30, file_data.id)
            delete_blob_after_delay(30, converted_data.id)

        return jsonify({"message": "File conversion successful!", "converted_file_id": converted_data.id})

# Add the Convert resource to the API
api.add_resource(Convert, '/convert/<string:format>')

# Initialize the database
if __name__ == '__main__':
    db.create_all()
    serve(app, host="0.0.0.0", port=8080)
