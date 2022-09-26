import shutil
from credentials import *
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy
from flask.cli import AppGroup
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, abort, url_for, redirect
import sys
import os
from random import randint, sample, choice, random
import string
from crypt import methods

LOCALHOST = "127.0.0.1"
staticDir = "static"
templatesDir = Path(staticDir, "templates")

app = Flask(__name__, static_folder=staticDir, template_folder=templatesDir)

app.config["SERVER_NAME"] = f"{HOST}:{PORT}"
app.config["APPLICATION_ROOT"] = f"/"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql+psycopg2://{DBUSER}:{DBPASSWD}@{DBHOST}:{DBPORT}/{DBNAME}"
app.config["PREFERRED_URL_SCHEME"] = "https"
IMAGES_FOLDER = Path(app.static_folder, "images")
db = SQLAlchemy(app)
# MODELS

whitelisted = None
with open("whitelist.txt", "r") as f:
    whitelisted = f.readlines()


def valid(request, passwd):
    return request.remote_addr in whitelisted and passwd == PASSWD


def remote2bytes(rmt):
    rmtList = None
    # v4
    if "." in rmt:
        rmtList = rmt.split(".")
    # v6
    if ":" in rmt:
        rmtList = rmt.split(".")
    return bytes(map(int, rmtList))


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.INTEGER, primary_key=True)
    name = db.Column(db.CHAR(40))
    price = db.Column(db.REAL, nullable=False)
    description = db.Column(db.TEXT, nullable=False)
    images = db.Column(db.ARRAY(db.TEXT), nullable=False)
    itemsInStock = db.Column(db.INTEGER, nullable=False)
    remote = db.Column(db.LargeBinary, nullable=False)

    def __init__(self,
                 remote,
                 name,
                 price,
                 description,
                 images,
                 itemsInStock=1,
                 ):
        self.remote = remote2bytes(remote)
        self.name = name
        self.price = price
        self.description = description
        self.images = images
        self.itemsInStock = itemsInStock

    def __repr__(self):
        return str(vars(self))


class CartProduct(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.INTEGER, primary_key=True)
    itemsToBuy = db.Column(db.INTEGER, nullable=False)
    remote = db.Column(db.LargeBinary, nullable=False)

    def __init__(self,
                 id,
                 remote,
                 itemsToBuy=1,
                 ):
        self.id = id
        self.itemsToBuy = itemsToBuy
        self.remote = remote2bytes(remote)

    def __repr__(self):
        return str(vars(self))

# ROUTES


def renderProducts(products, **kwargs):
    return render_template(kwargs["parent"], products=[render_template(
        kwargs["child"], **vars(productRaw)) for productRaw in products], **kwargs)


def renderAllProducts(**kwargs):
    return renderProducts(Product.query.order_by(Product.name.asc()).all(), **kwargs)


def renderAdminProducts(**kwargs):
    rmtBytes = remote2bytes(kwargs["remote"])
    return renderProducts(Product.query.filter(Product.remote == rmtBytes).order_by(Product.name.asc()).all(), **kwargs)


# def renderCartProducts(products, **kwargs):
#     return renderProducts([CartProduct(product, products[product.name]) for product in Product.query.filter(Product.name.in_(products.keys())).order_by(
#         Product.name.asc()).all()], **kwargs)


@ app.route("/", methods=["GET", "POST"])
def mainpageRoute():
    if request.method == "GET":
        return renderAllProducts(parent="mainpage.html", child="product.html", links=[
            {"name": "Main page", "href": url_for("mainpageRoute")},
            {"name": "My cart", "href": url_for(
                "cartRoute"), "onclick": "onCart(event)", "disabled": True},
        ])
    elif request.method == "POST":
        content_type = request.headers.get('Content-Type')
        return f'{content_type}: {request.form}!'


@ app.route("/cart", methods=["GET", "POST"])
def cartRoute():
    # products = None
    # if request.method == "GET":
    #     cartProducts = CartProduct.filter_by(remote=request.remote_addr).all()
    #     products =

    #     return renderCartProducts(products, parent="cart.html", child="product_cart.html", links=[
    #         {"name": "Main page", "href": url_for("mainpageRoute")},
    #         {"name": "My cart", "href": url_for(
    #             "cartRoute"), "onclick": "onCart(event)", "disabled": True},
    #     ])
    # el
    if request.method == "POST":
        productsRaw = request.json
        db.session.add_all([CartProduct(
            remote=request.remote_addr, **productRaw) for productRaw in productsRaw])
        db.session.commit()
    return "True"


@ app.route("/admin/<passwd>")
def adminRoute(passwd):
    if valid(request, passwd):
        return renderAdminProducts(parent="admin.html", child="product_admin.html", remote=request.remote_addr, links=[
            {"name": "Add item", "href": url_for(
                "addItemRoute", passwd=passwd)}
        ])
    return abort(404)


@ app.route("/admin/add/<passwd>", methods=["GET", "POST"])
def addItemRoute(passwd):
    if valid(request, passwd):
        if request.method == "GET":
            elems = [
                {
                    "name": "name",
                    "type": "text",
                    "maxlength": "40",
                },
                {
                    "name": "description",
                    "type": "text",
                },
                {
                    "name": "price",
                    "type": "text",
                },
                {
                    "name": "images",
                    "type": "file",
                    "data": "multiple",
                    "onchange": "onChange(event)",
                },
                {
                    "name": "itemsInStock",
                    "readableName": "items in stock",
                    "type": "number",
                    "maxlength": 2,
                    "min": 0,
                    "max": 99,
                    "value": 1,
                },
            ]
            return render_template("add_item.html", name="Add item", elems=elems)
        elif request.method == "POST":
            imgFiles = request.files.getlist("images")
            addImages(imgFiles, remote=request.remote_addr, **request.form)
            db.session.commit()
            return redirect(url_for(
                "adminRoute", passwd=passwd))
    return abort(404)


def addImages(imgList, src=None, **kwargs):
    imgListNumbered = [None]*len(imgList)
    prevFile = None
    with open(Path(IMAGES_FOLDER, "current.txt"), "r") as currFile:
        prevFile = int(currFile.read())
    for index, file in enumerate(imgList):
        fname = file if src else file.filename
        fileExt = fname.split(".")[-1]
        newFileName = f"{prevFile + index}.{fileExt}"
        newFilePath = Path(IMAGES_FOLDER, secure_filename(newFileName))
        if src:
            shutil.copyfile(str(Path(src, fname)), str(newFilePath))
        else:
            file.save(newFilePath)

        imgListNumbered[index] = url_for(
            "static", filename=f"images/{newFileName}")
        print(imgListNumbered[index])
    with open(Path(IMAGES_FOLDER, "current.txt"), "r+") as currFile:
        currFile.seek(0)
        currFile.write(str(prevFile + len(imgList)))
        currFile.truncate()
    db.session.add(
        Product(
            kwargs["remote"],
            kwargs["name"],
            kwargs["price"],
            kwargs["description"],
            imgListNumbered,
            kwargs["itemsInStock"],
        )
    )


@app.route("/admin/delete/<passwd>", methods=["POST"])
def deleteItemRoute(passwd):
    if valid(request, passwd):
        data = request.json
        product = Product.query.filter_by(
            id=data["id"], remote=remote2bytes(request.remote_addr)).first()
        db.session.delete(product)
        db.session.commit()
        return "True"
    return abort(404)


@app.route("/admin/update/<passwd>", methods=["POST"])
def updateItemRoute(passwd):
    if valid(request, passwd):
        data = request.json
        product = Product.query.filter_by(
            id=data["id"], remote=remote2bytes(request.remote_addr)).first()
        product.itemsInStock = data["itemsInStock"]
        db.session.commit()
        return "True"
    return abort(404)


# COMMANDS
db_cli = AppGroup('db')


def createdb():
    db.create_all()


def dropdb():
    for root, _, files in os.walk(IMAGES_FOLDER):
        for file in files:
            fileExt = file.split(".")[-1]
            if isImg(fileExt):
                os.remove(Path(root, file))
    with open(Path(IMAGES_FOLDER, "current.txt"), "r+") as currFile:
        currFile.seek(0)
        currFile.write("0")
        currFile.truncate()
    db.drop_all()


@db_cli.command('create')
def create_db():
    """Creates the database + tables."""
    createdb()


@db_cli.command('drop')
def drop_db():
    """Drops the database + tables."""
    dropdb()


@db_cli.command('reset')
def reset_db():
    """Resets the database + tables."""
    dropdb()
    createdb()


def isImg(fileExt):
    return fileExt in ["png", "jpg", "jpeg"]
# TEST COMMANDS
def randStr(length): return ''.join(choice(string.ascii_lowercase)
                                    for i in range(length))


def randFloat(a, b): return random()*(b-a)+a


THRESHOLD = .8


@db_cli.command('random')
def randomdb():
    """Fills in the table with random entries."""
    SRC_PATH = "test"
    imgFiles = list(filter(lambda x: isImg(
        x.split(".")[-1]), os.listdir(SRC_PATH)))
    print(imgFiles)
    iterLength = randint(10, 20)
    rndids = [None]*iterLength
    for i in range(iterLength):
        imgSample = sample(imgFiles, randint(1, len(imgFiles)))
        addImages(
            imgSample, src=SRC_PATH,
            remote=LOCALHOST,
            name=randStr(randint(10, 40)),
            price=randFloat(10, 40),
            description=randStr(randint(100, 1000)),
            itemsInStock=randint(0, 99),
        )
        if random() > THRESHOLD:
            rndid = None
            while rndid in rndids:
                rndid = randint(1, iterLength)
            rndids[i] = rndid
            db.session.add(
                CartProduct(
                    id=rndid,
                    remote=LOCALHOST,
                    itemsToBuy=randint(0, 99),
                )
            )
    db.session.commit()


app.cli.add_command(db_cli)


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "Product": Product, "CartProduct": CartProduct, "remote2bytes": remote2bytes}


# MAIN
if __name__ == "__main__":
    app.run(debug=True, host=HOST, port=PORT, ssl_context='adhoc')
