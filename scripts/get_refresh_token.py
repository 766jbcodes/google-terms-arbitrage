"""One-time script to generate an OAuth2 refresh token for Google Ads API.
Starts a local HTTP server to handle the OAuth redirect."""
import json
import os
import urllib.parse
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import webbrowser
import threading

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

CLIENT_ID = os.environ["GOOGLE_ADS_CLIENT_ID"]
CLIENT_SECRET = os.environ["GOOGLE_ADS_CLIENT_SECRET"]
SCOPE = "https://www.googleapis.com/auth/adwords"
REDIRECT_URI = "http://localhost:8431"

auth_code = None


class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h2>Authorization successful!</h2>"
                             b"<p>You can close this tab and return to the terminal.</p></body></html>")
        else:
            error = params.get("error", ["unknown"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><body><h2>Error: {error}</h2></body></html>".encode())

    def log_message(self, format, *args):
        pass  # suppress request logs


def main():
    global auth_code

    auth_url = (
        "https://accounts.google.com/o/oauth2/auth?"
        + urllib.parse.urlencode({
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPE,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
        })
    )

    server = HTTPServer(("localhost", 8431), OAuthHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.start()

    print("Opening browser for Google sign-in...")
    webbrowser.open(auth_url)
    print("Waiting for authorization...\n")

    thread.join(timeout=120)
    server.server_close()

    if not auth_code:
        print("Timed out or no authorization code received.")
        return

    print("Got authorization code, exchanging for refresh token...")

    data = urllib.parse.urlencode({
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()

    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read())

    refresh_token = tokens.get("refresh_token")
    if refresh_token:
        print(f"\nRefresh token:\n{refresh_token}")
        print("\nAdd this to your .env file as GOOGLE_ADS_REFRESH_TOKEN")
    else:
        print(f"\nUnexpected response: {tokens}")


if __name__ == "__main__":
    main()
