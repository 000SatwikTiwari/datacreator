import streamlit as st
from pymongo import MongoClient
import pandas as pd
from flask import Flask, request, render_template_string, redirect
from threading import Thread
import time
from bson.objectid import ObjectId
import socket

# Set up MongoDB client
client = MongoClient("mongodb://satwiksudhanshtiwari:Satwik2021@ac-0afcv37-shard-00-00.8hns6ba.mongodb.net:27017,ac-0afcv37-shard-00-01.8hns6ba.mongodb.net:27017,ac-0afcv37-shard-00-02.8hns6ba.mongodb.net:27017/?ssl=true&replicaSet=atlas-3m9dyh-shard-0&authSource=admin&retryWrites=true&w=majority&appName=Cluster0")
db = client['survey_database']

# HTML template for the form
FORM_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Custom Form</title>
</head>
<body>
    <h2>Custom Form</h2>
    <form method="post">
        {% for field in fields %}
        <label for="{{ field.name }}">{{ field.name }}</label><br>
        {% if field.type == "String" %}
        <input type="text" id="{{ field.name }}" name="{{ field.name }}"><br>
        {% elif field.type == "Integer" %}
        <input type="number" id="{{ field.name }}" name="{{ field.name }}" step="1"><br>
        {% elif field.type == "Float" %}
        <input type="number" id="{{ field.name }}" name="{{ field.name }}" step="0.01"><br>
        {% elif field.type == "Boolean" %}
        <input type="checkbox" id="{{ field.name }}" name="{{ field.name }}"><br>
        {% endif %}
        <br>
        {% endfor %}
        <input type="submit" value="Submit">
    </form>
</body>
</html>
'''

# Define Flask app
flask_app = Flask(__name__)

@flask_app.route('/form/<form_id>', methods=['GET', 'POST'])
def form(form_id):
    form_data = db.forms.find_one({"_id": form_id})
    if not form_data:
        return "Form not found", 404

    if request.method == 'POST':
        submission = {field['name']: request.form.get(field['name']) for field in form_data['fields']}
        db.responses.insert_one({"form_id": form_id, **submission})
        return redirect('/thanks')

    return render_template_string(FORM_TEMPLATE, fields=form_data['fields'])

@flask_app.route('/thanks')
def thanks():
    return "Thank you for your submission!"

# Function to run Flask app
def run_flask():
    flask_app.run(host='0.0.0.0', port=5000)

# Streamlit app
def main():
    st.title("Custom Dataset Creator")

    # Step 1: Get dataset details from the user
    st.header("Step 1: Define Your Dataset")
    num_columns = st.number_input("Number of Columns", min_value=1, max_value=20, step=1)
    columns = []

    for i in range(num_columns):
        col_name = st.text_input(f"Column {i+1} Name", key=f'col_name_{i}')
        col_type = st.selectbox(f"Column {i+1} Data Type", options=["String", "Integer", "Float", "Boolean"], key=f'col_type_{i}')
        columns.append({"name": col_name, "type": col_type})

    if st.button("Generate Form Link"):
        # Save form structure to MongoDB
        form_id = str(ObjectId())
        db.forms.insert_one({"_id": form_id, "fields": columns})
        
        # Get the local IP address of the machine
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        form_link = f"http://{local_ip}:5000/form/{form_id}"
        st.write("Form created! Share this link to collect data:")
        st.write(form_link)

    st.header("Step 3: Download Your Data")
    if st.button("Download CSV"):
        # Fetch data from MongoDB and provide download link
        data = fetch_data_from_mongodb()
        csv = convert_to_csv(data)
        st.download_button("Download CSV", data=csv, file_name="dataset.csv", mime="text/csv")

# Function to fetch data from MongoDB
def fetch_data_from_mongodb():
    data = list(db.responses.find({}, {"_id": 0, "form_id": 0}))
    return data

# Function to convert data to CSV
def convert_to_csv(data):
    df = pd.DataFrame(data)
    return df.to_csv(index=False)

if __name__ == "__main__":
    # Start Flask app in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Give Flask some time to start
    time.sleep(1)

    # Run Streamlit app
    main()
