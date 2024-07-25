from flask import Flask, render_template, Response, jsonify, request, session
from flask_wtf import FlaskForm
import secrets
from wtforms import FileField, SubmitField, StringField, DecimalRangeField, IntegerRangeField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired, NumberRange
import os
import cv2
import psycopg2  # Import the PostgreSQL connector
from YOLO_Video import video_detection 
import pdfkit  # Import pdfkit library
from reportlab.pdfgen import canvas
from io import BytesIO
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

import psycopg2
from urllib.parse import urlparse
url = urlparse("postgresql://powerguard_user:qraDCcZYglRcRYEzyOO7iaunanU6KFvh@dpg-cqg9ql2ju9rs73c9vr1g-a.oregon-postgres.render.com/powerguard")

# Extract connection parameters
db_params = {
    'host': "dpg-cqg9ql2ju9rs73c9vr1g-a",
    'port':5432,
    'user': url.username,
    'password': url.password,
    'database': url.path[1:],
}

try:
    db = psycopg2.connect(**db_params)
except psycopg2.Error as e:
    print(f"Unable to connect to the database. Error: {e}")
    exit()
def generate_frames_web(path_x):
    yolo_output = video_detection(path_x)
    for detection_ in yolo_output:
        ref,buffer=cv2.imencode('.jpg',detection_)
   
        frame=buffer.tobytes()
        yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame +b'\r\n')
        

@app.route('/', methods=['GET','POST'])
@app.route('/home', methods=['GET','POST'])
def home():
    session.clear()
    return render_template('indexproject.html')

@app.route('/FrontPage', methods=['GET','POST'])
def frontpage():
    session.clear()
    return render_template('videoprojectnew.html')



@app.route("/webcam", methods=['GET', 'POST'])
def webcam():
    # Fetch the last "crack" detection from the database
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT class_name, timestamp_column FROM detections WHERE class_name='crack' ORDER BY timestamp_column DESC LIMIT 1")
            last_crack_detection = cursor.fetchone()
    except psycopg2.Error as e:
        db.rollback()  # Rollback the transaction in case of an error
        print(f"Error executing SQL query: {e}")
        last_crack_detection = None

    # Check if last_crack_detection is not None before accessing attributes
    if last_crack_detection:
        class_name, timestamp_column = last_crack_detection
        print(f"Last Crack Detection - Class: {class_name}, Timestamp: {timestamp_column}")
    else:
        print("No crack detections found.")

    # Pass the last "crack" detection to the template
    return render_template('ui.html', last_crack_detection=last_crack_detection)
@app.route("/web", methods=['GET','POST'])
def web():
    session.clear()
    return render_template('web.html')



@app.route('/chart', methods=['GET','POST'])
def chart():
    # Dummy data (replace with your actual data)
    chart_data = [
        {'timing': '00:00:00', 'temperature': 920},
        {'timing': '03:00:00', 'temperature': 840},
        {'timing': '06:00:00', 'temperature': 1000},
        {'timing': '10:00:00', 'temperature': 1120},
        {'timing': '13:00:00', 'temperature': 1180},
        {'timing': '17:00:00', 'temperature': 1050},
        {'timing': '21:00:00', 'temperature': 990},
    ]
    chart_data2 = [
        {'timing': '00:00:00', 'temperature': 870},
        {'timing': '03:00:00', 'temperature': 784},
        {'timing': '06:00:00', 'temperature': 1134},
        {'timing': '10:00:00', 'temperature': 1125},
        {'timing': '13:00:00', 'temperature': 1152},
        {'timing': '17:00:00', 'temperature': 987},
        {'timing': '21:00:00', 'temperature': 867},
    ]

    session.clear()
    return render_template('chart.html',chart_data=chart_data,chart_data2=chart_data2)

@app.route('/webapp')
def webapp():
    #return Response(generate_frames(path_x = session.get('video_path', None),conf_=round(float(session.get('conf_', None))/100,2)),mimetype='multipart/x-mixed-replace; boundary=frame')
    return Response(generate_frames_web(path_x=1), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/generate_report', methods=['POST'])
def generate_report():
    try:
        # Retrieve data for the report (modify as needed)
        report_data = {
            'plant_name': 'Mettur Thermal Power Plant',
            'location': 'Salem, Tamilnadu',
            'date': 'Current Date',  # Replace with actual date
            'time': 'Current Time',  # Replace with actual time
            'engineer_name': 'pravinkumar',
            'engineer_id': 'aj012',
            # Add more data as needed
            'unit_data': [
                {
                    'unit_name': 'UNIT I',
                    'temperature': 1329,
                    'working_condition': 'Normal',
                    'damage_detection': 'Nil',
                    'gas_emission': 'Normal'
                    # Add more fields as needed
                },
                # Add data for other units
            ]
        }

        pdf_data = generate_pdf(report_data)

        # Send the PDF as a downloadable file
        response = Response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=periodic_report.pdf'

        return response
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        return jsonify({'error': error_message}), 500
    
def generate_pdf(report_data):
    # Render HTML template
    html_content = render_template('report_template.html', report_data=report_data)

    # Create a BytesIO buffer to store the PDF content
    pdf_buffer = BytesIO()

    # Create a PDF document from the HTML content
    pdf = canvas.Canvas(pdf_buffer)
    pdf.drawString(100, 800, html_content)  # Replace with the correct method to draw HTML content

    # Save the PDF content to the buffer
    pdf.showPage()
    pdf.save()

    # Set the buffer position to the beginning
    pdf_buffer.seek(0)

    return pdf_buffer


if __name__ == "__main__":
    app.run(debug=True,port=8082)
