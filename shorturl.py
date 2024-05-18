from bottle import route, run, request, response, redirect
import base64
import configparser
from dotenv import load_dotenv
import os

# site name displayed in short links returned to users
site_uri = ""

# sqllite file name
db_name = "shorturls.db"
db_uri = "libsql://genuine-magneto-bch13.turso.io"

conn = None

@route('/', method="get")
def index():
    return '''
        <h1>ShortUrl</h1>
        <form action="/" method="post">
            Long URL: <input name="longurl" type="text" /> <br/>
            Short name (optional): <input name="name" type="text" /> <br />
            <input value="Create" type="submit" />
        </form>
    '''

# Creates a new url with provided name and long url.
@route('/', method="post")
def post():
    # TODO: implement a lock or tx for get -> add flow to avoid race conditions
    name = request.params['name']
    longurl = request.params['longurl']

    if not (longurl.startswith("http://") or longurl.startswith("https://")):
        longurl = "https://" + longurl
    existingRec = getFromDb(name)
    if existingRec != None:
        response.status = 409
        return "A shortlink with name %s already exists" % (name)

    if name == None or len(name) == 0:
        # use a base64-encoded hash of the long url to generate a short url
        h = hash(longurl)
        encoded = base64.b64encode(str(h).encode()).decode()
        name = encoded.lower().strip('=')
    
    addToDb(name, longurl)

    return '''
        <b>Short URL:</b>
        <a href="/%s">%s/%s</a>
        <button onclick="history.back()">Go Back</button>
        ''' % (name, site_uri, name)

# Redirects the user to the longurl referred to by the provided shorturl.
@route('/<name>', method="get")
def get(name):
    print(name)
    existingRec = getFromDb(name)
    print(existingRec)
    if existingRec == None:
        response.status = 404
        return "404 Not Found"
    
    redirect(existingRec)

# Deletes a shorturl.
@route('/<name>', method="delete")
def delete(name):
    existingRec = getFromDb(name)

    if existingRec == None:
        response.status = 404
        return "404 Not Found"
    
    conn = connect()
    conn.execute("DELETE FROM urls WHERE shorturl = ?", tuple([name]))
    conn.commit()

# Access db data
def getFromDb(shorturl):
    print("connecting to get form db")
    print("connected. executing...")
    conn = connect()
    row = conn.execute("SELECT longurl from urls WHERE shorturl = ?", tuple([shorturl])).fetchone()
    if row == None:
        conn.sync()
        row = conn.execute("SELECT longurl from urls WHERE shorturl = ?", tuple([shorturl])).fetchone()
    return row[0] if row != None else None

# Add to data in db
def addToDb(shorturl, longurl):
    conn = connect()
    conn.execute("INSERT INTO urls (shorturl, longurl) VALUES (?,?)", tuple([shorturl, longurl]))
    conn.commit()
    conn.sync()

def connect():
    import libsql_experimental as libsql

    tursotoken = os.environ.get("shorturl_tursotoken", "")
    res = libsql.connect(db_name, sync_url=db_uri, auth_token=tursotoken)
    print("result: %s" % (res))
    return res


def main():
    load_dotenv()  # take environment variables from .env.
    config = configparser.ConfigParser()
    config.read('config.ini')
    global site_uri
    site_uri = config['shorturl']['siteurl']
    port = config['shorturl']['port']

    global tursotoken
    global conn
    conn = connect()
    conn.execute("CREATE TABLE IF NOT EXISTS urls(shorturl, longurl)")
    conn.commit()
    
    run(host='0.0.0.0', port=port)

main()