Number.prototype.mod = function (n) {
    "use strict";
    return ((this % n) + n) % n;
};

function changeSlide(event, offset) {
    const btnElement = event.srcElement;
    const slides = btnElement.parentElement.querySelectorAll(".slide");
    const activeSlide = btnElement.parentElement.querySelector(".slide[data-active]");
    const newIndex = ([...slides].indexOf(activeSlide) + offset).mod(slides.length)
    delete activeSlide.dataset.active;
    slides[newIndex].dataset.active = true;
}