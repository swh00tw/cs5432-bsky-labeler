"""Implementation of automated moderator"""

from typing import List
from atproto import Client
from .label import post_from_url

T_AND_S_LABEL = "t-and-s"
DOG_LABEL = "dog"
THRESH = 0.3


class AutomatedLabeler:
    """Automated labeler implementation"""

    def __init__(self, client: Client, input_dir):
        self.client = client
        self.input_dir = input_dir

        # for T-AND-S label
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

    def moderate_post(self, url: str) -> List[str]:
        """
        Apply moderation to the post specified by the given url
        """
        post = post_from_url(self.client, url)
        postBody = post.value.text
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

        return labels
