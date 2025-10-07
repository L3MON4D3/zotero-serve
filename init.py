from flask import Flask, send_from_directory, url_for, render_template
import sqlite3
from urllib.parse import quote_plus
from markupsafe import Markup
from pprint import pp
import os
import tempfile
from enum import Enum


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
    for (id,name) in cursor.execute(
        """
            select
                collections.collectionID, collectionName
            from
                collections
            where
                collections.collectionID not in (select collectionID from deletedCollections)
            ;
        """).fetchall() :
        collectionlist += Markup("<li class='bulletless'><a href='%s'>%s</a></li>") % (url_for("collectionitems", id=id), name)
    collectionlist += Markup("</ul>")

    return render_template("base.html", title = "Collections", header = "Collections", content = collectionlist)


class ItemTypes(Enum):
    ANNOTATION = 1
    ARTWORK = 2
    ATTACHMENT = 3
    AUDIORECORDING = 4
    BILL = 5
    BLOGPOST = 6
    BOOK = 7
    BOOKSECTION = 8
    CASE = 9
    COMPUTERPROGRAM = 10
    CONFERENCEPAPER = 11
    DATASET = 12
    DICTIONARYENTRY = 13
    DOCUMENT = 14
    EMAIL = 15
    ENCYCLOPEDIAARTICLE = 16 
    FILM = 17
    FORUMPOST = 18
    HEARING = 19
    INSTANTMESSAGE = 20
    INTERVIEW = 21
    JOURNALARTICLE = 22
    LETTER = 23
    MAGAZINEARTICLE = 24
    MANUSCRIPT = 25
    MAP = 26
    NEWSPAPERARTICLE = 27
    NOTE = 28
    PATENT = 29
    PODCAST = 30
    PREPRINT = 31
    PRESENTATION = 32
    RADIOBROADCAST = 33
    REPORT = 34
    STANDARD = 35
    STATUTE = 36
    THESIS = 37
    TVBROADCAST = 38
    VIDEORECORDING = 39
    WEBPAGE = 40

itemType_displayname = {
        ItemTypes.ANNOTATION: "Annotation",
        ItemTypes.ARTWORK: "Artwork",
        ItemTypes.ATTACHMENT: "Attachment",
        ItemTypes.AUDIORECORDING: "Audiorecording",
        ItemTypes.BILL: "Bill",
        ItemTypes.BLOGPOST: "Blogpost",
        ItemTypes.BOOK: "Book",
        ItemTypes.BOOKSECTION: "Booksection",
        ItemTypes.CASE: "Case",
        ItemTypes.COMPUTERPROGRAM: "Computer Program",
        ItemTypes.CONFERENCEPAPER: "Conference Paper",
        ItemTypes.DATASET: "Dataset",
        ItemTypes.DICTIONARYENTRY: "Dictionary entry",
        ItemTypes.DOCUMENT: "Document",
        ItemTypes.EMAIL: "Email",
        ItemTypes.ENCYCLOPEDIAARTICLE: "Encyclopedia article",
        ItemTypes.FILM: "Film",
        ItemTypes.FORUMPOST: "Forumpost",
        ItemTypes.HEARING: "Hearing",
        ItemTypes.INSTANTMESSAGE: "Instantmessage",
        ItemTypes.INTERVIEW: "Interview",
        ItemTypes.JOURNALARTICLE: "Journal article",
        ItemTypes.LETTER: "Letter",
        ItemTypes.MAGAZINEARTICLE: "Magazine article",
        ItemTypes.MANUSCRIPT: "Manuscript",
        ItemTypes.MAP: "Map",
        ItemTypes.NEWSPAPERARTICLE: "Newspaper article",
        ItemTypes.NOTE: "Note",
        ItemTypes.PATENT: "Patent",
        ItemTypes.PODCAST: "Podcast",
        ItemTypes.PREPRINT: "Preprint",
        ItemTypes.PRESENTATION: "Presentation",
        ItemTypes.RADIOBROADCAST: "Radio Broadcast",
        ItemTypes.REPORT: "Report",
        ItemTypes.STANDARD: "Standard",
        ItemTypes.STATUTE: "Statute",
        ItemTypes.THESIS: "Thesis",
        ItemTypes.TVBROADCAST: "TV Broadcast",
        ItemTypes.VIDEORECORDING: "Videorecording",
        ItemTypes.WEBPAGE: "Webpage"
}

def render_link(itemID, itemTypeID, name, key, path) :
    itemType = ItemTypes(itemTypeID)
    if itemType == ItemTypes.ATTACHMENT:
        if path is None :
            print(f"Skipping attachment with itemID {itemID}, it is not associated with a local path.")
            return Markup("")
        fname = path[8:]
        storage_file = f"{key}/{fname}"
        return Markup("<a href='%s' class='file'>%s</a>") % (url_for("storage", path = storage_file), fname)
    else:
        return Markup("<a href='%s' class='item'>%s</a>") % (url_for("items", id=itemID), name) 
    
    
@app.route('/collection/<int:id>')
def collectionitems(id) :
    zotdb = sqlite3.connect(DBPATH)
    cursor = zotdb.cursor()

    collection_name = cursor.execute(f"select collectionName from collections where collectionID = {id};").fetchone()[0]

    items = cursor.execute(f'''
        select
            items.itemID, itemDataValues.value, items.itemTypeID, key, path
        from
            collectionItems
        inner join
            items on collectionItems.itemID = items.itemID
        inner join
            itemData on items.itemID = itemData.itemID
        inner join
            itemDataValues on itemData.valueID = itemDataValues.valueID
        left join
            itemAttachments on itemAttachments.itemID = items.itemID
        inner join
            fields on itemData.fieldID = fields.fieldID
        where
            collectionItems.collectionID = {id}
            and items.itemID not in (select itemID from deletedItems)
            and fieldName = "title"
        ;
    ''')
    
    itemlist = Markup("<ul>")
    for (itemID,name,typeID,key,path) in items :
        itemlist += Markup("<li class='bulletless'>%s</li>") % render_link(itemID=itemID,itemTypeID=typeID,name=name,key=key,path=path)
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

    field_rows = ""
    title = None
    for (name,value) in fields_cursor :
        if name == "url" :
            value = Markup("<a href='%s'>%s<a>") % (value, value)
        field_rows += Markup(
            """
                <tr>
                    <td class="fieldname">%s</td>
                    <td>%s</td>
                </tr>
            """) % (name, value)

        if name == "title" :
            title = value
        
    assert(title is not None)

    attachments_cursor = cursor.execute(f'''
        select
            items.itemID,itemTypeID,key,path
        from
            itemAttachments
        inner join
            items on itemAttachments.itemID = items.itemID
        where
            itemAttachments.parentItemID={id}
            and items.itemID not in (select itemID from deletedItems)
    ''')

    attachment_items = ""
    for (itemID,itemTypeID,key,path) in attachments_cursor :
        attachment_items += Markup("<li class='bulletless'>%s</li>") % render_link(itemID=itemID,itemTypeID=itemTypeID,name=None,key=key,path=path)
    attachment_items += ""

    template = Markup(
    """
        <h3>Attachments</h3>
        <ul>
            %s
        </ul>
        <h3>Fields</h3>
        <table>
            <tr>
                <th>Name</th>
                <th>Value</th>
            </tr>
            %s
        </table>
    """) % (attachment_items, field_rows)
    

    return render_template("base.html", title = title, content = template)
