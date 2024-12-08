# Little Red Bandwagon Podcast Feed Parser

This Python application processes a live version or a saved version of the "Little Red Bandwagon" podcast feed.

The application generates an HTML file under `/output` that contains a table with each episode title, publish date, description and length.

## Requirements

This project requires Python 3.10 or higher.

## Installing Dependencies

It is highly recommended that you set up a virtual environment for this project and install the dependencies within the virtual environment. The following example uses Python's `venv` module to create the virtual environment, once a copy of this repository as been cloned locally.

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Running the Application

To run the application, activate the virtual environment if one was created, then run the following command:

```bash
python3 parser.py
```

## Development

Use the included `requirements-dev.txt` to install both the application and development dependencies.

For code linting and formatting, the project makes use of Ruff and Black.

## Code of Conduct

This project follows version 2.1 of the [Contributor Covenant's](https://www.contributor-covenant.org) Code of Conduct.

## License

This project is licensed under the terms of the [MIT License](LICENSE).
