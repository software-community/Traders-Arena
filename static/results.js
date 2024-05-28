// Celebration JS
// do this for 7.5 seconds

// function called after "Final Results" button clicked
function results() {
  document.getElementById("results").style.display = "none";
  var duration = 7.5 * 1000;
  var end_time = Date.now() + duration;
  window.end = end_time;
  frame_2();
  frame_1();
  results_div();
}

// left and right edge celebration
function frame_1() {
  // launch a few confetti from the left edge
  confetti({
    particleCount: 7,
    angle: 60,
    spread: 55,
    origin: { x: 0, y: 0.7 },
  });
  // and launch a few from the right edge
  confetti({
    particleCount: 7,
    angle: 120,
    spread: 55,
    origin: { x: 1, y: 0.7 },
  });

  // keep going until we are out of time
  if (Date.now() < end) {
    requestAnimationFrame(frame_1);
  }
}

var count = 200;
var defaults = {
  origin: { y: 0.7 },
};

function fire(particleRatio, opts) {
  confetti({
    ...defaults,
    ...opts,
    particleCount: Math.floor(count * particleRatio),
  });
}

// bottom center celebration
function frame_2() {
  fire(0.25, {
    spread: 26,
    startVelocity: 55,
  });
  fire(0.2, {
    spread: 60,
  });
  fire(0.35, {
    spread: 100,
    decay: 0.91,
    scalar: 0.8,
  });
  fire(0.1, {
    spread: 120,
    startVelocity: 25,
    decay: 0.92,
    scalar: 1.2,
  });
  fire(0.1, {
    spread: 120,
    startVelocity: 45,
  });
}

// removes the normal card display of all teams
// shows the top 3 team card div with animations
// animate.js classes added here
function results_div() {
  const cardsContainer = document.getElementById("cardsContainer");
  const resultsContainer = document.getElementById("resultsContainer");
  cardsContainer.classList.add("animate__animated", "animate__fadeOutDownBig");

  // Fade out the cards container
  // Show the result container and fade it in
  setTimeout(function () {
    cardsContainer.classList.add("hidden", "opacity-0");
    resultsContainer.classList.remove("hidden", "opacity-0");
    resultsContainer.classList.add("animate__animated", "animate__zoomInDown");
  }, 500); // Wait for the cards container to fade out

  // Disable the button after animation
  this.disabled = true;
}
