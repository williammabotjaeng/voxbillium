document.addEventListener("DOMContentLoaded", function() {
    // Step 1: Create a Contact
    const formArea = document.querySelector(".column.tile.blue");
    const form = formArea.querySelector(".form");
  
    const tour = introJs();
    tour.setOptions({
      steps: [
        {
          element: form,
          intro: "Welcome to the guided tour! This is the form area where you can create a new contact.",
          position: "top",
        },
        {
          element: ".column.tile.purple",
          intro: "Here you can see all your contacts. Each contact's first name and status are displayed.",
          position: "top",
        },
        {
          element: ".column.tile.teal",
          intro: "In this section, you can find your trusted contacts.",
          position: "top",
        },
        {
          element: ".column.tile.deep-orange",
          intro: "Here you can find your untrusted contacts.",
          position: "top",
        },
      ],
    });
  
    // Start the guided tour when the button is clicked
    const startTourButton = document.querySelector("#startTourButton");
    startTourButton.addEventListener("click", function() {
      tour.start();
    });
  
    // Move to the next step when the current step is completed
    tour.oncomplete(function() {
      const currentStep = tour._currentStep;
      if (currentStep < tour._options.steps.length - 1) {
        tour.goToStep(currentStep + 1);
      }
    });
  });
  