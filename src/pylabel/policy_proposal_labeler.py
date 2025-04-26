"""Implementation of linguistic evasion labeler for detecting dogpiling with evasion tactics"""

import json
import re
from typing import List, Dict, Set
from atproto import Client
from metaphone import doublemetaphone
from .label import post_from_url

# Label to apply for linguistic evasion
LINGUISTIC_EVASION_LABEL = "linguistic-evasion"
CHAR_SUBSTITUTION_LABEL = "character-substitution"
HOMOPHONE_LABEL = "homophone"
SPOONERISM_LABEL = "spoonerism"

# Thresholds for detection
CHAR_SUBSTITUTION_THRESHOLD = 0.8  # Min similarity score for character substitution
HOMOPHONE_SIMILARITY_THRESHOLD = 0.7  # Min phonetic similarity for homophones
MIN_WORD_LENGTH = 3  # Minimum word length to consider for harmful words


class LinguisticEvasionLabeler:
    """Labeler implementation for detecting posts with linguistic evasion"""

    def __init__(self, client: Client, input_dir: str):
        self.client = client
        self.input_dir = input_dir

        # Load harmful words
        self.harmful_words = self._load_harmful_words(f"{input_dir}/harmful_words.txt")

        # Create sets of harmful words by length for faster lookups
        self.harmful_words_by_length = {}
        for word in self.harmful_words:
            length = len(word)
            if length not in self.harmful_words_by_length:
                self.harmful_words_by_length[length] = set()
            self.harmful_words_by_length[length].add(word)

        # Load character substitutions
        self.char_substitutions = self._load_char_substitutions(
            f"{input_dir}/char_substitutions.json"
        )
        self.reverse_char_substitutions = self._create_reverse_substitutions()

        # Load homophones
        self.homophones = self._load_homophones(f"{input_dir}/homophones.json")

        # Build homophone lookup in both directions
        self.homophone_lookup = {}
        for word, variants in self.homophones.items():
            self.homophone_lookup[word] = set(variants)
            for variant in variants:
                if variant not in self.homophone_lookup:
                    self.homophone_lookup[variant] = set()
                self.homophone_lookup[variant].add(word)

        # Load spoonerisms
        self.spoonerisms = self._load_spoonerisms(f"{input_dir}/spoonerisms.json")

        # Build spoonerism lookup for faster matching
        self.spoonerism_lookup = {}
        for pattern in self.spoonerisms:
            original = tuple(pattern["original"])
            spoonerism = tuple(pattern["spoonerism"])
            self.spoonerism_lookup[spoonerism] = original

        # Create phonetic representations of harmful words for homophone detection
        self.harmful_phonetics = self._create_phonetic_mappings()

        # Context words that may indicate actual harmful intent
        self.context_harm_indicators = {
            "hate",
            "stupid",
            "ugly",
            "bad",
            "worst",
            "die",
            "death",
            "kill",
            "fuck",
            "shit",
            "damn",
            "hell",
            "idiot",
            "dumb",
            "worthless",
            "trash",
            "horrible",
        }

    def _load_harmful_words(self, file_path: str) -> Set[str]:
        """Load harmful words from a file"""
        harmful_words = set()
        try:
            with open(file_path, "r") as f:
                for line in f:
                    word = line.strip().lower()
                    if word and len(word) >= MIN_WORD_LENGTH:
                        harmful_words.add(word)
        except Exception as e:
            print(f"Error loading harmful words: {e}")
        return harmful_words

    def _load_char_substitutions(self, file_path: str) -> Dict[str, str]:
        """Load character substitution mappings from a JSON file"""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                return data.get("character_substitutions", {})
        except Exception as e:
            print(f"Error loading character substitutions: {e}")
            return {}

    def _create_reverse_substitutions(self) -> Dict[str, List[str]]:
        """Create a reverse lookup for character substitutions"""
        reverse_map = {}
        for char, replacement in self.char_substitutions.items():
            if replacement not in reverse_map:
                reverse_map[replacement] = []
            reverse_map[replacement].append(char)
        return reverse_map

    def _load_homophones(self, file_path: str) -> Dict[str, List[str]]:
        """Load homophone mappings from a JSON file"""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                return data.get("homophones", {})
        except Exception as e:
            print(f"Error loading homophones: {e}")
            return {}

    def _load_spoonerisms(self, file_path: str) -> List[Dict]:
        """Load spoonerism patterns from a JSON file"""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                return data.get("spoonerisms", [])
        except Exception as e:
            print(f"Error loading spoonerisms: {e}")
            return []

    def _create_phonetic_mappings(self) -> Dict[str, List[str]]:
        """Create phonetic representations of harmful words for homophone detection"""
        phonetic_map = {}
        for word in self.harmful_words:
            if len(word) < MIN_WORD_LENGTH:
                continue  # Skip very short words

            phonetics = doublemetaphone(word)
            for phonetic in phonetics:
                if phonetic:  # Skip empty strings
                    if phonetic not in phonetic_map:
                        phonetic_map[phonetic] = []
                    phonetic_map[phonetic].append(word)
        return phonetic_map

    def _normalize_text(self, text: str) -> str:
        """Replace character substitutions with their normal counterparts"""
        normalized = text.lower()
        for char, replacement in self.char_substitutions.items():
            normalized = normalized.replace(char, replacement)
        return normalized

    def _detect_context(self, words: List[str]) -> bool:
        """Detect if the context indicates harmful intent"""
        return any(word in self.context_harm_indicators for word in words)

    def _calculate_char_similarity(self, word1: str, word2: str) -> float:
        """Calculate character similarity between two words using Levenshtein distance

        The Levenshtein distance is a measure of the minimum number of single-character
        edits (insertions, deletions, or substitutions) required to change one word into
        another.
        """
        if not word1 or not word2:
            return 0.0

        # Simple Levenshtein distance implementation
        len1, len2 = len(word1), len(word2)

        # Early optimization: If lengths are very different, words are likely not similar
        if abs(len1 - len2) > 2:
            return 0.0

        # Initialize the distance matrix with dimensions (len1+1) x (len2+1)
        # Each cell [i,j] represents the edit distance between word1[:i] and word2[:j]
        d = [[0 for _ in range(len2 + 1)] for _ in range(len1 + 1)]

        # Initialize first row and column
        # The distance from empty string to a string of length i is i (i insertions)
        for i in range(len1 + 1):
            d[i][0] = i
        for j in range(len2 + 1):
            d[0][j] = j

        # Fill the matrix: calculate the minimum cost of operations to transform word1[:i] to word2[:j]
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                # If characters match, no additional cost from the previous state
                cost = 0 if word1[i - 1] == word2[j - 1] else 1

                # Choose the minimum cost operation (deletion, insertion, or substitution)
                d[i][j] = min(
                    d[i - 1][j]
                    + 1,  # deletion: transform word1[:i-1] to word2[:j], then delete
                    d[i][j - 1]
                    + 1,  # insertion: transform word1[:i] to word2[:j-1], then insert
                    d[i - 1][j - 1]
                    + cost,  # substitution/match: transform word1[:i-1] to word2[:j-1], then sub/match
                )

        # Convert Levenshtein distance to a similarity score (0 to 1)
        # Where 1 means identical and 0 means completely different
        max_len = max(len1, len2)
        if max_len == 0:
            return 1.0  # Both words empty, considered identical
        else:
            # The score is (1 - normalized_distance)
            return 1.0 - (d[len1][len2] / max_len)

    def _check_for_character_substitution(self, text: str) -> bool:
        """Check if the text contains character substitutions of harmful words"""
        # Normalize text first
        normalized_text = self._normalize_text(text)

        # Extract words
        words_raw = re.findall(r"\b\w+\b", normalized_text)
        words = [word for word in words_raw if len(word) >= MIN_WORD_LENGTH]

        # Check for matches of harmful words after normalization
        for word in words:
            # Optimization: Only check words of similar length
            word_len = len(word)
            possible_lengths = [word_len - 1, word_len, word_len + 1]

            for length in possible_lengths:
                if length in self.harmful_words_by_length:
                    for harmful_word in self.harmful_words_by_length[length]:
                        similarity = self._calculate_char_similarity(word, harmful_word)
                        if similarity >= CHAR_SUBSTITUTION_THRESHOLD:
                            # For non-exact matches, check for harmful context indicators
                            if word != harmful_word and not self._detect_context(
                                words_raw
                            ):
                                continue
                            return True

        return False

    def _calculate_phonetic_similarity(self, word1: str, word2: str) -> float:
        """Calculate phonetic similarity between words"""
        if not word1 or not word2:
            return 0.0

        phonetics1 = doublemetaphone(word1)
        phonetics2 = doublemetaphone(word2)

        # Check all combinations of phonetics
        max_similarity = 0.0
        for p1 in phonetics1:
            if not p1:
                continue
            for p2 in phonetics2:
                if not p2:
                    continue
                # Calculate similarity between phonetic codes
                len1, len2 = len(p1), len(p2)
                if not len1 or not len2:
                    continue

                # Simple matching coefficient: count matches divided by max length
                matches = sum(c1 == c2 for c1, c2 in zip(p1, p2))
                max_len = max(len1, len2)
                similarity = matches / max_len

                max_similarity = max(max_similarity, similarity)

        return max_similarity

    def _check_for_homophones(self, text: str) -> bool:
        """Check if the text contains homophones of harmful words"""
        words_raw = re.findall(r"\b\w+\b", text.lower())
        words = [word for word in words_raw if len(word) >= MIN_WORD_LENGTH]

        # First check direct homophone matches from our dictionary
        for word in words:
            # Check if this word is in our homophone lookup
            if word in self.homophone_lookup:
                for related_word in self.homophone_lookup[word]:
                    if related_word in self.harmful_words:
                        # Check for context indicators
                        if self._detect_context(words_raw):
                            return True

        # Then check using phonetic similarity for words not in our dictionary
        for word in words:
            if len(word) < MIN_WORD_LENGTH:
                continue

            # Check for phonetic similarity with harmful words
            for harmful_word in self.harmful_words:
                # Skip identical words (that's character substitution)
                if word == harmful_word:
                    continue

                similarity = self._calculate_phonetic_similarity(word, harmful_word)
                if similarity >= HOMOPHONE_SIMILARITY_THRESHOLD:
                    # Check for context indicators
                    if self._detect_context(words_raw):
                        return True

        return False

    def _check_for_spoonerisms(self, text: str) -> bool:
        """Check if the text contains spoonerisms of harmful phrases"""
        words = re.findall(r"\b\w+\b", text.lower())

        # Check for adjacent word pairs
        for i in range(len(words) - 1):
            word_pair = (words[i], words[i + 1])

            # Direct lookup in spoonerism dictionary
            if word_pair in self.spoonerism_lookup:
                original = self.spoonerism_lookup[word_pair]
                # Verify this is a true spoonerism of something harmful
                if any(orig_word in self.harmful_words for orig_word in original):
                    return True

            # Try to detect spoonerisms not in our dictionary
            # by checking if swapping initial sounds creates harmful words
            if len(words[i]) > 1 and len(words[i + 1]) > 1:
                # Extract initial sounds (first letter as approximation)
                sound1, sound2 = words[i][0], words[i + 1][0]

                # Create potential original words by swapping initial sounds
                potential_orig1 = sound2 + words[i][1:]
                potential_orig2 = sound1 + words[i + 1][1:]

                # Check if either potential original word is harmful
                if (
                    potential_orig1 in self.harmful_words
                    or potential_orig2 in self.harmful_words
                ):
                    return True

        return False

    def moderate_post(self, url: str) -> List[str]:
        """Apply moderation to detect linguistic evasion in the post"""
        try:
            post = post_from_url(self.client, url)
            post_text = post.value.text
            labels = []

            # If text is too short, likely not evasion
            if len(post_text.strip()) < 5:
                return labels

            # Apply detection methods
            char_sub_detected = self._check_for_character_substitution(post_text)
            homophone_detected = self._check_for_homophones(post_text)
            spoonerism_detected = self._check_for_spoonerisms(post_text)

            # Add appropriate labels
            if char_sub_detected:
                labels.append(CHAR_SUBSTITUTION_LABEL)

            if homophone_detected:
                labels.append(HOMOPHONE_LABEL)

            if spoonerism_detected:
                labels.append(SPOONERISM_LABEL)

            # If any evasion technique is detected, add the general label
            if labels:
                labels.append(LINGUISTIC_EVASION_LABEL)

            return labels
        except Exception as e:
            print(f"Error moderating post {url}: {e}")
            return []
