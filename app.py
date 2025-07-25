import streamlit as st
import pickle
import numpy as np
import pandas as pd
import requests
import json
import os

# ----------------- TMDb API Key -----------------
TMDB_API_KEY = "804978dfcea1ef19ea286f0fb628475d"

# ----------------- Load Data -----------------
movies = pickle.load(open('movies_list.pkl', 'rb'))
similarity = pickle.load(open('similarity2.pkl', 'rb'))
movies_list = movies['title'].values

# ----------------- Playlist Functions -----------------
def load_playlist():
    if os.path.exists("playlist.json"):
        with open("playlist.json", "r") as file:
            return json.load(file)
    return []

def save_playlist(playlist):
    with open("playlist.json", "w") as file:
        json.dump(playlist, file)

# ----------------- Session State -----------------
if "playlist" not in st.session_state:
    st.session_state.playlist = load_playlist()

# ----------------- Streamlit Page Setup -----------------
st.set_page_config(page_title="Movie Recommender", layout="wide")
st.title('🎬 Movie Recommender System')

# ----------------- Helper Functions -----------------
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
    try:
        data = requests.get(url).json()
        return "https://image.tmdb.org/t/p/w500" + data.get('poster_path', '')
    except:
        return "https://via.placeholder.com/500x750?text=No+Image"

def fetch_summary(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
    try:
        data = requests.get(url).json()
        return data.get('overview', 'No summary available.')
    except:
        return "Error fetching summary."

def fetch_cast_and_crew(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_API_KEY}"
    try:
        data = requests.get(url).json()
        cast = [actor['name'] for actor in data['cast'][:3]]
        crew = [person['name'] for person in data['crew'] if person['job'] == 'Director']
        return ', '.join(cast), ', '.join(crew)
    except:
        return "N/A", "N/A"

def fetch_rating(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
    try:
        data = requests.get(url).json()
        return data.get('vote_average', 'N/A')
    except:
        return "N/A"

def fetch_trailer(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}"
    try:
        data = requests.get(url).json()
        for video in data['results']:
            if video['site'] == 'YouTube' and video['type'] == 'Trailer':
                return f"https://www.youtube.com/watch?v={video['key']}"
        return None
    except:
        return None

def fetch_new_releases():
    url = f"https://api.themoviedb.org/3/movie/now_playing?api_key={TMDB_API_KEY}&language=en-US&page=1"
    try:
        data = requests.get(url).json()
        return [(movie['title'], fetch_poster(movie['id'])) for movie in data['results'][:5]]
    except:
        return []

def recommend(movie_name):
    index = movies[movies['title'] == movie_name].index[0]
    distance = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda vector: vector[1])
    recommended_movie = []
    recommended_poster = []
    for i in distance[1:6]:
        movie_id = movies.iloc[i[0]].id
        recommended_movie.append(movies.iloc[i[0]].title)
        recommended_poster.append(fetch_poster(movie_id))
    return recommended_movie, recommended_poster

# ----------------- Sidebar - Playlist -----------------
st.sidebar.header("🎞️ Your Favorite Playlist")

if st.sidebar.button("🧹 Clear Playlist"):
    st.session_state.playlist = []
    save_playlist([])

if st.session_state.playlist:
    for title in st.session_state.playlist:
        st.sidebar.write(f"• {title}")
else:
    st.sidebar.write("No favorite movies yet!")


selectvalue = st.selectbox('🎥 Select a movie to get recommendations:', movies_list)

selected_index = movies[movies['title'] == selectvalue].index[0]
selected_movie_id = movies.iloc[selected_index].id

poster = fetch_poster(selected_movie_id)
summary = fetch_summary(selected_movie_id)
cast, director = fetch_cast_and_crew(selected_movie_id)
rating = fetch_rating(selected_movie_id)
trailer_url = fetch_trailer(selected_movie_id)

col1, col2 = st.columns([1, 2])
with col1:
    st.image(poster, width=250)
    if st.button("➕ Add to Playlist"):
        if selectvalue not in st.session_state.playlist:
            st.session_state.playlist.append(selectvalue)
            save_playlist(st.session_state.playlist)
            st.success(f"{selectvalue} added to your playlist!")
        else:
            st.info("Already in playlist")

with col2:
    st.subheader(f"📝 Summary of {selectvalue}")
    st.write(summary)
    st.write(f"⭐ **Rating:** {rating}")
    st.write(f"🎭 **Actors:** {cast}")
    st.write(f"🎬 **Director:** {director}")
    if trailer_url:
        st.markdown(f"[▶️ Watch Trailer]({trailer_url})", unsafe_allow_html=True)


if st.button('🔍 Recommend Movies'):
    movie_names, movie_posters = recommend(selectvalue)
    st.markdown("## 🎯 You Might Also Like These Movies")
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            st.text(movie_names[i])
            st.image(movie_posters[i])


st.markdown("---")
st.markdown("## 🆕 Recently Released Movies")
new_releases = fetch_new_releases()
cols = st.columns(5)
for i, (title, poster_url) in enumerate(new_releases):
    with cols[i]:
        st.text(title)
        st.image(poster_url)
