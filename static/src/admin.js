
function subRoute(url, sub) {
    var tmp = url.split("/")
    tmp.splice(tmp.length - 1, 0, sub)
    return tmp.join("/")
}

async function onStockChange(event) {
    const inputElem = event.srcElement;
    const productStock = inputElem.value | 0;
    const productId = inputElem.parentElement.parentElement.querySelector("div[hidden]").innerText | 0;
    try {
        res = await fetch(subRoute(window.location.href, "update"),
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    id: productId,
                    itemsInStock: productStock,
                })
            }
        );
        if (!res.ok) {
            console.log(await res.json());
        }
    } catch (error) {
        console.log(error);
    }
}
//window.location.href
async function onDelete(event) {
    const btnElement = event.srcElement;
    const productId = btnElement.parentElement.querySelector("div[hidden]").innerText | 0;
    try {
        res = await fetch(subRoute(window.location.href, "delete"),
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    id: productId,
                })
            }
        );
        if (!res.ok) {
            console.log(await res.json());
        }
    } catch (error) {
        console.log(error);
    }
    window.location.reload();
}