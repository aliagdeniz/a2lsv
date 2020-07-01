AudioFiles = [];
var AudioIndex = 0;
SpeakerId = 0;
TotalSpeakerCount = 0
labelList = [];

$(document).ready(function() {

        var playlist = document.getElementById('playlist');
    	playlist.querySelectorAll('p').forEach(function (audio) {
    		AudioFiles.push({
        		'link': audio.getAttribute('link'),
        		'value': audio.textContent
    		});
   	        labelList.push(audio.getAttribute('preLabel'));
   	        audio.onclick = "";
    	})
    	
    	TotalSpeakerCount = document.querySelectorAll("#speakerButton").length;

        var counter = 0;
        document.querySelectorAll('.audio').forEach(el => {
            el.setAttribute('data-index', counter);
            counter += 1;
            el.addEventListener("click", function() {
        		AudioIndex = el.dataset.index;
                loadFile(el.dataset.index);
            }
        )});


        WaveSurfer
        wavesurfer = WaveSurfer.create({
            container: '#waveform',
            waveColor: 'red',
            progressColor: 'purple',
            height: '130',
            barWidth: '1',
            backend: 'MediaElement'
        })
        


        //To get waveform working, you need to download following extention
        //https://chrome.google.com/webstore/detail/allow-control-allow-origi/nlfbmbojpeacfghkpbjhddihlkkiljbi/related?hl=en-US
    	loadFile(AudioIndex)
//        wavesurfer.load('http://127.0.0.1:8887/' + AudioFiles[AudioIndex].value);
//        document.getElementById("AudioName").innerHTML = AudioFiles[AudioIndex];


        wavesurfer.on('ready', function() {
            var timeline = Object.create(WaveSurfer.Timeline);

            timeline.init({
                wavesurfer: wavesurfer,
                container: '#waveform-timeline'
            });
        });

    
        var slider = document.querySelector('#slider');
        
});

function post(path, parameters) {
    var form = $('form');

    form.attr("method", "post");
    form.attr("action", path);

    $.each(parameters, function(key, value) {
        var field = $('<input></input>');

        field.attr("type", "hidden");
        field.attr("name", key);
        field.attr("value", value);

        form.append(field);
    });

    // The form needs to be a part of the document in
    // order for us to be able to submit it.
    $(document.body).append(form);
    form.submit();
}

function confirm() {
    var videoId = document.querySelector('#videoId').getAttribute('value')
    var dbName = document.querySelector('#dbName').getAttribute('value')
    var url = 'labelAudio'
    var labelListJson = {}
    for (var i = 0; i < labelList.length; i++) {
    	let id = AudioFiles[i].value.split(".")[0]
    	labelListJson[id] = labelList[i]
    }
    post(url, {
        videoId: videoId,
        dbName: dbName,
        labelList: JSON.stringify(labelListJson)
        });
}



function loadFile(index){
    wavesurfer.clearRegions();
//    wavesurfer.load('http://127.0.0.1:8887/' + AudioFiles[index]);
    wavesurfer.load(AudioFiles[index].link);
    document.getElementById("AudioName").innerHTML = AudioFiles[index].value;
    AudioIndex = index;
    document.getElementById("status").innerHTML = AudioFiles[AudioIndex].value+" labeled as Speaker #"+ labelList[AudioIndex];
}

function addSpeaker(){
	TotalSpeakerCount += 1;

	var x = document.createElement('button');
	x.classList.add("btn");
	x.classList.add("btn-info");
	x.classList.add("btn-md");
	x.style = "margin:5px;width:100px;height:35px;"
	x.setAttribute('onclick', "labelSpeaker("+TotalSpeakerCount+")" );
	x.textContent = "Speaker #"+TotalSpeakerCount
	
	var buttontag = document.getElementById('buttons')
	buttontag.appendChild(x)

}

function addEvent (obj, type, fn) {
  if (obj.addEventListener) {

    obj.addEventListener(type, fn, false);

  } else if (obj.attachEvent) {

    obj.attachEvent('on' + type, function () {

      return fn.call(obj, window.event);

    });
  }
}

//Speaker Starts
function labelSpeaker(Id) {

    //Creates new label object 
    label = new Object();
    if (Id == -1)
        document.getElementById("status").innerHTML = AudioFiles[AudioIndex].value+" will be deleted!";
    else
        document.getElementById("status").innerHTML = AudioFiles[AudioIndex].value+" labeled as Speaker #"+ Id;

    labelList[AudioIndex] = String(Id);

}

function clearLabels() {
    wavesurfer.clearRegions();
 
    labelList = [];
    var playlist = document.getElementById('playlist');
    playlist.querySelectorAll('p').forEach(function (audio) {
        labelList.push(audio.getAttribute('preLabel'));
    })
}


function setSpeed_1_5x() {
    wavesurfer.backend.setPlaybackRate(1.5);
    document.getElementById("status").innerHTML = "Set playback speed to 1.5x!";
}

function setSpeed_2x() {
    wavesurfer.backend.setPlaybackRate(2);
    document.getElementById("status").innerHTML = "Set playback speed to 2x!";
}

function loadNextFile(){
	if (AudioIndex+1 < AudioFiles.length){
		loadFile(AudioIndex+1)
		wavesurfer.playPause();
		console.log(AudioIndex)
	}
}

function loadPrevFile(){
	if (AudioIndex-1 >= 0 && AudioIndex-1 < AudioFiles.length){
		loadFile(AudioIndex-1)
		wavesurfer.playPause();
		console.log(AudioIndex)
	}
}

function setSpeed_3x() {
    wavesurfer.backend.setPlaybackRate(3);
    document.getElementById("status").innerHTML = "Set playback speed to 3x!";
}

function setSpeed_1x() {
    wavesurfer.backend.setPlaybackRate(1);
    document.getElementById("status").innerHTML = "Set playback speed to 1x!";
}

// Control keyboard shortcuts
window.addEventListener("keydown", function(e){

// Ctrl + Space
if (e.keyCode==32 && e.ctrlKey){
    wavesurfer.playPause();
}
// 1,2, .. , 9 speakers
else if (e.keyCode>=49 && e.keyCode<=57 && e.keyCode-48 <= TotalSpeakerCount){
    labelSpeaker(e.keyCode-48);
}
// delete
else if (e.keyCode==46){
    labelSpeaker(-1);
}
// Right Arrow
else if (e.keyCode==39){
    if (e.keyCode==39 && e.ctrlKey){
        wavesurfer.skipForward(5);
    }
    else if (e.keyCode==39 && e.shiftKey){
        wavesurfer.skipForward(0.3);
    }
    else{
	loadNextFile();
    }
}
// Left Arrow
else if (e.keyCode==37){
    if (e.keyCode==37 && e.ctrlKey){
        wavesurfer.skipBackward(5);
    }
    else if (e.keyCode==37 && e.shiftKey){
        wavesurfer.skipBackward(0.3);
    }
    else{
	loadPrevFile();
    }
}
// "a"
else if (e.keyCode==65){
	addSpeaker()
}
// 's'
else if (e.keyCode==83){
    if (e.keyCode==83 && e.shiftKey && e.ctrlKey){
        confirm();
    }
}
// Ctrl + "up arrow"
else if (e.keyCode==38 && e.ctrlKey){
    setSpeed_2x()
}

// Ctrl + "down arrow"
else if (e.keyCode==40 && e.ctrlKey){
    setSpeed_1x()
}
});
