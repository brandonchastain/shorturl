from bottle import route, run, request, response, redirect
import base64
import configparser
import sqlite3

# site name displayed in short links returned to users
siteurl = ""

# sqllite file name
dbname = "shorturls.db"

@route('/', method="get")
def index():
    return '''
        <h1>ShortUrl</h1>
        <form action="/" method="post">
            Long URL: <input name="longurl" type="text" /> <br/>
            Short name (optional): <input name="name" type="text" />
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
        ''' % (name, siteurl, name)

# Redirects the user to the longurl referred to by the provided shorturl.
@route('/<name>', method="get")
def get(name):
    existingRec = getFromDb(name)

    if existingRec == None:
        response.status = 404
        return "404 Not Found"
    
    redirect(existingRec)

# Deletes a shorturl.
@route('/<name>', method="delete")
def delete(name):
    # TODO: implement a lock or tx for get -> delete flow to avoid race conditions
    existingRec = getFromDb(name)

    if existingRec == None:
        response.status = 404
        return "404 Not Found"
    
    with sqlite3.connect(dbname) as db:
        db.execute("DELETE FROM urls WHERE shorturl = ?", [name])

# Access db data
def getFromDb(shorturl):
    with sqlite3.connect(dbname) as db:
        res = db.execute("SELECT longurl from urls WHERE shorturl = ?", [shorturl])
        longurl = res.fetchone()
        return longurl[0] if longurl != None else None

# Add to data in db
def addToDb(shorturl, longurl):
    with sqlite3.connect(dbname) as db:
        db.execute("INSERT INTO urls (shorturl, longurl) VALUES (?,?)", [shorturl, longurl])

def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    global siteurl
    siteurl = config['shorturl']['siteurl']
    port = config['shorturl']['port']

    with sqlite3.connect(dbname) as db:
        db.execute("CREATE TABLE IF NOT EXISTS urls(shorturl, longurl)")
    
    run(host='0.0.0.0', port=port, server="gunicorn")

if __name__ == "__main__":
    main()