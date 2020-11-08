# hass_radarr_search_by_voice
Add movies to radarr by voice with Home Assistant and Google Home.


# Requirements
- Home Assistant
- Radarr
- Google Home
- https://www.themoviedb.org API Key
- IFTTT Account

# Features
Add movies to radarr by asking Google Home to do it.

- Mode 0 (best guess). Tell it a movie title or partial title and it will add the best guess from upcoming and recent years to radarr.

- Mode 1 (search). Tell it a movie title or partial title and it will offers up to 3 options to choose from.

- Mode 2. Tell it a number to download from previous options given by search.

- Mode 3 (search by actor/actress). Search recent movies with an specific actor/actress and it will offers up to 5 options to choose from.

## Install Home Assistant (Home Assistant Supervised ) using Docker.
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

#### Supported Machine types

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

#### Git Clone this script
install git

```
apt-get install -y git
```

Now it's time to clone the repo to you folder 

```
git clone THIS_REPOSITORY 
```

go to your cloned folder 

```
cd hass_radarr_search_by_voice
```

copy `hass_radarr_search_by_voice.py` and `hass_radarr_search_by_voice/example/homeassistant_docker/` to the `/usr/share/hassio/homeassistant/`

!! WARNING: if you have allready a `configuration.yaml` please backup it First because the the next step will replace it / after that you need to import your configs manually (Copy and paste with nano/vim or any text editor) from your backup file, (configuration.yaml) to the new once have been copied. IF YOUR INSTALLATION IS A FRESH INSTALL JUST IGNORE THIS WARNING !

```
cp hass_radarr_search_by_voice.py /usr/share/hassio/homeassistant/
cd /example/homeassistant_docker/
cp -r * /usr/share/hassio/homeassistant/
```

* Note the destination path is only for the Home Assistant Supervised docker installation (Method Above using docker).* 


# A) How to setup
- Set your own values to the configuration variables in `hass_radarr_search_by_voice.py` and on your `hass_sonarr_search_by_voice.py`

```
HASS_SERVER="" # Home assistant URL eg. localhost:8123 with port
HASS_API="" # Home assistant legacy api password, leave blank if using long-lived token (used for voice feedback)
HASS_TOKEN="" # Home assistant long-lived token, leave blank if using legacy API (used for voice feedback)
HASS_SCRIPTS_PATH="" # Home assistant scripts path eg. /users/vr/.homeassistant/scripts or for container (e.g HA SUPERVISED) /config/scripts
HASS_GOOGLE_HOME_ENTITY="" # Home assistant google home entity_id  eg. media_player.family_room_speaker
RADARR_SERVER="" # with port usually :7878
RADARR_API="" # api of radarr
RADARR_DOWNLOAD_PATH="" # aka rootFolderPath
RADARR_QUALITY_PROFILE_ID=4  # 1080p
TMDBID_API="" # themoviedb API Key
```
*Note to get HASS_TOKEN go to your home assistant (http://ip_of_server:8123/) then go to Your Profile (last option on the button at the left tab) then go to  Long-Lived Access Tokens at the end of the page.*

*Note to get the HASS_GOOGLE_HOME_ENTITY go to your home assistant (http://ip_of_server:8123/) then go to Your Configuration tab -> Entities , there is all entity ID of the devices in your home.*

# B) How to test from command line
Go to the path of the script, make sure the give executable permissions and run:
```python3 ./hass_radarr_search_by_voice.py "Artemis Fowl" "0"```

It should let you know if it found and added a movie (The Google Home Speaker, should speak back).

# C) Integrate with Home Assistant
1º Copy the content of the _example/homeassistant_ folder to your homeassistant folder. If you already have a custom yaml file for your own scripts and shell commands then just add the content of each files (_scripts.yaml_ and _shellcommand.yaml_) to your own files.

2º Let homeassistant know where your scripts and shell commands will be by adding the following lines to your _configuration.yaml_ (in case you are using the same file structure as me).

```
script: !include scripts.yaml
shell_command: !include shellcommand.yaml
```

* Note DON'T needed if you are using the files from `/hass_radarr_search_by_voice/homeassistant_docker/`

3º In your _homeassistant/scripts/download.sh_.  file replace ‘/path/to/hass_radarr_search_by_voice.py’ with the actual path where you saved the python file.
  *IMPORTANT NOTE: If you follow the installation method you don't need to edit the path because it point to `/usr/share/hassio/homeassistant/hass_radarr_search_by_voice.py`*
  
4º Fill up the User defined variables in your _hass_radarr_search_by_voice.py_

5º Make sure the give executable permissions to everything inside _homeassistant/scripts_ folder and to _hass_radarr_search_by_voice.py_ file.

6º Bonus. Fill up the User defined variables in _homeassistant/scripts/remove_download.sh_

# D) Use it by voice with Google Assistant and IFTTT
 0º - Setup IFTTT integration on Home Assistant. Go to Configuration > integrations > IFTTT. It will give you a private IFTTT_WEEBHOOK_ID, save it somewhere this is important.
 
 1º - Go to https://ifttt.com
 
 2º - create a new applet
 
 3º - click on (if this) -> Google Assistant -> Say a phrase with a text ingredient
 
 4º - What do you want to say? Enter: Download the movie $
   
   *Note the $(Dollar symbol ) is very important.THIS IS A EXEMPLE OF WHAT YOU MAY SAY TO DOWNLOAD THE MOVIE $*

5º - What do you want the Assistant to say in response? Enter: Searching the movie $
     
   *Note the $(Dollar symbol ) is very important.THIS IS A EXEMPLE OF WHAT AFTER YOUR REQUEST $*
 
 6º - Save!!
 
 7º - Click on (Then That) --> webhoock

8º - Enter the following:
    
    URL: the url you copied before at 0.D)
    Method: Post
    Content Type: application/json
    body: { "action": "call_service", "service": "script.download_movie", "data": "<<<{{TextField}}>>>"} 
    
    *IMPOTANT NOTE the text ("TextField" should be surrounded by grey spaces) , 
    
   !IF YOU USE THE INSTALLATION METHOD ABOVE USE THE FOLLOWING!
   
    URL: the url you copied before at 0.D)
    Method: Post
    Content Type: application/json
    body: { "action": "call_service", "service": "script.download_movie", "movie": "<<<{{TextField}}>>>"} 
 
 9º - Save!!

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


