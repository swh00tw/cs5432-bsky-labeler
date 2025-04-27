# Bsky Linguistic Evasion Labler

## Setup

This project is mainly managed by [`uv`](https://docs.astral.sh/uv/) (for JavaScript part, it's managed by [`npm`](https://www.npmjs.com/)), which is the fastest package manager for python now. It will automatically setup virtual environment for you and install all the dependencies. You can install it by running the following command:

Please install `uv` on your machine first. (Installation guide: [https://docs.astral.sh/uv/#installation](https://docs.astral.sh/uv/#installation))

To install all python dependencies, run the following command:

```bash
uv sync
```

To install all JavaScript dependencies, run the following command:

```bash
npm install
```

To run any python file, run the following command:

```bash
# use this to replace running `python3 path/to/python/file.py` to automatically activate virtual environment
# so that we don't have to worry about dependencies
uv run path/to/python/file.py
```

## Environment Variables

After cloning the repository, you need to create a `.env` file in the root directory. Please run

```bash
cp .env.example .env
```

Then, you need to fill in the `.env` file with your own environment variables.

After adding environment variables, you can run the following command to check if everything is working fine:

```bash
uv run src/get_post_test.py
```

## How to collect more testing data?

To collect more evasion posts:

1. Tweak the keywords in `SEARCH_TERMS` in `src/test-data/collect_evasion_test_data.py`
2. Run the script via `uv run src/test-data/collect_evasion_test_data.py`

Notes:

- This script will append posts crawled from Bluesky which match the "search term" and append the (url, ground_truth_labels) to testing dataset `linguistic_evasion_test_posts.csv`.

The `SEARCH_TERMS` look like this:

```py
SEARCH_TERMS = {
    "character-substitution": [
        "a",
        # ...
    ],
    "homophone": [
        "b",
        # ...
    ],
    "spoonerism": [
        "d",
        # ...
    ],
}
```

- The script will use ATProto's API to find posts contain `"a"` and apply a label `"character-substitution"`, and find posts contain `"b"` and apply a label `"homophone"`, and find posts contain `"c"` and apply a label `"spoonerism"`. And for each evasion posts, also apply a general label `"linguistic-evasion"`.

To collect normal posts:

1. Run the script via `uv run src/test-data/collect_normal_posts.py`

It will append testing data to the dataset `linguistic_evasion_test_posts.csv`.

## Test & Evaluation

To know the accuracy and how well the labeler in `policy_proposal_labeler.py` run on our dataset. Run:
`uv run src/comprehensive_evaluation.py`

It will take a few minutes to complete. Once complete, you will see the accuracy, precision, and recall.
