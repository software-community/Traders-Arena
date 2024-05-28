let form = document.getElementById("form");
let content = document.getElementById("content");
let title = document.getElementById("title");
let img = document.getElementById("image");
let round = document.getElementById("round");
let newDiv = document.getElementById("Event");
let EventDelete = document.getElementsByClassName("EventDelete");

document
  .getElementById("form")
  .addEventListener("submit", async function (event) {
    event.preventDefault(); // preventing the default form behavior.
    let newEvent = document.createElement("div");
    let ImageDiv = document.createElement("div");
    let EventDetailDiv = document.createElement("div");
    let newRound = document.createElement("p");
    let newTitle = document.createElement("h3");
    let newContent = document.createElement("p");
    let deleteButton = document.createElement("button");
    let EventFooter = document.createElement("div");

    newRound.innerText = "Round No: " + round.value;
    newTitle.innerText = title.value;
    newContent.innerText = content.value;
    deleteButton.textContent = "Delete Event";
    deleteButton.setAttribute("class", "btn btn-outline-dark mb-4");

    newEvent.appendChild(ImageDiv);
    newEvent.appendChild(EventDetailDiv);

    EventDetailDiv.appendChild(newTitle);
    EventDetailDiv.appendChild(newContent);
    EventDetailDiv.append(EventFooter);

    EventFooter.appendChild(newRound);
    EventFooter.appendChild(deleteButton);

    newEvent.classList.add("EventStyle");
    newContent.classList.add("EventContentStyle");
    newTitle.classList.add("EventHeading");
    newRound.classList.add("EventRound");
    deleteButton.classList.add("EventDelete");
    ImageDiv.classList.add("imageDiv");
    EventDetailDiv.classList.add("EventDetailDiv");
    EventFooter.classList.add("eventFooter");

    EventDetailDiv.classList.add();

    var file = document.getElementById("image").files[0];
    if (file) {
      var reader = new FileReader();
      reader.onload = function (e) {
        var image = new Image();
        image.src = e.target.result;
        image.classList.add("EventImage"); // Optional: Add a CSS class for styling

        // newTitle.append(image);
        ImageDiv.append(image);
      };
      reader.readAsDataURL(file);
    }

    newDiv.appendChild(newEvent); // Append newEvent to newDiv

    form.reset();
  });

newDiv.addEventListener("click", function (event) {
  if (event.target && event.target.classList.contains("EventDelete")) {
    let eventToDelete = event.target.parentElement.parentElement.parentElement;
    console.log(eventToDelete);
    newDiv.removeChild(eventToDelete);
  }
});
