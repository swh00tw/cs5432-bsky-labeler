# Setup

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
