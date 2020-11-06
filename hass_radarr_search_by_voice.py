import datetime
import requests
import json
import sys
import os

# User defined variables

# Home assistant URL eg. localhost:8123 with port
HASS_SERVER=""

# Home assistant legacy api password
HASS_API="" # leave blank if using long-lived token

# Home assistant long-lived token
HASS_TOKEN="" # leave blank if using legacy API

# Home assistant scripts path eg. /users/vr/.homeassistant/scripts
HASS_SCRIPTS_PATH=""

# Home assistant google home entity_id  eg. media_player.family_room_speaker
HASS_GOOGLE_HOME_ENTITY=""


RADARR_SERVER="" # with port
RADARR_API=""
RADARR_DOWNLOAD_PATH="" # aka rootFolderPath
RADARR_QUALITY_PROFILE_ID=4  # 1080p

TMDBID_API=""

# ------------------------------------


class MovieDownloader:



    '''
    Constrctor

    :param str movie: Title of the movie or option number if mode 2 is used
    :param int mode: 0 | 1 | 2
        mode 0 - takes the movie string and download best guess from upcoming and recent years.
        mode 1 - search movie string and offers 3 options to choose from.
        mode 2 - download option given from previous search.
        mode 3 - search latest movies by Actor/Actress and offers 5 options to choose from.
    '''
    def __init__(self, movie, mode=0):


        year = datetime.datetime.now().year
        term = movie
        search_term = term.replace(" ", "%20")
        current_years = [year, year+1, year+2]
        for i  in range(1,49):
         current_years .append(year-i)

        if mode == 0 or mode == 1: # we are making a search by movie title
            # search

            r = requests.get("http://"+RADARR_SERVER+"/api/movie/lookup?apikey="+RADARR_API+"&term="+search_term)

            if r.status_code == requests.codes.ok:

                media_list = r.json()

                if len(media_list) > 0:

                    if mode == 0: # download best guess
                        # add first occurrence to downloads
                        # we search for newish movies (recent and upcoming movies only)
                        i = 0
                        found = False
                        while i < len(media_list) and found == False:
                            year = media_list[i]['year']
                            if year in current_years:
                                found = True
                                data = self.prepare_movie_json(media_list[i])
                                self.add_movie(data)
                                break;
                            i += 1
                        if found == False:
                            self.tts_google("No recent movie found. Try with the command Search movie.")

                    elif mode == 1: # search movie and give 3 options
                        # add to download_options file and read them out loud
                        i = 0
                        movies = []
                        while i < len(media_list) and i < 3:
                            data = self.prepare_movie_json(media_list[i])
                            movies.append(data)
                            i += 1
                        msg = self.save_options_found_and_compose_msg(movies)
                        self.tts_google(msg)


        elif mode == 3:  # search latest movies by Actor/Actress and offers 5 options to choose from.
            actor_id = self.get_actor_id(search_term)
            if actor_id > 0:
                movies = []
                movies = self.get_actors_latest_movies(actor_id, year)
                if len(movies) > 0:
                    msg = self.save_options_found_and_compose_msg(movies)
                    self.tts_google(msg)
                else:
                    self.tts_google("No movies were found.")
            else:
                self.tts_google("No actor or actress was found.")
        else:
            # add to downloads from download_options file
            download_option = int(movie)-1
            data = {}

            with open(HASS_SCRIPTS_PATH+'/download_options.txt') as json_data:
                movies = json.load(json_data)
                if download_option > -1 and len(movies) >= download_option:
                    m = movies[download_option]
                    if m['qualityProfileId'] == -1 and m['tmdbId'] > 0:
                        r = requests.get("http://"+RADARR_SERVER+"/api/movie/lookup/tmdb?apikey="+RADARR_API+"&tmdbId="+str(m['tmdbId']))
                        if r.status_code == requests.codes.ok:
                            media_list = r.json()
                            # print(media_list)
                            # if len(media_list) > 0:
                            data = self.prepare_movie_json(media_list)
                    else:
                        data = self.prepare_movie_json(m)
                    self.add_movie(data)
                else:
                    self.tts_google("There's no such option.")


    def prepare_movie_json(self, media):
        data = {}
        data['title'] = media['title']
        data['qualityProfileId'] = RADARR_QUALITY_PROFILE_ID
        data['titleSlug'] = media['titleSlug']
        data['images'] = media['images']
        data['tmdbId'] = media['tmdbId']
        data['rootFolderPath'] = RADARR_DOWNLOAD_PATH
        data['monitored'] = True
        data['minimumAvailability'] = 'released'
        data['year'] = media['year']
        data['cast'] = self.get_cast(data['tmdbId'])

        return data

    def prepare_barebone_movie_json(self, tmdbId, title):
        data = {}
        data['title'] = title
        data['qualityProfileId'] = -1
        data['titleSlug'] = 0
        data['images'] = 0
        data['tmdbId'] = tmdbId
        data['rootFolderPath'] = 0
        data['monitored'] = 0
        data['minimumAvailability'] = 0
        data['year'] = 0
        data['cast'] = ""

        return data

    def add_movie(self, data):
        r = requests.post("http://"+RADARR_SERVER+"/api/movie?apikey="+RADARR_API,json.dumps(data))

        if r.status_code == 201:
            self.tts_google("I added the movie "+str(data['title'])+" with "+str(data['cast'])+" to your download list.")
            movie = r.json()
            with open(HASS_SCRIPTS_PATH+"/last_download_added.txt", "w") as myfile:
                myfile.write("movie:"+str(movie['id'])+"\n")
        else:
            res = self.is_movie_already_added(data)
            if res >= 0:
                if res == 0:
                    self.tts_google("I found a movie, but I wasn't able to add it.")
                else:
                    self.tts_google("The movie "+str(data['title'])+" with "+str(data['cast'])+" is already on your list.")
            else:
                self.tts_google("Something went wrong when adding the movie.")

    def is_movie_already_added(self, data):
        # print("http://"+RADARR_SERVER+"/api/movie?apikey="+RADARR_API)
        r = requests.get("http://"+RADARR_SERVER+"/api/movie?apikey="+RADARR_API)

        found = False
        # print(data['tmdbId'])
        # print(r.status_code)
        if r.status_code == 200:
            media_list = r.json()
            # print(media_list)
            if len(media_list) > 0:
                i = 0
                while i < len(media_list) and found == False:
                    tmdbId = media_list[i]['tmdbId']
                    if tmdbId == data['tmdbId']:
                        found = True
                        break;
                    i += 1

            return 1 if found == True else 0

        else:
            return -1

    def get_cast(self, movieId):
        r = requests.get("https://api.themoviedb.org/3/movie/"+str(movieId)+"/credits?api_key="+TMDBID_API)
        if r.status_code == requests.codes.ok:
            movie = r.json()
            cast = movie['cast']
            if len(cast) > 1:
                return(cast[0]['name']+" and "+cast[1]['name'])
            else:
                return(cast[0]['name'])
        else:
            return("")

    def get_actor_id(self, actor_name):
        r = requests.get("https://api.themoviedb.org/3/search/person?language=en-US&page=1&include_adult=false&api_key="+TMDBID_API+"&query="+actor_name)
        if r.status_code == requests.codes.ok:
            results = r.json()
            if int(results['total_results']) > 0:
                return(int(results['results'][0]['id']))
            else:
                return(-1)
        else:
            return(-1)

    def get_actors_latest_movies(self, actor_id, year):
        latest_years = [ year+1, year, year-1, year-2]
        i = 0
        movies = []
        while i < len(latest_years) and len(movies) < 5:
            r = requests.get("https://api.themoviedb.org/3/discover/movie?language=en-US&page=1&sort_by=release_date.desc&include_adult=false&include_video=false&page=1&primary_release_year=&api_key="+TMDBID_API+"&primary_release_year="+str(latest_years[i])+"&with_cast="+str(actor_id))
            if r.status_code == requests.codes.ok:
                results = r.json()
                if int(results['total_results']) > 0:
                    for movie in results['results']:
                        if len(movies) < 5:
                            data = self.prepare_barebone_movie_json(int(movie["id"]), movie["title"])
                            movies.append(data)
            i += 1
        return(movies)

    def save_options_found_and_compose_msg(self, movies):
        msg=""

        with open(HASS_SCRIPTS_PATH+"/download_options.txt", "w") as myfile:
            json.dump(movies, myfile)

        i = 0
        if len(movies) > 1:
            msg = "I found "+str(len(movies))+" options.\n"
        else:
            msg = "I found "+str(len(movies))+" option.\n"
        while i < len(movies):
            m = movies[i]
            if str(m['cast']) != "":
                msg = msg+"Option "+str(i+1)+", "+str(m['title'])+" with "+str(m['cast'])+".\n"
            else:
                msg = msg+"Option "+str(i+1)+", "+str(m['title'])+". "
            i += 1
        return msg

    def tts_google(self, msg):
        data = {"entity_id": HASS_GOOGLE_HOME_ENTITY, "message": msg}

        if HASS_API == "" and HASS_TOKEN != "":
            headers = {
                'Authorization': 'Bearer '+HASS_TOKEN
            }
            r = requests.post("http://"+HASS_SERVER+"/api/services/tts/google_translate_say",json.dumps(data), headers=headers)

        else:
            r = requests.post("http://"+HASS_SERVER+"/api/services/tts/google__translate_say?api_password="+HASS_API,json.dumps(data))


        # assistant-relay
        # command_data = {"command": msg}
        # r = requests.post("http://"+HASS_SERVER+"/api/services/rest_command/gh_broadcast?api_password="+HASS_API,json.dumps(command_data))
        print(msg)


query = sys.argv[1]
mode = sys.argv[2]

# full_search = sys.argv[2]
# downloading_from_file = sys.argv[3]
# download_option = int(sys.argv[4])-1

print(query)
print(mode)
# print(downloading_from_file)
# print(download_option)

downloader = MovieDownloader(query, int(mode))
