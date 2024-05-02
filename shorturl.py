from bottle import route, run, request, response, redirect
import base64

# Map of shorturls to their associated long urls
# (ideally should be a database or KV store)
urlMap = dict()

@route('/', method="get")
def index():
    return '''
        <form action="/" method="post">
            Long URL: <input name="longurl" type="text" /> <br/>
            Short name (optional): <input name="name" type="text" />
            <input value="Create" type="submit" />
        </form>
    '''

# Creates a new url with provided name and long url.
@route('/', method="post")
def post():
    name = request.params['name']
    longurl = request.params['longurl']

    if name == None or len(name) == 0:
        # use a base64-encoded hash of the long url to generate a short url
        h = hash(longurl)
        encoded = base64.b64encode(str(h).encode()).decode()
        name = encoded.lower().strip('=')
    elif name in urlMap and urlMap[name] != None:
        response.status = 409
        return "A shortlink with name %s already exists" % (name)
    
    urlMap[name] = longurl
    return '<b>Short URL:</b> <a href="http://localhost:8080/%s">http://localhost:8080/%s' % (name, name)

# Redirects the user to the longurl referred to by the provided shorturl.
@route('/<name>', method="get")
def get(name):
    if not name in urlMap or urlMap[name] == None:
        response.status = 404
        return
    redirect(urlMap[name])

# Deletes a shorturl.
@route('/<name>', method="delete")
def delete(name):
    if not name in urlMap or urlMap[name] == None:
        response.status = 404
        return
    urlMap[name] = None

run(host='localhost', port=8080)