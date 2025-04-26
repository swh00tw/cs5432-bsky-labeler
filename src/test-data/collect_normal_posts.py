"""Script to collect normal posts (negative examples) for testing the linguistic evasion labeler"""

import os
import json
import csv
import random
from atproto import Client
from dotenv import load_dotenv

load_dotenv(override=True)
USERNAME = os.getenv("USERNAME")
PW = os.getenv("PW")

# Search terms for normal content that likely doesn't contain linguistic evasion
NORMAL_SEARCH_TERMS = [
    "good morning",
    "happy birthday",
    "beautiful day",
    "thanks for sharing",
    "just posted",
    "great photo",
    "interesting article",
    "weather today",
    "weekend plans",
    "new recipe",
    "love this song",
    "favorite book",
    "tech news",
    "just learned",
    "thinking about",
    "excited to share",
]

# Popular topics that are generally neutral
TOPICS = [
    "photography",
    "cooking",
    "hiking",
    "gardening",
    "reading",
    "travel",
    "music",
    "art",
    "technology",
    "science",
    "space",
    "history",
    "nature",
    "sports",
]


def collect_normal_posts(client, output_file, limit_per_term=25):
    """Collect normal posts without linguistic evasion"""
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

    # Combine search terms with topics for more diversity
    search_queries = NORMAL_SEARCH_TERMS.copy()
    for term in random.sample(NORMAL_SEARCH_TERMS, min(5, len(NORMAL_SEARCH_TERMS))):
        for topic in random.sample(TOPICS, min(3, len(TOPICS))):
            search_queries.append(f"{term} {topic}")

    # Open file in append mode if it exists, or write mode if it doesn't
    file_mode = "a" if os.path.exists(output_file) else "w"
    with open(output_file, file_mode, newline="") as f:
        writer = csv.writer(f)

        # Write header only if creating a new file
        if file_mode == "w":
            writer.writerow(["URL", "Labels"])

        for query in search_queries:
            try:
                print(f"Searching for normal posts: '{query}'")
                results = client.app.bsky.feed.search_posts(
                    {"q": query, "limit": limit_per_term}
                )

                count = 0
                for post in results.posts:
                    if count >= limit_per_term:
                        break

                    post_url = f"https://bsky.app/profile/{post.author.handle}/post/{post.uri.split('/')[-1]}"

                    # Skip if we've already processed this URL
                    if post_url in existing_urls:
                        print(f"Skipping duplicate post: {post_url}")
                        continue

                    # Empty array means no labels - this is a normal post
                    labels_json = json.dumps([])
                    writer.writerow([post_url, labels_json])
                    existing_urls.add(post_url)
                    count += 1
                    print(f"Found normal post: {post_url}")
            except Exception as e:
                print(f"Error searching for '{query}': {e}")


def main():
    """Main function"""
    client = Client()
    client.login(USERNAME, PW)

    output_file = "src/test-data/linguistic_evasion_test_posts.csv"
    collect_normal_posts(client, output_file)
    print(f"Data collection complete. Results appended to {output_file}")


if __name__ == "__main__":
    main()
