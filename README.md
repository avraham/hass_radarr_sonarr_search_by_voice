# hass_radarr_search_by_voice
Add movies to radarr by voice with Home Assistant and Google Home.


# Requirements
- Home Assistant
- Radarr
- Google Home
- https://www.themoviedb.org API Key

# How to use
- Set your own values to the configuration variables
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

- Create an IFTTT applet (optional) (see folder example)
- Call script from Home Assistant (see folder example)
