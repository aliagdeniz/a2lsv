var wavesurfersDict = {}
var videoIds = []
$(document).ready(function() {

        document.querySelectorAll('p#videoId').forEach(el => {
            videoIds.push(el.getAttribute('value'))
        });
        document.querySelectorAll('.audio').forEach(audioEl => {
            audioEl.addEventListener("click", function() {
                loadFile(audioEl.getAttribute('link'), audioEl.textContent, audioEl.getAttribute('videoid'));
            }
        )});
        
        videoIds.forEach(function(videoId){
            document.querySelectorAll('#waveform'+videoId).forEach(el => {
                WaveSurfer
                wavesurfersDict[videoId] = WaveSurfer.create({
                    container: '#waveform'+videoId,
                    waveColor: 'red',
                    progressColor: 'purple',
                    height: '130',
                    barWidth: '1',
                    backend: 'MediaElement'
                })
                wavesurfersDict[videoId].on('ready', function() {
                    var timeline = Object.create(WaveSurfer.Timeline);
        
                    timeline.init({
                        wavesurfer: wavesurfersDict[videoId],
                        container: '#waveform-timeline'+videoId,
                    });
                });

                let playlist = document.querySelector(".playlist"+videoId)
                let audioEl = playlist.querySelector('.audio')
                loadFile(audioEl.getAttribute('link'), audioEl.textContent, audioEl.getAttribute('videoid'));
            });
        });

});

function loadFile(link, name, videoId){
    wavesurfersDict[videoId].clearRegions();
    wavesurfersDict[videoId].load(link);
}

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

function confirm(isSameSpeaker) {
    let postData = document.querySelector('p#postData').getAttribute('value')
    var url = 'solveSpeakerDuplicate'
    post(url, {
        postData: postData,
        isSameSpeaker: isSameSpeaker
        });
}

