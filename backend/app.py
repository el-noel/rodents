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
def csv_search(query, min_age, min_players, max_players, category):
    matches = data_df[data_df['name'].str.lower().str.contains(query.lower())]
    if min_age is not None:
        matches = matches[matches['minage'] >= min_age]
    if min_players is not None:
        matches = matches[matches['minplayers'] >= min_players]
    if max_players is not None:
        matches = matches[matches['maxplayers'] <= max_players]
    if category:  # If a category is provided, filter by itm
        matches = matches[matches['boardgamecategory'].str.contains(category, case=False, na=False)]
        
    matches_filtered = matches[['name', 'description', 'average', 'objectid']]  # Update column names as necessary
    matches_filtered_json = matches_filtered.to_json(orient='records')
    return matches_filtered_json

@app.route("/")
def home():
    return render_template('base.html', title="sample html")

@app.route("/episodes")
def episodes_search():
    text = request.args.get("title")
    min_age = request.args.get("min_age", type=int)
    min_players = request.args.get("min_players", type=int)
    max_players = request.args.get("max_players", type=int)
    category = request.args.get("category")  # No type, because it's a string
    return csv_search(text, min_age, min_players, max_players, category)

@app.route("/about/<game_id>")
def about(game_id):
    game_id = int(game_id)
    game_details_query = data_df[data_df['objectid'] == game_id]
    # Check if the query returned any rows
    if not game_details_query.empty:
        game_details = game_details_query.iloc[0].to_dict()
        return render_template('about.html', game=game_details)
    else:
        # If no rows are returned, handle the case (e.g., show a not found page or message)
        return "Game not found", 404

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
