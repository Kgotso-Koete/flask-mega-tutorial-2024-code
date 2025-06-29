# Flask Mega Tutorial

## Getting Started

### Prerequisites

- Python 3.12.3
- Virtual environment (recommended)
- pip (Python package installer)

### Setting Up Virtual Environment

1. Create a virtual environment:

   ```bash
   python3 -m venv .venv
   ```

2. Activate the virtual environment:

   - On Linux/MacOS:
     ```bash
     source .venv/bin/activate
     ```
   - On Windows:
     ```
     .venv\Scripts\activate
     ```

3. Your command prompt should now show `(.venv)` at the beginning, indicating the virtual environment is active.

4. To deactivate the virtual environment when you're done, simply type:
   ```bash
   deactivate
   ```

### Installing Dependencies

With your virtual environment activated, install the required packages:

```bash
pip install -r requirements.txt
```

This will install all the necessary packages including:

- Flask 3.1.0
- Flask-SQLAlchemy 3.1.1
- Flask-Migrate 4.1.0
- Flask-WTF 1.2.2
- And other required dependencies

Dump a list pf installed packages using the command:

```bash
pip freeze > requirements.txt
```


### Run database migrations

Migrate any database changes with the following:

```bash
flask db migrate -m "<insert your comment here>"
```

Upgrade the database to commit the changes:

```bash
flask db upgrade
```

## Debugging email serverr

Run `aiosmtpd -n -c aiosmtpd.handlers.Debugging -l localhost:8025` if debug is set to 0.

## Tutorial

Chapter 1 [pdf file](./tutorial/chapter-1.pdf) and [YouTube](https://youtu.be/9FBDda0NCwo)
