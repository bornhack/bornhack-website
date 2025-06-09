"""Quick oauth2 authorization code flow demo for whatever.

Create a user, login, go to /o/applications/ and create a new application:
- type: public
- grant type: authorization code
- redirect uri https://example.com/redirect/ (url can be whatever)

Then call this script with <hostname> <username> <password> <client_id>
./oauth.py http://127.0.0.1:8080 username password some_client_id

Only works with local users, not social users.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import string
import sys
from urllib.parse import parse_qs
from urllib.parse import urlparse

import requests

host = sys.argv[1]
username = sys.argv[2]
password = sys.argv[3]
client_id = sys.argv[4]

s = requests.Session()
csrf = s.get(host + "/api/csrf/")
csrf = s.post(
    # set next to /api/csrf/ so getting the next csrftoken is easy
    host + "/login/?next=/api/csrf/",
    data={
        "csrfmiddlewaretoken": csrf.text.strip(),
        "login": username,
        "password": password,
    },
    headers={"Referer": host + "/login/"},
)
alphabet = string.ascii_uppercase + string.digits
code_verifier = "".join(secrets.choice(alphabet) for i in range(43 + secrets.randbelow(86)))
code_verifier_base64 = base64.urlsafe_b64encode(code_verifier.encode("utf-8"))
code_challenge = hashlib.sha256(code_verifier_base64).digest()
code_challenge_base64 = base64.urlsafe_b64encode(code_challenge).decode("utf-8").replace("=", "")
state = "".join(secrets.choice(alphabet) for i in range(15))

data = {
    "csrfmiddlewaretoken": csrf.text.strip(),
    "client_id": client_id,
    "state": state,
    "redirect_uri": f"{host}/api/csrf/",
    "response_type": "code",
    "code_challenge": code_challenge_base64,
    "code_challenge_method": "S256",
    "nonce": "",
    "claims": "",
    "scope": "openid profile",
    "allow": "Authorize",
}
auth = s.post(
    host + "/o/authorize/",
    allow_redirects=False,
    data=data,
    headers={"Referer": host + "/o/authorize/"},
)
if auth.status_code != 302:
    print(f"/o/authorize/ returned status code {auth.status_code} - no token today")
    sys.exit(1)
url = auth.headers["Location"]
result = urlparse(url)
qs = parse_qs(result.query)
assert state == qs["state"][0]
authcode = qs["code"][0]
token = s.post(
    host + "/o/token/",
    data={
        "grant_type": "authorization_code",
        "code": authcode,
        "redirect_uri": f"{host}/api/csrf/",
        "client_id": client_id,
        "code_verifier": code_verifier_base64,
    },
)
print(token.json())
