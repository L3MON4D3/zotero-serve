from flask import Flask, send_from_directory, url_for, render_template
import sqlite3
from urllib.parse import quote_plus
from markupsafe import Markup
from pprint import pp
import os
import tempfile


ZOTERO_STORAGE_DIR = os.environ["ZOTERO_STORAGE_DIR"] # "/srv/misc/zotero/data/storage"
DBPATH_ORIG = os.environ["DBPATH_ORIG"] # "/mnt/zotero/zotero.sqlite"

tmpdir = tempfile.mkdtemp()
DBPATH = os.path.join(tmpdir, "zotero.sqlite") # "/home/simon/projects/zotero-serve/zotero.sqlite"
os.system(f"cp {DBPATH_ORIG} {DBPATH}")

app = Flask(__name__)

@app.route('/storage/<path:path>')
def storage(path):
    return send_from_directory(ZOTERO_STORAGE_DIR,
                               path, as_attachment=True)

@app.route('/')
def index() :
    # refresh guaranteed-unlocked db.
    os.system(f"cp {DBPATH_ORIG} {DBPATH}")

    zotdb = sqlite3.connect(DBPATH)
    cursor = zotdb.cursor()

    collectionlist = Markup("<ul>")
    for (id,name) in cursor.execute("select collectionID, collectionName from collections;").fetchall() :
        collectionlist += Markup("<li class='bulletless'><a href='%s'>%s</a></li>") % (url_for("collectionitems", id=id), name)
    collectionlist += Markup("</ul>")

    return render_template("base.html", title = "Collections", header = "Collections", content = collectionlist)

@app.route('/collection/<int:id>')
def collectionitems(id) :
    zotdb = sqlite3.connect(DBPATH)
    cursor = zotdb.cursor()

    collection_name = cursor.execute(f"select collectionName from collections where collectionID = {id};").fetchone()[0]

    items = cursor.execute(f'''
        select
            items.itemID, value
        from
            collectionItems
        inner join
            items on collectionItems.itemID = items.itemID
        inner join
            itemData on items.itemID = itemData.itemID
        inner join
            itemDataValues on itemData.valueID = itemDataValues.valueID
        inner join
            fields on itemData.fieldID = fields.fieldID
        where
            collectionItems.collectionID = {id}
            and items.itemID not in (select itemID from deletedItems)
            and fieldName = "title"
        ;
    ''')
    
    itemlist = Markup("<ul>")
    for (id,name) in items :
        itemlist += Markup("<li class='bulletless'><a href='%s'>%s</a></li>") % (url_for("items", id=id), name)
    itemlist += Markup("</ul>")

    return render_template("base.html", title = collection_name, content = itemlist)

@app.route('/items/<int:id>')
def items(id) :
    zotdb = sqlite3.connect(DBPATH)
    cursor = zotdb.cursor()

    fields_cursor = cursor.execute(f'''
        select
            fieldName, value
        from
            items
        inner join
            itemData on items.itemID = itemData.itemID
        inner join
            itemDataValues on itemData.valueID = itemDataValues.valueID
        inner join
            fields on itemData.fieldID = fields.fieldID
        where
            items.itemID = {id}
        ;
    ''').fetchall()

    fields = {}
    for res in fields_cursor :
        if res[0] == "title" :
            fields["title"] = res[1]
        
    # pp(fields)
    
    attachments_cursor = cursor.execute(f'''
        select
            key,path
        from
            itemAttachments
        inner join
            items on itemAttachments.itemID = items.itemID
        where
            itemAttachments.parentItemID={id}
            and items.itemID not in (select itemID from deletedItems)
    ''')

    attachment_list = Markup("<ul>")
    for res in attachments_cursor :
        pp(res)
        fname = res[1][8:]
        storage_file = f"{res[0]}/{fname}"
        attachment_list += Markup("<li class='bulletless'><a href='%s'>%s</a></li>") % (url_for("storage", path = storage_file), fname)
    attachment_list += Markup("</ul>")

    return render_template("base.html", title = fields["title"], content = attachment_list)
