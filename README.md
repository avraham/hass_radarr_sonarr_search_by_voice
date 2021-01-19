# hass_radarr_sonarr_search_by_voice
Add movies and tv shows to radarr and sonarr by voice with Home Assistant and a smart speaker (Google Home, Echo) and receive voice feedback.


# Requirements
- Home Assistant
- Radarr
- Sonarr
- Smart speaker (Google Home, Echo, etc)
- IFTTT Account
- https://www.themoviedb.org API Key (Optional) (Free)
- http://www.omdbapi.com/ API Key (Optional) (Free)

# Features
Add movies to radarr and tv shows to sonarr by asking your smart speaker to do it. You can set it up only for radarr, only for sonarr or both.

This script has several use cases that can be called with a different phrase depending your setup:

- **Add best guess (mode 0)**. This is the most common use. Tell a movie/series title or partial title and it will add the best guess from upcoming  movie/series and last 50 years to radarr/sonarr.

- **Full search (mode 1)**. If the best guess feature doesn't find the correct movie/series you can do a full search. Tell a movie/series title or partial title and it will offers up to 3 enumerated options to choose from.

- **Add option from previous search (mode 2)**. Tell it a number to download from previous enumerated options given by search.

- **Search by actor/actress (Mode 3)**. Movies Only. Search recent movies with an specific actor/actress and it will offers up to 5 options to choose from.

## Install Home Assistant (Home Assistant Supervised ) using Docker. (Skip if you already have Home Assistant)
  1º - Download the installer.sh from HA(Home Assistant) repository.
      Command:
```
curl -Lo installer.sh https://raw.githubusercontent.com/home-assistant/supervised-installer/master/installer.sh
```

   2º - Than execute (You need to change the MACHINE_TYPE with the correct machine type listed bellow)
      Command:
```
bash installer.sh --machine MACHINE_TYPE
```

##### Supported Machine types

- intel-nuc
- odroid-c2
- odroid-n2
- odroid-xu
- qemuarm
- qemuarm-64
- qemux86
- qemux86-64
- raspberrypi
- raspberrypi2
- raspberrypi3
- raspberrypi4
- raspberrypi3-64
- raspberrypi4-64
- tinker

After sometime you should be able to go to http://ip_of_server:8123/ it can take some time on the first start, so be pacient.

## Git Clone this script
install git

```
apt-get install -y git
```

Now it's time to clone the repo to you folder

```
git clone THIS_REPOSITORY
```


# A) How to setup
- Set your own values in the configuration file `ha_radarr_sonarr.conf` without quotes.
If you are not using Radarr just leave that part blank. The same goes for Sonarr. it should work even if radarr and
sonarr are on a different host.

HomeAssistant
- **server_url**. Home assistant URL eg. http://localhost:8123 with protocol (http or https) and port
- **api_key**. Home assistant legacy api password, leave blank if using long-lived token (used for voice feedback)
- **token**. Home assistant long-lived token, leave blank if using legacy API (used for voice feedback)
- **scripts_path**. Home assistant scripts path eg. /users/vr/.homeassistant/scripts or for container (e.g HA SUPERVISED) /config/scripts
- **speaker_entity**. Home assistant smart speaker entity_id  eg. media_player.family_room_speaker
- **tts_service**. Your Home assistant text-to-speech service. eg. google_say

Radarr
- **server_url**. Radarr url with protocol (http or https) and port (usually :7878)
- **api_key**. Radarr API Key
- **root_directory**. Radarr root_directory also knwon as rootFolderPath. If you are using docker, the root_directory is the virtual path your radarr
app has access to. It's the same path it shows on the UI when you add a movie manually.
- **profile_id**. Radarr quality profile id. eg. 4 is 1080p

Sonarr
- **server_url**. Sonarr url with protocol (http or https) and port (usually :8989)
- **api_key**. Sonarr API Key
- **root_directory**. Sonarr root_directory also knwon as rootFolderPath
- **profile_id**. Sonarr quality profile id

Services
- **omdb_api_key**. (Optional) (recommended for Sonarr). Used for cast details feedback for tvshows added. http://www.omdbapi.com/apikey.aspx
- **tmdmid_api_key_v3**. (Optional) (recommended for Radarr). Used for cast details feedback for movies added and search movies by actor or actress function. https://www.themoviedb.org/settings/api v3 auth

*Note to get your HomeAssistant token go to your home assistant (http://ip_of_server:8123/) then go to Your Profile (last option on the button at the left tab) then go to  Long-Lived Access Tokens at the end of the page.*

*Note to get the HomeAssistant speaker_entity go to your home assistant (http://ip_of_server:8123/) then go to Your Configuration tab -> Entities , there is all entity ID of the devices in your home.*

# B) How to test from command line
For movies go to the path of the script, make sure the give executable permissions and run:
```python3 ./hass_radarr_search_by_voice.py "Artemis Fowl" "0"```

Note. First parameter is the movie title, second parameter is the _mode_: best guess, full search, search by actor.

For series go to the path of the script, make sure the give executable permissions and run:
```python3 ./hass_sonarr_search_by_voice.py "The Mandalorian" "0" "future"```

Note. First parameter is the movie title, second parameter is the _mode_: best guess, full search; the third parameter is _what should be monitored_: `future` monitors episodes that have not aired yet and `missing` monitors all missing episodes that do not have files or have not aired yet.

It should let you know if it found and added a movie/tv shows (The Google Home Speaker or Echo, should speak back).

# C) Integrate with Home Assistant

##### 1) Hassio only.
1º Copy the content of the _example/homeassistant_docker_.
go to your cloned folder and copy the files to the Home Assistant folder.

```
cd hass_radarr_sonarr_search_by_voice
```

copy `hass_radarr_search_by_voice.py`, `hass_sonarr_search_by_voice.py`, `ha_radarr_sonarr.conf` and `hass_radarr_search_by_voice/example/homeassistant_docker/` to the `/usr/share/hassio/homeassistant/`

!! WARNING: if you have allready a `configuration.yaml` please backup it First because the the next step will replace it / after that you need to import your configs manually (Copy and paste with nano/vim or any text editor) from your backup file, (configuration.yaml) to the new once have been copied. IF YOUR INSTALLATION IS A FRESH INSTALL JUST IGNORE THIS WARNING !

```
cp hass_radarr_search_by_voice.py hass_sonarr_search_by_voice.py ha_radarr_sonarr.conf /usr/share/hassio/homeassistant/
cd /example/homeassistant_docker/
cp -r * /usr/share/hassio/homeassistant/
```

* Note the destination path is only for the Home Assistant Supervised docker installation (Method Above using docker).*

#####  1) Non Hassio only.
1º Copy the content of the _example/homeassistant_ folder to your homeassistant folder. If you already have a custom yaml file for your own scripts and shell commands then just add the content of each files (_scripts.yaml_ and _shellcommand.yaml_) to your own files. Also copy the examples automations in _automations.yaml_.

2º Let homeassistant know where your scripts and shell commands will be by adding the following lines to your _configuration.yaml_ (in case you are using the same file structure as me).

```
script: !include scripts.yaml
shell_command: !include shellcommand.yaml
```

3º In your _homeassistant/scripts/download.sh_ and _homeassistant/scripts/download_tvshow.sh_ files replace ‘/path/to/hass_radarr_search_by_voice.py’ and ‘/path/to/hass_sonarr_search_by_voice.py’ respectively with the actual path where you saved the python file.
  *IMPORTANT NOTE: If you are using Hassio and followed the installation method you don't need to edit the path because it point to `/usr/share/hassio/homeassistant/hass_radarr_search_by_voice.py`*


#####  2) Hassio and Non Hassio.

4º Fill up the User defined variables in Configuration file `ha_radarr_sonarr.conf` if you haven't done it.

5º Make sure the give executable permissions to _hass_radarr_search_by_voice.py_ & _hass_sonarr_search_by_voice.py_ file.

6º Bonus (optional). Fill up the User defined variables in _homeassistant/scripts/remove_download.sh_

# D) Use it by voice with your smart speaker and IFTTT
 0º - Setup IFTTT integration on Home Assistant. Go to Configuration > integrations > IFTTT. It will give you a private IFTTT_WEEBHOOK_ID, save it somewhere this is important.

 1º - Go to https://ifttt.com

 2º - create a new applet. (One applet for movies and another for tv shows)

 3º - click on (if this) -> Google Assistant -> Say a phrase with a text ingredient (or whatever smart speaker)

 4º - What do you want to say? Enter: Download the movie $

   *Note the $(Dollar symbol ) is very important.THIS IS A EXAMPLE OF WHAT YOU MAY SAY TO DOWNLOAD THE MOVIE $*

5º - What do you want the Assistant to say in response? Enter: Searching the movie $

   *Note the $(Dollar symbol ) is very important.THIS IS A EXAMPLE OF WHAT AFTER YOUR REQUEST $*

 6º - Save!!

 7º - Click on (Then That) --> webhook

8º - Enter the following:

    URL: the url you copied before at 0.D)
    Method: Post
    Content Type: application/json
    body: { "action": "call_service", "service": "script.download_movie", "movie": "<<<{{TextField}}>>>"}

  8.1º - For for sonarr (TVshows)

    URL: the url you copied before at 0.D)
    Method: Post
    Content Type: application/json
    body: { "action": "call_service", "service": "script.download_tvshow", "tvshow": " <<<{{TextField}}>>>"}

 9º - Save and test with your smart speaker!!




### Example folder Files overview (Additional Information):

**homeassistant folder**.
This is your homeassistant folder where the configuration yaml files are.

**homeassistant/scripts.yaml**.  
A separate configuration file for your own scripts  instead of including everything in _configuration.yaml_. It’s required to add the line `script: !include scripts.yaml` in the _configuration.yaml_ file to let know homeassistant about the separation.

**homeassistant/shellcommand.yaml**.  
A separate configuration file for your own Shell commands  instead of including everything in _configuration.yaml_. It’s required to add the line `shell_command: !include shellcommand.yaml` in the _configuration.yaml_ file to let know homeassistant about the separation.

**homeassistant/scripts/download.sh**.  
Shell script for homeassistant that will call the python script.

**homeassistant/scripts/remove_download.sh**
Bonus shell script for removing the last movie added to radarr by this script.

Thank you to CyberPoison for the sonarr script and better guide.
