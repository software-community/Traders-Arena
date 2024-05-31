const myslide = document.querySelectorAll('.myslide'),
      dot = document.querySelectorAll('.dot');
let counter = 1;
let isPaused = false;
slidefun(counter);

console.log(myslide.length);

var timer = setInterval(autoSlide, 21000);
function autoSlide() {
    if (!isPaused) {
        counter += 1;
        slidefun(counter);
    }
}
function plusSlides(n) {
    counter += n;
    slidefun(counter);
    resetTimer();
}
function currentSlide(n) {
    counter = n;
    slidefun(counter);
    resetTimer();
}
function resetTimer() {
    clearInterval(timer);
    timer = setInterval(autoSlide, 21000);
}
function slidefun(n) {
    let i;
    for (i = 0; i < myslide.length; i++) {
        myslide[i].style.display = "none";
    }
    for (i = 0; i < dot.length; i++) {
        dot[i].className = dot[i].className.replace(' active', '');
    }
    if (n > myslide.length) {
        counter = 1;
    }
    if (n < 1) {
        counter = myslide.length;
    }
    myslide[counter - 1].style.display = "block";
    dot[counter - 1].className += " active";
}

function togglePause() {
    const pauseButton = document.getElementById('pauseButton');
    isPaused = !isPaused;
    if (isPaused) {
        pauseButton.textContent = 'Play';
        clearInterval(timer);
    } else {
        pauseButton.textContent = 'Pause';
        resetTimer();
    }
}
