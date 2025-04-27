"""Script to collect test data for the linguistic evasion labeler"""

import os
import json
import csv
from atproto import Client
from dotenv import load_dotenv

load_dotenv(override=True)
USERNAME = os.getenv("USERNAME")
PW = os.getenv("PW")

DEFAULT_LABEL = "linguistic-evasion"
SEARCH_TERMS = {
    "character-substitution": [
        # Character substitution examples
        "f@ck",
        "sh1t",
        "b!tch",
        "k1ll",
        "d!e",
        "h@te",
        "r3t@rd",
        "1d1ot",
        "@$$",
        "d1ck",
        "wh0re",
        "m0r0n",
        "r@c1st",
        "n@z1",
        "$tupid",
        "tr@$h",
        "fr3@k",
        "$lu+",
        "+err0r1st",
    ],
    # Homophone examples based on homophones.json
    "homophone": [
        "dye now",
        "kil yourself",
        "keel him",
        "h8 speech",
        "h8 you",
        "hayt crime",
        "4 you to die",
        "ur ugly",
        "ur stupid",
        "beach please",
        "sheet happens",
        "phuck that",
        "as hole",
        "sewer side thoughts",
        "commit sewer side",
        "ghey people",
        "gey marriage",
        "tranz people",
        "ray cyst comment",
        "race ist ideology",
        "yew deserve to die",
        "ewe should leave",
    ],
    # Spoonerism examples based on spoonerisms.json
    "spoonerism": [
        "yill kou",
        "yuck fou",
        "buck you",
        "till khem",
        "yill kourself",
        "ock fuff",
        "hit shead",
        "aumb dass",
        "ick sut",
        "yate hou",
        "nie dow",
        "fit the shan",
        "wit the fhat",
        "shaming neep",
        "ducking sick",
        "rucking fetarded",
        "bunning cumhag",
        "dumb fick",
        "tumb dass",
        "hure pussy",
    ],
}


def search_posts(client, output_file):
    """Search for posts that might contain linguistic evasion"""
    # Track existing URLs to avoid duplicates
    existing_urls = set()

    # Check if the file already exists and read existing URLs
    if os.path.exists(output_file):
        with open(output_file, "r", newline="") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if row:  # Make sure the row is not empty
                    existing_urls.add(row[0])  # Add URL to set

    # Open file in append mode if it exists, or write mode if it doesn't
    file_mode = "a" if os.path.exists(output_file) else "w"
    with open(output_file, file_mode, newline="") as f:
        writer = csv.writer(f)

        # Write header only if creating a new file
        if file_mode == "w":
            writer.writerow(["URL", "Labels"])

        for label, terms in SEARCH_TERMS.items():
            for term in terms:
                try:
                    print(f"Searching for term: {term}")
                    results = client.app.bsky.feed.search_posts(
                        {"q": term, "limit": 25}
                    )

                    for post in results.posts:
                        post_url = f"https://bsky.app/profile/{post.author.handle}/post/{post.uri.split('/')[-1]}"

                        # Skip if we've already processed this URL
                        if post_url in existing_urls:
                            print(f"Skipping duplicate post: {post_url}")
                            continue

                        labels_json = json.dumps([DEFAULT_LABEL, label])
                        writer.writerow([post_url, labels_json])
                        existing_urls.add(post_url)  # Add to set to track duplicates
                        print(f"Found new post: {post_url}")
                except Exception as e:
                    print(f"Error searching for {term}: {e}")


def main():
    """Main function"""
    client = Client()
    client.login(USERNAME, PW)

    output_file = "src/test-data/linguistic_evasion_test_posts.csv"
    search_posts(client, output_file)
    print(f"Data collection complete. Results appended to {output_file}")


if __name__ == "__main__":
    main()
