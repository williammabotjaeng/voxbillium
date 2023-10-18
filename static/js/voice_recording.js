
function toggleInvoice() {
 console.log("Inside toggle invoice");
//  var element = document.getElementById("invoicemic");
//  element.style.backgroundColor = "teal";
//  element.style.borderRadius = "50%";
chunks = []

if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    // Get audio access
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(function (stream) {
        // Create MediaRecorder instance
        var recorder = new MediaRecorder(stream);
  
        console.log("Inside the recorder", recorder);
  
        // Initialize on dataavailable callback
        recorder.ondataavailable = function (e) {
          // Store recorded chunks in an array
          chunks.push(e.data);
  
          console.log("Audio Chunks", chunks);
  
          // Once recording is stopped, convert the array to a blob  
          if (recorder.state == "inactive") {
            var blob = new Blob(chunks, { 'type': 'audio/webm; codecs=opus' });
  
            console.log("Audio Blob", blob);
  
            // Store the audio blob in localStorage
            localStorage.setItem("audioRecording", URL.createObjectURL(blob));
          }
        };
  
        console.log("Recorded Value", localStorage.getItem("audioRecording"));
  
        // Start recording 
        recorder.start();
  
        // Check if recording is active
        console.log("Recording active:", recorder.state === "recording");
  
        // Stop recording after 5 seconds
        setTimeout(function () {
          recorder.stop();
          console.log("Recording active:", recorder.state === "recording");
        }, 30000);
  
      });
  }
  
}