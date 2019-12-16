# hass_radarr_search_by_voice
Add movies to radarr by voice with Home Assistant and Google Home.


# Requirements
- Home Assistant
- Radarr
- Google Home
- https://www.themoviedb.org API Key

# Features
Add movies to radarr by asking Google Home to do it.
- Mode 0 (best guess). Tell it a movie title or partial title and it will add the best guess from upcoming and recent years to radarr.
- Mode 1 (search). Tell it a movie title or partial title and it will offers up to 3 options to choose from.
- Mode 2. Tell it a number to download from previous options given by search.
- Mode 3 (search by actor/actress). Search recent movies with an specific actor/actress and it will offers up to 5 options to choose from.

# How to setup
- Set your own values to the configuration variables in hass_radarr_search_by_voice.py
```
HASS_SERVER="" # Home assistant URL eg. localhost:8123 with port
HASS_API="" # Home assistant legacy api password, leave blank if using long-lived token (used for voice feedback)
HASS_TOKEN="" # Home assistant long-lived token, leave blank if using legacy API (used for voice feedback)
HASS_SCRIPTS_PATH="" # Home assistant scripts path eg. /users/vr/.homeassistant/scripts
HASS_GOOGLE_HOME_ENTITY="" # Home assistant google home entity_id  eg. media_player.family_room_speaker
RADARR_SERVER="" # with port
RADARR_API=""
RADARR_DOWNLOAD_PATH="" # aka rootFolderPath
RADARR_QUALITY_PROFILE_ID=4  # 1080p
TMDBID_API="" # themoviedb API Key
```

# How to test from command line
Go to the path of the script, make sure the give executable permissions and run:
python3 ./hass_radarr_search_by_voice.py "star wars" "0"
It should let you know if it found and added a movie.

# Integrate with Home Assistant
1. Copy the content of the _example/homeassistant_ folder to your homeassistant folder. If you already have a custom yaml file for your own scripts and shell commands then just add the content of each files (_scripts.yaml_ and _shellcommand.yaml_) to your own files.
2. Let homeassistant know where your scripts and shell commands will be by adding the following lines to your _configuration.yaml_ (in case you are using the same file structure as me).
```script: !include scripts.yaml```
```shell_command: !include shellcommand.yaml```
3. In your _homeassistant/scripts/download.sh_.  file replace ‘/path/to/hass_radarr_search_by_voice.py’ with the actual path where you saved the python file.
4. Fill up the User defined variables in your _hass_radarr_search_by_voice.py_
5. Make sure the give executable permissions to everything inside _homeassistant/scripts_ folder and to _hass_radarr_search_by_voice.py_ file.
6. Bonus. Fill up the User defined variables in _homeassistant/scripts/remove_download.sh_

### Example folder Files overview:

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

# How to use it with IFTTT
- Create an IFTTT applet for each mode [Example provided by sinker1345](https://github.com/avraham/hass_radarr_search_by_voice/issues/3#issuecomment-552521505)
