import os, requests

def login(request):
    auth = request.authorization
    if not auth:
        return None, ("Missing authorization credentials", 401)

    basicAuth = (auth.username, auth.password)

    auth_svc = os.environ.get("AUTH_SVC_ADDRESS")
    if not auth_svc:
        return None, ("AUTH_SVC_ADDRESS not set", 500)

    try:
        response = requests.post(
            f"http://{auth_svc}/login",
            auth=basicAuth,
            timeout=5
        )
    except requests.RequestException as e:
        return None, (str(e), 502)

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)
