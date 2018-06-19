import datetime
import requests
import json
import sys
import os

# User defined variables

# Home assistant URL eg. localhost:8123 with port
HASS_SERVER=""

# Home assistant api password
HASS_API=""

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
    '''
    def __init__(self, movie, mode=0):


        year = datetime.datetime.now().year
        term = movie
        search_term = term.replace(" ", "%20")
        current_years = [ year-1, year, year+1, year+2]

        if mode != 2: # we are making a query
            # query

            r = requests.get("http://"+RADARR_SERVER+"/api/movie/lookup?apikey="+RADARR_API+"&term="+search_term)

            if r.status_code == requests.codes.ok:

                media_list = r.json()

                if len(media_list) > 0:

                    if mode == 0: # download best guess
                        # add first occurrence to downloads
                        # we search for recent movies only
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
                    else: # search movie and give 3 options
                        # add to download_options file and read them out loud
                        i = 0
                        movies = []
                        while i < len(media_list) and i < 3:
                            data = self.prepare_movie_json(media_list[i])
                            movies.append(data)
                            i += 1
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
                        self.tts_google(msg)
                else:
                    self.tts_google("I didn't find any movie with that title.")
            else:
                self.tts_google("Something went wrong with the query.")
        else:
            # add to downloads from download_options file
            download_option = int(movie)-1

            with open(HASS_SCRIPTS_PATH+'/download_options.txt') as json_data:
                movies = json.load(json_data)
                if download_option > -1 and len(movies) >= download_option:
                    m = movies[download_option]
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

    def add_movie(self, data):
        r = requests.post("http://"+RADARR_SERVER+"/api/movie?apikey="+RADARR_API,json.dumps(data))

        if r.status_code == 201:
            self.tts_google("I added the movie "+str(data['title'])+" with "+str(data['cast'])+" to your download list.")
            movie = r.json()
            with open(HASS_SCRIPTS_PATH+"/last_download_added.txt", "w") as myfile:
                myfile.write("movie:"+str(movie['id'])+"\n")
        else:
            self.tts_google("I found a movie, but I wasn't able to add it to your download list. It's possible I already added it.")

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

    def tts_google(self, msg):
        data = {"entity_id": HASS_GOOGLE_HOME_ENTITY, "message": msg}
        r = requests.post("http://"+HASS_SERVER+"/api/services/tts/google_say?api_password="+HASS_API,json.dumps(data))
        # print(msg)


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
