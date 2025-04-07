"""Implementation of automated moderator"""

from typing import List, TypeGuard
from atproto import Client
from atproto_client.models.app.bsky.embed.images import Main as Images, Image
from atproto_client.models.blob_ref import IpldLink
from .label import post_from_url
import os
from perception.hashers.image import PHash

T_AND_S_LABEL = "t-and-s"
DOG_LABEL = "dog"
THRESH = 0.3


class AutomatedLabeler:
    """Automated labeler implementation"""

    def __init__(self, client: Client, input_dir):
        self.client = client
        self.input_dir = input_dir
        self.hasher = PHash()

        # for milestone2: T-AND-S label
        tsWordSet = set()
        tsDomainSet = set()
        # read words from t-and-s-words.csv under input_dir
        with open(f"{input_dir}/t-and-s-words.csv", "r") as f:
            for line in f:
                tsWordSet.add(line.strip().lower())
        # read domains from t-and-s-domains.csv under input_dir
        with open(f"{input_dir}/t-and-s-domains.csv", "r") as f:
            for line in f:
                tsDomainSet.add(line.strip().lower())
        self.tsWordSet = tsWordSet
        self.tsDomainSet = tsDomainSet

        # for milestone3: citation labels
        domainToLabel = {}
        # read domain, label pair from news-domains.csv under input_dir
        with open(f"{input_dir}/news-domains.csv", "r") as f:
            for line in f:
                domain, label = line.strip().split(",")
                domainToLabel[domain] = label
        self.domainToLabel = domainToLabel

        # for milestone4: dog images
        self.dogImageHashes = []
        dog_images_dir = f"{self.input_dir}/dog-list-images"
        for filename in os.listdir(dog_images_dir):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(dog_images_dir, filename)
                hash = self.hasher.compute(image_path)
                self.dogImageHashes.append(hash)

    def moderate_post(self, url: str) -> List[str]:
        """
        Apply moderation to the post specified by the given url
        """
        post = post_from_url(self.client, url)
        postBody = post.value.text
        authorDid = self.getDidFromRecordUri(post.uri)
        labels = []

        # T-AND-S
        # if postBody contains words or domains in tsWordSet or tsDomainSet, add T_AND_S_LABEL
        shouldApplyTSLabel = False
        if any(word in postBody.lower() for word in self.tsWordSet):
            shouldApplyTSLabel = True
        if any(domain in postBody.lower() for domain in self.tsDomainSet):
            shouldApplyTSLabel = True
        if shouldApplyTSLabel:
            labels.append(T_AND_S_LABEL)

        # CITATION
        # if postBody contains words or domains in domainToLabel, add corresponding label
        for domain in self.domainToLabel:
            if domain in postBody.lower():
                labels.append(self.domainToLabel[domain])

        # DOG IMAGE
        if self.isEmbedImages(post.value.embed):
            for image in post.value.embed.images:
                image_url = self.extractImageUrl(image, authorDid)
                distance = self.getImageHashDistance(image_url)
                if distance <= THRESH:
                    labels.append(DOG_LABEL)
                    break

        return labels

    def isEmbedImages(self, embed) -> TypeGuard[Images]:
        """
        Type guard to narrow down the type of embed field of post record to models.AppBskyEmbedImages
        ref: https://atproto.blue/en/latest/atproto/atproto_client.models.app.bsky.feed.post.html#atproto_client.models.app.bsky.feed.post.Record
        """
        return embed.py_type == "app.bsky.embed.images"

    def extractImageUrl(self, image: Image, did: str) -> str:
        """
        Extract the image url from the given image object
        """
        cid = ""
        if isinstance(image.image.ref, IpldLink):
            cid = image.image.ref.link
        elif isinstance(image.image.ref, bytes):
            cid = image.image.ref.decode('utf-8')
        else:
            cid = image.image.ref

        return f"https://cdn.bsky.app/img/feed_thumbnail/plain/{did}/{cid}@jpeg"

    def getDidFromRecordUri(self, uri: str) -> str:
        """
        Extract the did from the given uri
        """
        return uri.split("/")[-3]

    def getImageHashDistance(self, image_url: str) -> float:
        """
        Get the minimum hash distance between an image and a list of reference hashes
        """
        try:
            # Compute hash directly from URL
            target_hash = self.hasher.compute(image_url)
            if target_hash is None or isinstance(target_hash, list):
                return float('inf')

            # Find minimum distance to any reference hash
            min_distance = float('inf')
            for ref_hash in self.dogImageHashes:
                distance = self.hasher.compute_distance(target_hash, ref_hash)
                min_distance = min(min_distance, distance)

            return float(min_distance)

        except Exception as e:
            print(f"Error processing image {image_url}: {e}")
            return float('inf')
