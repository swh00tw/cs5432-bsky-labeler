"""Simple test to ensure that you can query labels which issued by our labeler account"""

import os

from atproto import Client
from dotenv import load_dotenv

from pylabel import did_from_handle

load_dotenv(override=True)
USERNAME = os.getenv("USERNAME")
PW = os.getenv("PW")


def main():
    """Main function"""
    client = Client()
    client.login(USERNAME, PW)

    uris = ["at://did:plc:z72i7hdynmk6r22z27h6tvur/app.bsky.feed.post/3l6oveex3ii2l"]
    did = did_from_handle(USERNAME)

    response = client.com.atproto.label.query_labels(
        {"uri_patterns": uris, "sources": [did]}
    )
    print("Successfully loaded labels:", response)


if __name__ == "__main__":
    main()
