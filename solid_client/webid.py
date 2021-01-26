from rdflib import Graph, URIRef, Literal, Namespace

SOLID = Namespace('http://www.w3.org/ns/solid/terms#')

g = Graph()
g.bind("solid", SOLID)
this = URIRef('#this')

g.add((this, SOLID.oidcRegistration, Literal(
    '''{
    "client_id": "http://127.0.0.1:8001/webid#this",
    "redirect_uris": [ "http://127.0.0.1:8001/callback" ],
    "client_name": "Example Client",
    "client_uri": "http://127.0.0.1:8001/",
    "logo_uri": "http://127.0.0.1:8001/logo.png",
    "tos_uri": "http://127.0.0.1:8001/tos.html",
    "scope": "openid profile offline_access",
    "grant_types": [ "refresh_token", "authorization_code" ],
    "response_types": [ "code" ],
    "default_max_age": 60000,
    "require_auth_time": true
    }''')))

g.serialize('/Users/hamishgibbs/Documents/Personal/solid_client/static/webid.ttl', format='turtle')

from rdflib.plugins.sparql import prepareQuery

q = prepareQuery(
    'SELECT ?o WHERE { ?s <http://www.w3.org/ns/solid/terms#oidcRegistration> ?o }'
)


for row in g.query(q):
        print(row)


row[0]
