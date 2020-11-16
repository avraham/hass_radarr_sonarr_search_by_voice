import datetime
import requests
import json
import sys
import os
import configparser


# ------------------------------------


class ShowDownloader:



    '''
    Constrctor

    :param str show: Title of the tv show or option number if mode 2 is used
    :param int mode: 0 | 1 | 2
        mode 0 - takes the tv show string and download best guess from upcoming and recent years.
        mode 1 - search tv show string and offers 3 options to choose from.
        mode 2 - download option given from previous search.
    :param str monitor: missing | future
        missing - Monitors episodes that do not have files or have not aired yet.
        future - Monitors episodes that have not aired yet.
    '''
    def __init__(self, show, mode=0, monitor='future'):

        self.monitor = monitor
        self.loadParameters()

        year = datetime.datetime.now().year
        term = show
        search_term = term.replace(" ", "%20")
        current_years = [year, year+1, year+2]
        for i  in range(1,69):
         current_years .append(year-i)


        if mode == 0 or mode == 1: # we are making a search by series title
            # search

            r = requests.get("http://"+self.SONARR_SERVER+"/api/series/lookup?term="+search_term+"&apikey="+self.SONARR_API)

            if r.status_code == requests.codes.ok:

                media_list = r.json()

                if len(media_list) > 0:

                    if mode == 0: # download best guess
                        # add first occurrence to downloads
                        # we search for newish show (recent and upcoming show only)
                        i = 0
                        found = False
                        while i < len(media_list) and found == False:
                            year = media_list[i]['year']
                            if year in current_years:
                                found = True
                                data = self.prepare_show_json(media_list[i])
                                self.add_show(data)
                                break;
                            i += 1
                        if found == False:
                            self.tts_google("I didn't find the tv show. Try again with the search option.")

                    elif mode == 1: # search tv show and give 3 options
                        # add to download_options file and read them out loud
                        i = 0
                        show = []
                        while i < len(media_list) and i < 3:
                            data = self.prepare_show_json(media_list[i])
                            show.append(data)
                            i += 1
                        msg = self.save_options_found_and_compose_msg(show)
                        self.tts_google(msg)


        # elif mode == 3:  # search latest show by Actor/Actress and offers 5 options to choose from.
        #     actor_id = self.get_actor_id(search_term)
        #     if actor_id > 0:
        #         show = []
        #         show = self.get_actors_latest_show(actor_id, year)
        #         if len(show) > 0:
        #             msg = self.save_options_found_and_compose_msg(show)
        #             self.tts_google(msg)
        #         else:
        #             self.tts_google("Your tv show was not found.")
        #     else:
        #         self.tts_google("The actor was not found.")
        else:
            # add to downloads from download_options file
            download_option = int(show)-1
            data = {}

            with open(self.HASS_SCRIPTS_PATH+'/download_tvshow_options.txt') as json_data:
                show = json.load(json_data)
                if download_option > -1 and len(show) >= download_option:
                    m = show[download_option]
                    if m['profileId'] == -1 and m['tvdbId'] > 0:
                        r = requests.get("http://"+self.SONARR_SERVER+"/api/series/lookup?term=tvdb:"+str(m['tvdbId'])+"&apikey="+self.SONARR_API)
                        if r.status_code == requests.codes.ok:
                            media_list = r.json()
                            # print(media_list)
                            # if len(media_list) > 0:
                            data = self.prepare_show_json(media_list)
                    else:
                        data = self.prepare_show_json(m)
                    self.add_show(data)
                else:
                    self.tts_google("There are no options.")


    def prepare_show_json(self, media):
        data = {}
        addOptions = {}

        if self.monitor == "missing":
            addOptions['ignoreEpisodesWithFiles'] = True
            addOptions['ignoreEpisodesWithoutFiles'] = False
            addOptions['searchForMissingEpisodes'] = True
        elif self.monitor == "future":
            addOptions['ignoreEpisodesWithFiles'] = True
            addOptions['ignoreEpisodesWithoutFiles'] = True
            addOptions['searchForMissingEpisodes'] = False

        data['title'] = media['title']
        data['profileId'] = self.SONARR_QUALITY_PROFILE_ID
        data['titleSlug'] = media['titleSlug']
        data['images'] = media['images']
        data['seasons'] = media['seasons']
        data['imdbId'] = media['imdbId']
        data['tvdbId'] = media['tvdbId']
        data['seasonFolder'] = True
        data['rootFolderPath'] = self.SONARR_DOWNLOAD_PATH
        data['addOptions'] = addOptions
        data['year'] = media['year']
        data['cast'] = self.get_cast(data['imdbId'])

        return data

    def prepare_barebone_show_json(self, tvdbId, title):
        data = {}
        data['title'] = title
        data['profileId'] = -1
        data['titleSlug'] = 0
        data['images'] = 0
        data['seasons'] = 0
        data['imdbId'] = ""
        data['tvdbId'] = tvdbId
        data['seasonFolder'] = 0
        data['rootFolderPath'] = 0
        data['year'] = 0
        data['cast'] = ""

        return data

    def add_show(self, data):
        r = requests.post("http://"+self.SONARR_SERVER+"/api/series?apikey="+self.SONARR_API,json.dumps(data))

        if r.status_code == 201:
            self.tts_google("I added the tv show "+str(data['title'])+" "+str(data['year'])+" with, "+str(data['cast'])+" to your list.")
            show = r.json()
            with open(self.HASS_SCRIPTS_PATH+"/last_tvshow_download_added.txt", "w") as myfile:
                myfile.write("show:"+str(show['id'])+"\n")
        else:
            res = self.is_show_already_added(data)
            if res >= 0:
                if res == 0:
                    self.tts_google("I found your tv show but I was not able to add it to your list.")
                else:
                    self.tts_google("The tv show, "+str(data['title'])+" "+str(data['year'])+" with, "+str(data['cast'])+" is already in your list.")
            else:
                self.tts_google("Something wrong occured when trying to add the tv show to your list.")

    def is_show_already_added(self, data):
        # print("http://"+self.SONARR_SERVER+"/api/movie?apikey="+self.SONARR_API)
        r = requests.get("http://"+self.SONARR_SERVER+"/api/series?apikey="+self.SONARR_API)

        found = False
        # print(data['tvdbId'])
        # print(r.status_code)
        if r.status_code == 200:
            media_list = r.json()
            # print(media_list)
            if len(media_list) > 0:
                i = 0
                while i < len(media_list) and found == False:
                    tvdbId = media_list[i]['tvdbId']
                    if tvdbId == data['tvdbId']:
                        found = True
                        break;
                    i += 1

            return 1 if found == True else 0

        else:
            return -1

    def get_cast(self, imdbId):
        if self.OMDB_API:
            r = requests.get("http://www.omdbapi.com/?i="+str(imdbId)+"&apikey="+self.OMDB_API)
            if r.status_code == requests.codes.ok:
                movie = r.json()
                cast = movie['Actors'].split(',')
                if len(cast) > 0:
                    if len(cast) > 1:
                        return(cast[0]+" and"+cast[1])
                    else:
                        return(cast[0])
                else:
                    return("")
            else:
                return("")
        else:
            return("")
        # TVDB_API
        # r = requests.get("https://api.thetvdb.com/series/"+str(tvdbId)+"/actors")
        # if r.status_code == requests.codes.ok:
        #     series = r.json()
        #     data = series['data']
        #     if len(data) > 1:
        #         return(data[0]['name']+" et "+data[1]['name'])
        #     else:
        #         return(data[0]['name'])
        # else:
        #     return("")

    #  POSSIBLE FUTURE FEATURE IF TVDB_API BECOMES FREE
    # def get_actor_id(self, actor_name):
    #     r = requests.get("https://api.thetvdb.com/3/search/person?language=en-US&page=1&include_adult=false&api_key="+TVDB_API+"&query="+actor_name)
    #     if r.status_code == requests.codes.ok:
    #         results = r.json()
    #         if int(results['total_results']) > 0:
    #             return(int(results['results'][0]['id']))
    #         else:
    #             return(-1)
    #     else:
    #         return(-1)
    #
    # def get_actors_latest_show(self, actor_id, year):
    #     latest_years = [ year+1, year, year-1, year-2]
    #     i = 0
    #     shows = []
    #     while i < len(latest_years) and len(show) < 5:
    #         r = requests.get("https://api.thetvdb.com/3/discover/series?language=en-US&page=1&sort_by=release_date.desc&include_adult=false&include_video=false&page=1&primary_release_year=&api_key="+TVDB_API+"&primary_release_year="+str(latest_years[i])+"&with_cast="+str(actor_id))
    #         if r.status_code == requests.codes.ok:
    #             results = r.json()
    #             if int(results['total_results']) > 0:
    #                 for show in results['results']:
    #                     if len(show) < 5:
    #                         data = self.prepare_barebone_show_json(int(show["id"]), show["title"])
    #                         show.append(data)
    #         i += 1
    #     return(show)

    def save_options_found_and_compose_msg(self, show):
        msg=""

        with open(self.HASS_SCRIPTS_PATH+"/download_tvshow_options.txt", "w") as myfile:
            json.dump(show, myfile)

        i = 0
        if len(show) > 1:
            msg = "I found, "+str(len(show))+" options.\n"
        else:
            msg = "I found, "+str(len(show))+" option.\n"
        while i < len(show):
            m = show[i]
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
            r = requests.post("http://"+self.HASS_SERVER+"/api/services/tts/"+self.HASS_TTS_SERVICE,json.dumps(data), headers=headers)

        else:
            r = requests.post("http://"+self.HASS_SERVER+"/api/services/tts/"+self.HASS_TTS_SERVICE+"?api_password="+self.HASS_API,json.dumps(data))


        # assistant-relay
        # command_data = {"command": msg}
        # r = requests.post("http://"+self.HASS_SERVER+"/api/services/rest_command/gh_broadcast?api_password="+self.HASS_API,json.dumps(command_data))
        print(msg)


    def loadParameters(self):
        config=configparser.ConfigParser()
        configFile = './ha_radarr_sonarr.conf'


        config.read('./ha_radarr_sonarr.conf')

        self.HASS_SERVER = config.get('HomeAssistant', 'server_url')
        self.HASS_API = config.get('HomeAssistant', 'api_key')
        self.HASS_TOKEN = config.get('HomeAssistant', 'token')
        self.HASS_SCRIPTS_PATH = config.get('HomeAssistant', 'scripts_path')
        self.HASS_SPEAKER_ENTITY = config.get('HomeAssistant', 'speaker_entity')
        self.HASS_TTS_SERVICE = config.get('HomeAssistant', 'tts_service')

        self.SONARR_SERVER = config.get('Sonarr', 'server_url')
        self.SONARR_API = config.get('Sonarr', 'api_key')
        self.SONARR_DOWNLOAD_PATH = config.get('Sonarr', 'root_directory')
        self.SONARR_QUALITY_PROFILE_ID = int(config.get('Sonarr', 'profile_id'))


        self.OMDB_API = config.get('Services', 'omdb_api_key')

        # print(self.HASS_SERVER)
        # print(self.HASS_API)
        # print(self.HASS_TOKEN)
        # print(self.HASS_SCRIPTS_PATH)
        # print(self.HASS_SPEAKER_ENTITY)
        # print(self.HASS_TTS_SERVICE)
        #
        # print(self.SONARR_SERVER)
        # print(self.SONARR_API)
        # print(self.SONARR_DOWNLOAD_PATH)
        # print(self.SONARR_QUALITY_PROFILE_ID)
        #
        # print(self.OMDB_API)

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

        if not self.SONARR_SERVER:
            error_messages.append('Sonarr url with port (usually :8989) must be defined')

        if not self.SONARR_API:
            error_messages.append('Sonarr API Key must be defined')

        if not self.SONARR_DOWNLOAD_PATH:
            error_messages.append('Sonarr root_directory also knwon as rootFolderPath must be defined')

        if self.SONARR_QUALITY_PROFILE_ID == 0:
            error_messages.append('Sonarr quality profile id must be defined. Default value is 4 (1080p)')

        if not self.OMDB_API:
            warning_messages.append("Warning. omdb_api_key (optional)(recommended) is not set. Your speaker's feedback will miss cast details for tvshows. http://www.omdbapi.com/apikey.aspx'")

        if len(error_messages) > 0:
            print('Problem(s) in configuration file :')
            for m in error_messages:
                print(m)

        if len(warning_messages) > 0:
            for m in warning_messages:
                print(m)

        if len(error_messages) > 0:
            exit(1)


query = sys.argv[1]
mode = sys.argv[2]
monitor = sys.argv[3]

print(query)
print(mode)
print(monitor)


downloader = ShowDownloader(query, int(mode), monitor)
