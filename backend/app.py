import os
from flask import Flask, render_template, request
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# Load the CSV file into a dataframe
csv_file_path = 'data/semicleanedbg.csv'
data_df = pd.read_csv(csv_file_path)

# Assuming your CSV has columns like 'title', 'description', and 'imdb_rating'
# Adjust the column names as needed to match your CSV structure
def csv_search(query, min_age, max_age):
    matches = data_df[data_df['name'].str.lower().str.contains(query.lower())]
    if min_age is not None:
        matches = matches[matches['minage'] >= min_age]
    if max_age is not None:
        matches = matches[matches['minage'] <= max_age]
    matches_filtered = matches[['name', 'description', 'average']]  # Update column names as necessary
    matches_filtered_json = matches_filtered.to_json(orient='records')
    return matches_filtered_json

@app.route("/")
def home():
    return render_template('base.html', title="sample html")

@app.route("/episodes")
def episodes_search():
    text = request.args.get("title")
    min_age = request.args.get("min_age", type=int)  # Set default as None if not provided
    max_age = request.args.get("max_age", type=int)  # Set default as None if not provided
    return csv_search(text, min_age, max_age)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)