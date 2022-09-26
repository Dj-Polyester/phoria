
function addRoute(url, sub) {
    var tmp = url.split("/")
    tmp.pop()
    tmp.push(sub)
    return tmp.join("/")
}

async function onCart(event) {
    console.log(cart);
    try {
        res = await fetch(addRoute(window.location.href, "cart"),
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(cart)
            }
        )
        if (!res.ok) {
            console.log(await res.json());
        }
    } catch (error) {
        console.log(error);
    }
}