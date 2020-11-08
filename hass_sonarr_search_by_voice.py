import datetime
import requests
import json
import sys
import os
from tvdb_api_client import TVDBClient

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


SONARR_SERVER="" # with port
SONARR_API=""
SONARR_DOWNLOAD_PATH="" # aka rootFolderPath
SONARR_QUALITY_PROFILE_ID=4  # 1080p

TVDB_API="" #Need a paid subcrition on thetvdb.com it cost 11$ per year thi is the V4 api Key not legacy api key

# ------------------------------------


class ShowDownloader:



    '''
    Constrctor

    :param str show: Title of the tv show or option number if mode 2 is used
    :param int mode: 0 | 1 | 2
        mode 0 - takes the tv show string and download best guess from upcoming and recent years.
        mode 1 - search tv show string and offers 3 options to choose from.
        mode 2 - download option given from previous search.
        mode 3 - search latest tv show by Actor/Actress and offers 5 options to choose from.
    '''
    def __init__(self, show, mode=0):


        year = datetime.datetime.now().year
        term = show
        search_term = term.replace(" ", "%20")
        current_years = [year, year+1, year+2]
        for i  in range(1,49):
         current_years .append(year-i)


        if mode == 0 or mode == 1: # we are making a search by series title
            # search

            r = requests.get("http://"+SONARR_SERVER+"/api/series/lookup?term="+search_term+"&apikey="+SONARR_API)

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
                            self.tts_google("I don't been able to find the tv show.Try again with the vocal search.")

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


        elif mode == 3:  # search latest show by Actor/Actress and offers 5 options to choose from.
            actor_id = self.get_actor_id(search_term)
            if actor_id > 0:
                show = []
                show = self.get_actors_latest_show(actor_id, year)
                if len(show) > 0:
                    msg = self.save_options_found_and_compose_msg(show)
                    self.tts_google(msg)
                else:
                    self.tts_google("Your tv show was not found.")
            else:
                self.tts_google("The actor was not found.")
        else:
            # add to downloads from download_options file
            download_option = int(show)-1
            data = {}

            with open(HASS_SCRIPTS_PATH+'/download_tvshow_options.txt') as json_data:
                show = json.load(json_data)
                if download_option > -1 and len(show) >= download_option:
                    m = show[download_option]
                    if m['qualityProfileId'] == -1 and m['tvdbId'] > 0:
                        r = requests.get("http://"+SONARR_SERVER+"/api/series/lookup?term=tvdb:"+str(m['tvdbId'])+"&apikey="+SONARR_API)
                        if r.status_code == requests.codes.ok:
                            media_list = r.json()
                            # print(media_list)
                            # if len(media_list) > 0:
                            data = self.prepare_show_json(media_list)
                    else:
                        data = self.prepare_show_json(m)
                    self.add_show(data)
                else:
                    self.tts_google("There is no options.")


    def prepare_show_json(self, media):
        data = {}
        data['title'] = media['title']
        data['qualityProfileId'] = SONARR_QUALITY_PROFILE_ID
        data['titleSlug'] = media['titleSlug']
        data['images'] = media['images']
        data['tvdbId'] = media['tvdbId']
        data['rootFolderPath'] = SONARR_DOWNLOAD_PATH
        data['monitored'] = True
        data['minimumAvailability'] = 'released'
        data['year'] = media['year']
        data['cast'] = self.get_cast(data['tvdbId'])

        return data

    def prepare_barebone_show_json(self, tvdbId, title):
        data = {}
        data['title'] = title
        data['qualityProfileId'] = -1
        data['titleSlug'] = 0
        data['images'] = 0
        data['tvdbId'] = tvdbId
        data['rootFolderPath'] = 0
        data['monitored'] = 0
        data['minimumAvailability'] = 0
        data['year'] = 0
        data['cast'] = ""

        return data

    def add_show(self, data):
        r = requests.post("http://"+SONARR_SERVER+"/api/series?apikey="+SONARR_API,json.dumps(data))

        if r.status_code == 201:
            self.tts_google("I have added your tv show "+str(data['title'])+" started, "+str(data['year'])+" with the actor, "+str(data['cast'])+" to your download list.")
            show = r.json()
            with open(HASS_SCRIPTS_PATH+"/last_tvshow_download_added.txt", "w") as myfile:
                myfile.write("show:"+str(SeriesName['id'])+"\n")
        else:
            res = self.is_show_already_added(data)
            if res >= 0:
                if res == 0:
                    self.tts_google("I found your tv show but i was not able to add it to your download list.")
                else:
                    self.tts_google("The tv show, "+str(data['title'])+" starting on, "+str(data['year'])+" with the actors, "+str(data['cast'])+" is allready in your list.")
            else:
                self.tts_google("Something wrong occured when trying to add the tv show to your download list.")

    def is_show_already_added(self, data):
        # print("http://"+SONARR_SERVER+"/api/movie?apikey="+SONARR_API)
        r = requests.get("http://"+SONARR_SERVER+"/api/series?apikey="+SONARR_API)

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

    def get_cast(self, tvdbId):
        r = requests.get("https://api.thetvdb.com/series/"+str(tvdbId)+"/actors")
        if r.status_code == requests.codes.ok:
            series = r.json()
            data = series['data']
            if len(data) > 1:
                return(data[0]['name']+" et "+data[1]['name'])
            else:
                return(data[0]['name'])
        else:
            return("")

    def get_actor_id(self, actor_name):
        r = requests.get("https://api.thetvdb.com/3/search/person?language=en-US&page=1&include_adult=false&api_key="+TVDB_API+"&query="+actor_name)
        if r.status_code == requests.codes.ok:
            results = r.json()
            if int(results['total_results']) > 0:
                return(int(results['results'][0]['id']))
            else:
                return(-1)
        else:
            return(-1)

    def get_actors_latest_show(self, actor_id, year):
        latest_years = [ year+1, year, year-1, year-2]
        i = 0
        shows = []
        while i < len(latest_years) and len(show) < 5:
            r = requests.get("https://api.thetvdb.com/3/discover/series?language=en-US&page=1&sort_by=release_date.desc&include_adult=false&include_video=false&page=1&primary_release_year=&api_key="+TVDB_API+"&primary_release_year="+str(latest_years[i])+"&with_cast="+str(actor_id))
            if r.status_code == requests.codes.ok:
                results = r.json()
                if int(results['total_results']) > 0:
                    for show in results['results']:
                        if len(show) < 5:
                            data = self.prepare_barebone_show_json(int(show["id"]), show["title"])
                            show.append(data)
            i += 1
        return(show)

    def save_options_found_and_compose_msg(self, show):
        msg=""

        with open(HASS_SCRIPTS_PATH+"/download_tvshow_options.txt", "w") as myfile:
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
        data = {"entity_id": HASS_GOOGLE_HOME_ENTITY, "message": msg}

        if HASS_API == "" and HASS_TOKEN != "":
            headers = {
                'Authorization': 'Bearer '+HASS_TOKEN
            }
            r = requests.post("http://"+HASS_SERVER+"/api/services/tts/google_translate_say",json.dumps(data), headers=headers)

        else:
            r = requests.post("http://"+HASS_SERVER+"/api/services/tts/google_translate_say?api_password="+HASS_API,json.dumps(data))


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

downloader = ShowDownloader(query, int(mode))
