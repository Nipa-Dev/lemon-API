# lemonAPI
Small part of larger API. Gives random fact related to lemons. The larger API is not yet published.

## Usage
**This project is built to run in docker, basically only because of PostgreSQL**
You may connect to your own postgresql host by modifying `./lemonapi/utils/config.py` ``Server`` class.

## Credentials
There are no default testing credentials, you must create user yourself. It is done easily in the `/docs/` endpoint, security section --> `add_user`.

### Docker usage
Project has `Dockerfile` and `docker-compose.yml` pre made.
1) clone repo
2) in terminal type `docker compose up --build` to run and build or `docker compose build` to only build image
3) API should be running

### Using the API

The API should be running at `http://localhost:5001` check `http://localhost:5001/docs` to view endpoints.

## How to make a request to get API token?
Most of functionality can be tested alone in the `/docs` endpoint, but you may as well interact with code.
This example will give you access to authorization token used to authenticate your request to endpoints requiring OAuth2.

With curl when endpoint is running with https:
```bash
curl -d "username=admin&password=weakadmin" --ssl-no-revoke -X POST https://127.0.0.1:5001/token
```
```py
import requests

data = {"username": "exampleusername", "password": "coolpassword"}  # example data

resp = session.post(
    "http://localhost:5001/token", data=data
)  # request to the server to get token

token = resp.json()["access_token"]  # get the token from the response
print("access token", token)  # printing the access token
```
### Using the API token
Using the variable `token` from example above. The endpoint `/lemon/verbs` uses OAuth2, so you must pass an Authorization token.
```py
import requests

foo = requests.get(
    "http://localhost:5001/lemon/verbs", headers={"Authorization": f"Bearer {token}"}
)
print(foo.status_code)  # You should be granted with response status 200
```
That's it, you should be able to get started with the basics
## Errors

If you find a bug or error, open an issue and give a required information such as function/line where it happens in at, what is wrong and possibly other information (optional)

Want to know more about the API? Open an issue with label **question** or DM me in discord or something idk.
