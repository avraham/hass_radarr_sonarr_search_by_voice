#!/bin/bash

# Home assistant scripts path eg. /users/vr/.homeassistant/scripts
HASS_SCRIPTS_PATH=""
RADARR_SERVER="" # with port
RADARR_API=""


while read -r line; do
  IFS=':'
  MAP_ARRAY=($(echo "$line"))
  TYPE=${MAP_ARRAY[0]}
  ID=${MAP_ARRAY[1]}


  # delete from radarr database
  if [ "$TYPE" == "movie" ]; then
    if [ "$ID" != "null" ]; then
      curl -d '{deleteFiles: true}' -H "Content-Type: application/json" -X DELETE http://"$RADARR_SERVER"/api/movie/"$ID"?apikey="$RADARR_API"
    fi
  fi


done < "$HASS_SCRIPTS_PATH/last_download_added.txt"
