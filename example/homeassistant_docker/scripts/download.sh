#!/bin/bash

movie="$1"
mode="$2"

response=$(python3 /config/hass_radarr_search_by_voice.py "$movie" "$mode")
