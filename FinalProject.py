import streamlit as st
import requests
import pandas as pd
import numpy as np
import geocoder
import re

st.set_page_config(page_title="GameGenie")
st.title("GameGenie")
st.subheader("Discover Your Next Favorite Game")

api_key = "df2f3d0bb58b4768afa2fe240fa6ed8b"

page_color = """
<style>
 [data-testid="stSidebar"] > div:first-child {
 background-color: #c1eefc;}
 [data-testid="stHeader"] {
 background: rgba(0,0,0,0);
 }
 </style>
"""
st.markdown(page_color,unsafe_allow_html=True)


################ FUNCTIONS ###################################
@st.cache_data
def generate_list_of_genres():
    genres_url = f"https://api.rawg.io/api/genres?key={api_key}"
    genres_dict = requests.get(genres_url).json()
    #st.write(genres_dict)
    return genres_dict

genres_dict = generate_list_of_genres()
genres_list = []
for i in genres_dict["results"]:
    genres_list.append(i["name"])
genres_list.insert(0, "")


@st.cache_data
def generate_list_of_platforms():
    platforms_url = f"https://api.rawg.io/api/platforms?key={api_key}"
    platforms_dict = requests.get(platforms_url).json()
    return platforms_dict

platforms_dict = generate_list_of_platforms()
platforms_list = []
for i in platforms_dict["results"]:
    platforms_list.append(i["name"])
platforms_list.insert(0, "")


@st.cache_data
def generate_list_of_tags():
    tags_url = f"https://api.rawg.io/api/tags?key={api_key}"
    tags_dict = requests.get(tags_url).json()
    return tags_dict

tags_dict = generate_list_of_tags()
tags_list = []
for i in tags_dict["results"]:
    tags_list.append(i["name"])
tags_list.insert(0, "")

# Generate a list of games (10 pages)
tags_list2 = []
def generate_list_of_games():
    games_url = f"https://api.rawg.io/api/games?key={api_key}"
    games_dict = {"results": []}
    for page in range(1, 12):
        page_url = f"{games_url}&page={page}"
        page_data = requests.get(page_url).json()
        #st.write(page_data)
        games_dict["results"].extend(page_data["results"])
    return games_dict
#games_dict = generate_list_of_games()




################### SIDEBAR ######################################

st.sidebar.header("Filter your Results")

# Game genre selection
genres_selected = st.sidebar.multiselect("Select Game Genres (required)", genres_list)

# Game platform selection
platforms_selected = st.sidebar.selectbox("Select a Platform (required)", options=platforms_list)

# Game rating selection
rating = st.sidebar.select_slider(
    "Select Game's ESRB Rating",
    options=['', 'Everyone', 'Everyone 10+', 'Teen', 'Mature', 'Adults Only'])


# create a number input widget that accepts integer values from 1 to 5
user_input = st.sidebar.number_input("Enter Game's Top Rating (1-5)", min_value=0, max_value=5, step=1)
# Game tags selection
tags_selected = st.sidebar.checkbox("Filter by Game Tags", value=False)
if tags_selected:
    selected_tags = st.sidebar.multiselect("Select Game Tags", tags_list)

#########################################################################
search_button = st.sidebar.button("Search")

test = []
games_filtered = []

# Generate and filter list of games
if platforms_selected and genres_selected:
    games_dict = generate_list_of_games()
    for game in games_dict["results"]:
        platforms = [p["platform"]["name"] for p in game["platforms"]]
        if platforms_selected in platforms and all(
                genre in [g["name"] for g in game["genres"]] for genre in genres_selected):
            if user_input != 0 and game["rating_top"] != user_input:
                continue
            if tags_selected:
                game_tags = [t["name"] for t in game["tags"]]
                if all(tag in game_tags for tag in selected_tags):
                    if rating and not game.get("esrb_rating") or game.get("esrb_rating") and rating.lower() != \
                            game["esrb_rating"]["name"].lower():
                        continue
                    games_filtered.append(game)
                elif not rating or game.get("esrb_rating") and rating.lower() == game["esrb_rating"]["name"].lower():
                    continue
            else:
                if rating and not game.get("esrb_rating") or game.get("esrb_rating") and rating.lower() != \
                        game["esrb_rating"]["name"].lower():
                    continue
                games_filtered.append(game)

# Filter by tags if selected
if tags_selected and games_filtered:
    games_filtered_by_tags = []
    for game in games_filtered:
        game_tags = [t["name"] for t in game["tags"]]
        if all(tag in game_tags for tag in selected_tags):
            games_filtered_by_tags.append(game)
    games_filtered = games_filtered_by_tags


if search_button:
    if platforms_selected != "" and genres_selected:
        if not games_filtered:
            st.warning("No games found. Please try again with different filters.")
        else:
            st.success(f"Here are games with {platforms_selected} as a platform and {genres_selected} as genres:")

    else:
        st.warning("Please enter required fields")

if games_filtered:
    # Display list of games
    for game in games_filtered:
        test.append(game["name"])
    game_choice = st.selectbox("Select a game:", test)
    selected_game = next((game for game in games_filtered if game["name"] == game_choice), None)
    if selected_game:
        # Display the details of the selected game
        st.image(selected_game["background_image"], use_column_width=True)
        #st.write("Name:", selected_game["name"])
        st.subheader(selected_game["name"])
        col1, col2= st.columns(2)
        with col1:
            st.write("Released:", selected_game["released"])
            st.write("Metacritic Rating:", selected_game["metacritic"])
            game_playtime = selected_game["playtime"]
            st.write(f"Playtime: {game_playtime} hour(s)")

        game_details_url = f"https://api.rawg.io/api/games/{selected_game['id']}?key={api_key}"
        game_details_response = requests.get(game_details_url)
        game_details_data = game_details_response.json()
        #st.write(game_details_data)

        # Display the Game Description
        st.write("About:")
        description_html = game_details_data["description"]
        description_text = re.sub('<[^<]+?>', '', description_html)
        st.write(description_text)

        game_details_ratings = game_details_data["ratings"]
        game_details_esrb = game_details_data["esrb_rating"]
        game_details_tags = game_details_data["tags"]
        game_details_topRating = game_details_data["rating_top"]
        game_details_developers = game_details_data["developers"]

        with col1:
            if game_details_topRating:
                st.write(f"Top Rating: {game_details_topRating}")
        with col2:
            # Display game ESRB rating
            if game_details_esrb:
                esrb_name = game_details_esrb["name"]
                st.write(f"ESRB Rating: {esrb_name}")
                #st.write(game_details_esrb["name"])
            else:
                st.warning("No ESRB rating found for this game")

            # Displays list of Developers
            if game_details_data.get("developers"):
                developers_list = [developer["name"] for developer in game_details_data["developers"]]
                developers_str = ", ".join(developers_list)
                st.write("Developers: " + developers_str)

            # Displays list of Publishers
            if game_details_data.get("publishers"):
                publishers_list = [publisher["name"] for publisher in game_details_data["publishers"]]
                publishers_str = ", ".join(publishers_list)
                st.write("Publishers: " + publishers_str)

        st.write("Reviews:")
        # Create tabs component
        tabs = st.tabs(["Bar chart", "Line Chart"])
        with tabs[0]:
            # Bar chart of game's ratings
            if game_details_ratings:
                ratings_dict = {}
                for rating in game_details_ratings:
                    rating_name = rating["title"]
                    rating_count = rating["count"]
                    ratings_dict[rating_name] = rating_count
                st.bar_chart(ratings_dict)

        with tabs[1]:
            # Line chart of game's ratings
            if game_details_ratings:
                ratings_dict = {}
                for rating in game_details_ratings:
                    rating_name = rating["title"]
                    rating_count = rating["count"]
                    ratings_dict[rating_name] = rating_count
                st.line_chart(ratings_dict)

        col3, col4 = st.columns(2)

        with col3:
            # Display 2 trailers for the selected game on button click
            if st.button("Show Game Trailers"):
                trailers_url = f"https://api.rawg.io/api/games/{selected_game['id']}/movies?key={api_key}"
                trailers_response = requests.get(trailers_url)
                trailers_data = trailers_response.json()
                trailers_results = trailers_data['results']
                num_of_trailers_to_display = 2
                if trailers_results:
                    st.write("Trailers:")
                    for i in range(min(num_of_trailers_to_display, len(trailers_results))):
                        trailer = trailers_results[i]
                        st.write(trailer['name'])
                        st.video(trailer['data']['max'])
                else:
                    st.warning("No trailers available for this game.")

        with col4:
            # Display 2 screenshots for the selected game on button click
            if st.button("Show Game Screenshots"):
                screenshots_url = f"https://api.rawg.io/api/games/{selected_game['id']}/screenshots?key={api_key}"
                screenshots_response = requests.get(screenshots_url)
                screenshots_data = screenshots_response.json()
                #st.write(screenshots_data)
                screenshots_results = screenshots_data['results']
                num_of_screenshots_to_display = 2
                if screenshots_results:
                    st.write("Screenshots:")
                    for i in range(min(num_of_screenshots_to_display, len(screenshots_results))):
                        screenshot = screenshots_results[i]
                        st.image(screenshot['image'])
                else:
                    st.warning("No screenshots available for this game.")

        # Display game's genres
        if game_details_data.get("genres"):
            genres_list = [genre["name"] for genre in game_details_data["genres"]]
            genres_str = ", ".join(genres_list)
            st.write("Genres:  " + genres_str)

        # Display game's tags
        if game_details_tags:
            tags_list = [tag["name"] for tag in game_details_tags]
            tags_str = ", ".join(tags_list)
            st.write("Tags:  " + tags_str)

        # Display game's platforms
        if "platforms" in selected_game:
            platforms_list = [platform["platform"]["name"] for platform in selected_game["platforms"]]
            platforms_str = ", ".join(platforms_list)
            st.write("Platforms: " + platforms_str)



        # Call the API to get suggested games
        url = f"https://api.rawg.io/api/games/{selected_game['id']}/game-series?key={api_key}"
        response = requests.get(url)
        if response:
            st.write("Games Part of the Same Series:")
            suggested_games_data = response.json()
            #st.write(suggested_games_data)
            if suggested_games_data["count"] == 0:
                st.info("No games found")
            else:
                # Extract relevant data and create DataFrame
                suggestions = []
                for suggestion in suggested_games_data["results"]:
                    row = {
                        "Name": suggestion["name"],
                        "Metacritic": suggestion["metacritic"],
                        "Top Rating": suggestion["rating_top"],
                        "Playtime (hrs)": suggestion["playtime"],
                        "Genres": ", ".join([genre["name"] for genre in suggestion["genres"]]),
                        "Platforms": ", ".join([platform["platform"]["name"] for platform in suggestion["platforms"]])
                    }
                    suggestions.append(row)

                df = pd.DataFrame(suggestions)

                # Display DataFrame
                st.dataframe(df)

        else:
            st.info("No suggested games found")

        # Get the user's location based on their IP address
        g = geocoder.ipinfo('me')
        lat, lon = g.latlng
        #st.write(lat)
        #st.write(lon)

        # Call the Mapbox API to search for Target stores near the user's location
        url = f'https://api.mapbox.com/geocoding/v5/mapbox.places/Target.json'
        params = {
            'access_token': "pk.eyJ1IjoiY2hhcmxvdHRldzkyMyIsImEiOiJjbGdsdjlkd3kxc3l4M2VvMnlqdWZucGh5In0.CahQ-6p11MJgIsP7uzdZzA",
            'proximity': f'{lon},{lat}',
            'types': 'poi',
            'limit': 1,
        }
        response = requests.get(url, params=params)
        #st.write(response.json())

        # Check if the API request was successful
        if response.status_code != 200:
            st.error(f"API request failed with status code {response.status_code}")
        else:
            # Parse the API response and get the latitude and longitude of the nearest Target store
            results = response.json()['features']
            if len(results) == 0:
                st.warning("No Target stores found near your location")
            else:
                nearest = results[0]
                nearest_lat, nearest_lon = nearest['geometry']['coordinates']

                # Create a pandas DataFrame with the user's location and the nearest Target store
                df = pd.DataFrame({
                    #'lat': [lat, nearest_lat],
                    #'lon': [lon, nearest_lon],
                    'lat': [nearest_lon],
                    'lon': [nearest_lat],
                    'name': ["Nearest Target"],#['Your Location'],#, 'Nearest Target'],
                })

                # Print some diagnostic information
                #st.write("User's location:", lat, lon)
                #st.write("Nearest Target store:", nearest_lat, nearest_lon)

                st.write("Nearby Game Store:")

                # Display the user's location and the nearest Target store on a map with markers
                st.map(df, zoom=13)

    else:
        st.warning("Could not find the selected game.")
