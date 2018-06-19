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

# How to setup
- Set your own values to the configuration variables in hass_radarr_search_by_voice.py
```
HASS_SERVER="" # Home assistant URL eg. localhost:8123 with port
HASS_API="" # Home assistant api password
HASS_SCRIPTS_PATH="" # Home assistant scripts path eg. /users/vr/.homeassistant/scripts
HASS_GOOGLE_HOME_ENTITY="" # Home assistant google home entity_id  eg. media_player.family_room_speaker
RADARR_SERVER="" # with port
RADARR_API=""
RADARR_DOWNLOAD_PATH="" # aka rootFolderPath
RADARR_QUALITY_PROFILE_ID=4  # 1080p
TMDBID_API="" # themoviedb API Key
```

- Create an IFTTT applet for each mode (optional) (see folder example)
- Call script from Home Assistant (see folder example)

# Bonus
- Create an IFTTT applet for removing last movie added to radarr by this script in case of a mistake. (see folder example)
