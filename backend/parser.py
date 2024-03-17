import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler
import pandas as pd
import csv

# Open the CSV file for reading


# ROOT_PATH for linking with all your files. 
# Feel free to use a config.py or settings.py with a global export variable
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..",os.curdir))

# Get the directory of the current script
# ROOT_PATH for linking with all your files. 
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..", os.curdir))

# Get the directory of the current script
current_directory = os.path.dirname(os.path.abspath(__file__))

# CSV to JSON Conversion
with open(os.path.join(current_directory, "data", "semicleanedbg.csv"), 'r', encoding='utf-8') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    data = list(csv_reader)

with open(os.path.join(current_directory, "bg.json"), 'w') as json_file:
    json.dump(data, json_file, indent=4)

# Reading and Parsing JSON
json_file_path = os.path.join(current_directory, 'bg.json')

# Assuming your JSON data is stored in a file named 'init.json'
with open(json_file_path, 'r') as file:
    data = json.load(file)
    bg_df = pd.DataFrame(data)

app = Flask(__name__)
CORS(app)

# Sample search using json with pandas
def json_search(query):
    matches = []
    matches = bg_df[bg_df['name'].str.lower().str.contains(query.lower())]

    matches_filtered = matches[['name', 'description', 'baverage']]
    matches_filtered_json = matches_filtered.to_json(orient='records')
    return matches_filtered_json

@app.route("/")
def home():
    return render_template('base.html',title="sample html")

@app.route("/episodes")
def episodes_search():
    text = request.args.get("title")
    return json_search(text)

if 'DB_NAME' not in os.environ:
    app.run(debug=True,host="0.0.0.0",port=5000)