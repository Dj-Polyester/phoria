function onChange(event) {
    const inputElement = event.srcElement;
    console.log(inputElement.files);
    // inputElement.name = inputElement.value
    // const clone = inputElement.cloneNode(true);
    // clone.value = ""
    // inputElement.parentElement.insertBefore(clone, inputElement.nextSibling);
}