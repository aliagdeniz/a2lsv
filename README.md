# A2LSV - Automatic Audio Labeler for Speaker Verification

This project will make it very easy to create speaker verification datasets for all languages. Audios will be  automatically downloaded with 'youtube-dl'. Speakers in the audio will be pre-labeled automatically with [GE2E encoder](https://github.com/CorentinJ/Real-Time-Voice-Cloning). Labeling can be done very efficently with keyboard shortcuts.
For web interface, benefitted from [this project](https://github.com/defianceblack/django-multiple-user-types-example).
For labelling interface, benefitted from [this project](https://github.com/KrishnaKarunaharan/AudioLabeller).

![Labeling Screenshot](https://github.com/aliagdeniz/a2lsv/blob/master/images/labeling.png)

## Shortcuts
| Shortcut  | Description  |
|---|---|
| CTRL + Space  | Play/Pause current audio.  |
| Right Arrow  |  Load next audio. |
| Left Arrow  | Load previous audio.  |
| CTRL + Right Arrow | Forward audio |
| CTRL + Left Arrow | Backward audio. |
| CTRL + Up Arrow| Set speed to 2x. |	
| CTRL + Down Arrow | Set speed to 1x. |	
| a | Add new speaker. |	
| 1, 2, 3, 4, .. , 9 | Label speaker as according to input number. |	
| Delete | Delete this audio. |	

## Setup
Need to install and configure apache kafka and mongoDB.
To install apache kafka, you can follow [this blog post](https://www.digitalocean.com/community/tutorials/how-to-install-apache-kafka-on-ubuntu-18-04).
To install mongoDB server, you can follow [offical documentation](https://docs.mongodb.com/manual/installation/).

## configs.json
Need to get a valid GCP API developer key. Default values for kafka port and mongoDb address are below. Change them if you need.
```
{
	"kafkaPort": 9092,
	"mongoDbAddress" : "127.0.0.1:27017",
	"googleAPIDeveloperKey" : "your_developer_key_here"	
}
```

## Installing ffmpeg
```
sudo apt install ffmpeg
```

## Creating environment
```
pip install pipenv
pipenv --python 3.6
```

## Activating environment
```
pipenv shell
```

## Installing python packages
```
pip install -r requirements.txt
```

## Making migrations
```
cd a2lsv_web
python manage.py makemigrations web_interface
python manage.py migrate
```
## Loading some language records
```
python manage.py loaddata fixtures.json
```

## Running server
```
python manage.py runserver
```

## Starting Kafka Consumers and Producers
Open new terminal window and activate environment for every script.
### youtubeSearch
```
python youtubeSearch.py
```
### youtubeAudioDownloader
```
python youtubeAudioDownloader.py
```
### speakerDiarization
```
python speakerDiarization.py
```

## Accessing final dataset files
You can find final dataset files in “a2lsv_web/static/datasets/(dataset_name)/final_dataset” directory. Folder hierarchy is like speaker id => youtube video id => audio file.

## Documents
You can download [Installation Guide](https://github.com/aliagdeniz/a2lsv/raw/master/docs/Installation%20Guide.pdf), [Software Design Document](https://github.com/aliagdeniz/a2lsv/raw/master/docs/Software%20Design%20Document.pdf) and  [User Guide](https://github.com/aliagdeniz/a2lsv/raw/master/docs/User%20Guide.pdf).
