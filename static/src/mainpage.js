var cart = new Array()

function onAddCart(event) {
    const btnElement = event.srcElement;
    const productId = btnElement.parentElement.parentElement.querySelector("div[hidden]").innerText | 0;
    const productStock = btnElement.parentElement.parentElement.querySelector(".no-items-add > input");

    val = productStock.value == "" ? 1 : productStock.value | 0;

    cart.push({ id: productId, itemsToBuy: val })
}