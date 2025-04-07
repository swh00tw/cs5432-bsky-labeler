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

To run python file, run the following command:

```bash
uv run main.py
```

## Environment Variables

After cloning the repository, you need to create a `.env` file in the root directory. Please run

```bash
cp .env.example .env
```

Then, you need to fill in the `.env` file with your own environment variables.
