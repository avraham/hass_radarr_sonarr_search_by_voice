import datetime
import requests
import json
import sys
import os
import configparser
import argparse
import logging

parser = argparse.ArgumentParser()
parser.add_argument("query", help="Term to search",
                    type=str)
parser.add_argument("mode", help="Running mode. 0=Add best match. 1=Full search. 2=Add numeric option. 3=Search by actor",
                    type=str)
parser.add_argument(
    '-d', '--debug',
    help="Print lots of debugging statements",
    action="store_const", dest="loglevel", const=logging.DEBUG,
    default=logging.WARNING,
)
args = parser.parse_args()
logging.basicConfig(level=args.loglevel)

class MovieDownloader:



    '''
    Constrctor

    :param str movie: Title of the movie or option number if mode 2 is used
    :param int mode: 0 | 1 | 2 | 3
        mode 0 - takes the movie string and download best guess from upcoming and recent years.
        mode 1 - search movie string and offers 3 options to choose from.
        mode 2 - download option given from previous search.
        mode 3 - search latest movies by Actor/Actress and offers 5 options to choose from.
    '''
    def __init__(self, movie, mode=0):

        self.loadParameters()

        year = datetime.datetime.now().year
        term = movie
        search_term = term.replace(" ", "%20")

        current_years = [year, year+1, year+2]
        for i  in range(1,49):
         current_years .append(year-i)

        if mode == 0 or mode == 1: # we are making a search by movie title
            # search
            logging.debug("Searching movie: "+movie+" in the last 50 years and upcoming realeases.")
            r = requests.get(self.RADARR_SERVER+"/api/movie/lookup?apikey="+self.RADARR_API+"&term="+search_term)

            if r.status_code == requests.codes.ok:

                media_list = r.json()

                if len(media_list) > 0:

                    if mode == 0: # download best guess
                        # add first occurrence to downloads
                        # we search for newish movies (recent and upcoming movies only)
                        logging.debug("Mode 0: Automatically adding best match.")
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
                        logging.debug("Mode 1: Making a search and providing 3 best options found.")
                        i = 0
                        movies = []
                        while i < len(media_list) and i < 3:
                            data = self.prepare_movie_json(media_list[i])
                            movies.append(data)
                            i += 1
                        msg = self.save_options_found_and_compose_msg(movies)
                        self.tts_google(msg)

                else:
                    logging.debug("Your radarr setup seems fine, but it didn't found a result.")

            else:
                logging.debug("Radarr didn't respond. Please check your conf file setup, such as server_url and api_key fo Radarr.")


        elif mode == 3:
            logging.debug("Mode 3: Making a search by Actor: "+term+" and providing 3 best options found.")
            if self.TMDBID_API_V3 and "http" not in self.TMDBID_API_V3: # search latest movies by Actor/Actress and offers 5 options to choose from.
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
                logging.error("It looks like you haven't setup you api key (v3 auth) for TMDBID. To get one go to https://www.themoviedb.org/settings/api")
        else:
            # add to downloads from download_options file
            try:
                logging.debug("Mode 2: Adding numeric option from previous search in mode 1 or 3")
                download_option = int(movie)-1
                data = {}

                with open(self.HASS_SCRIPTS_PATH+'/download_options.txt') as json_data:
                    movies = json.load(json_data)
                    if download_option > -1 and len(movies) >= download_option:
                        m = movies[download_option]
                        if m['qualityProfileId'] == -1 and m['tmdbId'] > 0:
                            r = requests.get(self.RADARR_SERVER+"/api/movie/lookup/tmdb?apikey="+self.RADARR_API+"&tmdbId="+str(m['tmdbId']))
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
            except ValueError:
                logging.error("Sorry. That was not a valid option. It needs to be a number.")



    def prepare_movie_json(self, media):
        data = {}
        data['title'] = media['title']
        data['qualityProfileId'] = self.RADARR_QUALITY_PROFILE_ID
        data['titleSlug'] = media['titleSlug']
        data['images'] = media['images']
        data['tmdbId'] = media['tmdbId']
        data['rootFolderPath'] = self.RADARR_DOWNLOAD_PATH
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
        r = requests.post(self.RADARR_SERVER+"/api/movie?apikey="+self.RADARR_API,json.dumps(data))
        logging.debug("Trying to add movie...")
        logging.debug("Radarr response is: r.status_code="+str(r.status_code))

        if r.status_code == 201:
            if str(data['cast']) == "":
                self.tts_google("I added the movie "+str(data['title'])+" to your list.")
            else:
                self.tts_google("I added the movie "+str(data['title'])+" with "+str(data['cast'])+" to your list.")
            movie = r.json()
            with open(self.HASS_SCRIPTS_PATH+"/last_download_added.txt", "w") as myfile:
                myfile.write("movie:"+str(movie['id'])+"\n")
        else:
            logging.debug("movie wasn't added")
            res = self.is_movie_already_added(data)
            if res >= 0:
                if res == 0:
                    self.tts_google("I found a movie, but I wasn't able to add it.")
                else:
                    if str(data['cast']) == "":
                        self.tts_google("The movie "+str(data['title'])+" is already on your list.")
                    else:
                        self.tts_google("The movie "+str(data['title'])+" with "+str(data['cast'])+" is already on your list.")
            else:
                self.tts_google("Something went wrong when adding the movie. Please try again.")

    def is_movie_already_added(self, data):
        # print("http://"+self.RADARR_SERVER+"/api/movie?apikey="+self.RADARR_API)
        r = requests.get(self.RADARR_SERVER+"/api/movie?apikey="+self.RADARR_API)
        logging.debug("Checking if movie with tmdbId: "+str(data['tmdbId'])+" already exists on Radarr...")
        logging.debug("Radarr response is: r.status_code="+str(r.status_code))

        found = False
        # print(data['tmdbId'])
        # print(r.status_code)
        if r.status_code == 200:
            media_list = r.json()
            # print(media_list)
            if len(media_list) > 0:
                logging.debug("Searching a match in "+str(len(media_list))+" movies on Radarr...")
                i = 0
                while i < len(media_list) and found == False:
                    tmdbId = media_list[i]['tmdbId']
                    if tmdbId == data['tmdbId']:
                        found = True
                        break;
                    i += 1

            return 1 if found == True else 0

        else:
            logging.error("Error while checking if movie already exists. r.status_code="+str(r.status_code))
            return -1

    def get_cast(self, tmdbId):
        if self.TMDBID_API_V3:
            r = requests.get("https://api.themoviedb.org/3/movie/"+str(tmdbId)+"/credits?api_key="+self.TMDBID_API_V3)
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
        r = requests.get("https://api.themoviedb.org/3/search/person?language=en-US&page=1&include_adult=false&api_key="+self.TMDBID_API_V3+"&query="+actor_name)
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
            r = requests.get("https://api.themoviedb.org/3/discover/movie?language=en-US&page=1&sort_by=release_date.desc&include_adult=false&include_video=false&page=1&primary_release_year=&api_key="+self.TMDBID_API_V3+"&primary_release_year="+str(latest_years[i])+"&with_cast="+str(actor_id))
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

        with open(self.HASS_SCRIPTS_PATH+"/download_options.txt", "w") as myfile:
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
        data = {"entity_id": self.HASS_SPEAKER_ENTITY, "message": msg}

        if self.HASS_API == "" and self.HASS_TOKEN != "":
            headers = {
                'Authorization': 'Bearer '+self.HASS_TOKEN
            }
            r = requests.post(self.HASS_SERVER+"/api/services/tts/"+self.HASS_TTS_SERVICE,json.dumps(data), headers=headers)

        else:
            r = requests.post(self.HASS_SERVER+"/api/services/tts/"+self.HASS_TTS_SERVICE+"?api_password="+self.HASS_API,json.dumps(data))


        # assistant-relay
        # command_data = {"command": msg}
        # r = requests.post("http://"+self.HASS_SERVER+"/api/services/rest_command/gh_broadcast?api_password="+self.HASS_API,json.dumps(command_data))
        print(msg)


    def loadParameters(self):
        config=configparser.ConfigParser()
        dirname, filename = os.path.split(os.path.abspath(sys.argv[0]))
        configFile = os.path.join(dirname, 'ha_radarr_sonarr.conf')

        config.read(configFile)

        self.HASS_SERVER = config.get('HomeAssistant', 'server_url')
        self.HASS_API = config.get('HomeAssistant', 'api_key')
        self.HASS_TOKEN = config.get('HomeAssistant', 'token')
        self.HASS_SCRIPTS_PATH = config.get('HomeAssistant', 'scripts_path')
        self.HASS_SPEAKER_ENTITY = config.get('HomeAssistant', 'speaker_entity')
        self.HASS_TTS_SERVICE = config.get('HomeAssistant', 'tts_service')

        self.RADARR_SERVER = config.get('Radarr', 'server_url')
        self.RADARR_API = config.get('Radarr', 'api_key')
        self.RADARR_DOWNLOAD_PATH = config.get('Radarr', 'root_directory')
        self.RADARR_QUALITY_PROFILE_ID = int(config.get('Radarr', 'profile_id'))

        self.TMDBID_API_V3 = config.get('Services', 'tmdmid_api_key_v3')




        self.checkConfig()


    def checkConfig(self):
        error_messages = []
        warning_messages = []

        if not self.HASS_SERVER:
            error_messages.append('Home Assistant url with port (usually localhost:8123) must be defined')

        if not self.HASS_API and not self.HASS_TOKEN:
            error_messages.append('A Long-lived token or HA API password (legacy) must be defined')

        if not self.HASS_SCRIPTS_PATH:
            error_messages.append('Path were this script is located. must be defined. eg. /users/vr/.homeassistant/scripts or for container (e.g HA SUPERVISED) /config/scripts')

        if not self.HASS_SPEAKER_ENTITY:
            error_messages.append('Home assistant speaker entity_id must be specified. eg. media_player.family_room_speaker')

        if not self.HASS_TTS_SERVICE:
            error_messages.append('Home assistant text-to-speech service must be specified.')

        if not self.RADARR_SERVER:
            error_messages.append('Radarr url with port (usually :7878) must be defined')

        if not self.RADARR_API:
            error_messages.append('Radarr API Key must be defined')

        if not self.RADARR_DOWNLOAD_PATH:
            error_messages.append('Radarr root_directory also knwon as rootFolderPath must be defined')

        if self.RADARR_QUALITY_PROFILE_ID == 0:
            error_messages.append('Radarr quality profile id must be defined. Default value is 4 (1080p)')

        if not self.TMDBID_API_V3:
            warning_messages.append("Warning. tmdmid_api_key_v3 (optional)(recommended) is not set. You won't be able to search movies by actor or actress and your speaker's feedback will miss cast details for movies. https://www.themoviedb.org/settings/api v3 auth")

        if len(error_messages) > 0:
            print('Problem(s) in configuration file :')
            for m in error_messages:
                print(m)

        if len(warning_messages) > 0:
            for m in warning_messages:
                print(m)

        if len(error_messages) > 0:
            exit(1)


# query = sys.argv[1]
# mode = sys.argv[2]

# full_search = sys.argv[2]
# downloading_from_file = sys.argv[3]
# download_option = int(sys.argv[4])-1

# print(query)
# print(mode)
# print(downloading_from_file)
# print(download_option)

downloader = MovieDownloader(args.query, int(args.mode))
