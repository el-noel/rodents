import os
from flask import Flask, render_template, request
from flask_cors import CORS
import pandas as pd
import html

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


import requests
from bs4 import BeautifulSoup
app = Flask(__name__)
CORS(app)


csv_file_path = 'data/semicleanedbg.csv'
data_df = pd.read_csv(csv_file_path)


# for cosine sim
data_df['processed_description'] = data_df['description'].apply(lambda x: x.lower() if isinstance(x, str) else '')
tfidf_vectorizer = TfidfVectorizer()
tfidf_matrix = tfidf_vectorizer.fit_transform(data_df['processed_description'].values.astype('U'))  # 'U' for Unicode


def basic_search(query, min_age, min_players, max_players, category):
    matches = data_df[data_df['name'].str.lower().str.contains(query.lower())]
    if min_age is not None:
        matches = matches[matches['minage'] >= min_age]
    if min_players is not None:
        matches = matches[matches['minplayers'] >= min_players]
    if max_players is not None:
        matches = matches[matches['maxplayers'] <= max_players]
    if category:
        matches = matches[matches['boardgamecategory'].str.contains(category, case=False, na=False)]
        
    matches_filtered = matches[['name', 'description', 'average', 'objectid']] 
    matches_filtered['name'] = matches_filtered['name'].apply(html.unescape)
    matches_filtered['description'] = matches_filtered['description'].apply(html.unescape)
    matches_filtered_json = matches_filtered.to_json(orient='records')
    return matches_filtered_json

@app.route("/")
def home():
    return render_template('base.html', title="sample html")

@app.route("/games")
def search():
    text = request.args.get("title")
    min_age = request.args.get("min_age", type=int)
    min_players = request.args.get("min_players", type=int)
    max_players = request.args.get("max_players", type=int)
    category = request.args.get("category")
    mode = request.args.get("mode")  # Added to capture the search mode

    if mode == 'recommendation':
        matches = recommendation_search(text)
    else:
        matches = matches = data_df[data_df['name'].str.lower().str.contains(text.lower())]
        # basic_search(text, min_age, min_players, max_players, category)

    if min_age is not None:
        matches = matches[matches['minage'] >= min_age]
    if min_players is not None:
        matches = matches[matches['minplayers'] >= min_players]
    if max_players is not None:
        matches = matches[matches['maxplayers'] <= max_players]
    if category:
        matches = matches[matches['boardgamecategory'].str.contains(category, case=False, na=False)]
    matches_filtered = matches[['name', 'description', 'average', 'objectid']] 
    matches_filtered['name'] = matches_filtered['name'].apply(html.unescape)
    matches_filtered['description'] = matches_filtered['description'].apply(html.unescape)
    matches_filtered_json = matches_filtered.to_json(orient='records')

    # Return only the relevant columns
    return matches_filtered_json

def recommendation_search(query):
    if query:
        #some preprocessing: 1- fetch the game 2- get its processed desc
        game_row = data_df[data_df['name'].str.lower() == query.lower()].iloc[0]
        game_description = game_row['processed_description']

        #cos sim
        query_vector = tfidf_vectorizer.transform([game_description])
        cosine_similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()

        #get the top 1000       
        similar_indices = cosine_similarities.argsort()[-(1000+1):][::-1]
    game_index = game_row.index[0]

    # It's possible the game itself is the most similar one, so we exclude it if so.
    similar_indices = similar_indices[1:]
    
    # Fetch the details of the top N similar games then return
    similar_games = data_df.iloc[similar_indices]
    return similar_games
    

@app.route("/about/<game_id>")
def about(game_id):
    game_id = int(game_id)
    game_details_query = data_df[data_df['objectid'] == game_id]
    if not game_details_query.empty:
        game_details = game_details_query.iloc[0].to_dict()
        print("!!!! LOOK HERE !!!!")
        print(game_details)
        # game_img = fetch_game_link(game_details_query["gamelink"])
        print(game_id)
        game_img = fetch_game_link(game_details_query.reset_index(drop=True).at[0, "gamelink"])
        print("!!!! LOOK HERE !!!!")
        print(game_img)
        game_details["img"] = game_img
        return render_template('about.html', game=game_details)
    else:
        return "Game not found", 404
    
def fetch_game_link(game_link):
    # game_link = game_link[game_link.index("/"):]
    print("!!!! LOOK HERE !!!!")
    print(game_link)
    game_url = f"https://boardgamegeek.com{game_link}"
    print("!!!! LOOK HERE !!!!")
    print(game_link)
    response = requests.get(game_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # img_tag = soup.find('meta', attrs={"property": "og:image", })
        link_tag = soup.find_all('link', attrs={"rel": "preload", "as": "image"})
        if link_tag:
            return link_tag[1]['href']
        else:
            return "No <img> tag with the specified class found."
    else:
        return f"Failed to retrieve the webpage. Status code: {response.status_code}"
    
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
