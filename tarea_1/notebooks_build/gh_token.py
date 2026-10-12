# -*- coding: utf-8 -*-
"""Obtiene el token de GitHub del Credential Manager y prueba permisos."""
import subprocess

GCM = r"C:\Program Files\Git\mingw64\bin\git-credential-manager.exe"


def token():
    r = subprocess.run([GCM, "get"], input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True, timeout=30)
    datos = dict(l.split("=", 1) for l in r.stdout.strip().splitlines() if "=" in l)
    return datos.get("username"), datos.get("password")


if __name__ == "__main__":
    import urllib.request
    import json

    user, tok = token()
    req = urllib.request.Request("https://api.github.com/user",
                                 headers={"Authorization": f"Bearer {tok}",
                                          "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        d = json.loads(resp.read())
        print("login:", d.get("login"))
        scopes = resp.headers.get("X-OAuth-Scopes", "fine-grained o no listado")
        print("scopes:", scopes)
