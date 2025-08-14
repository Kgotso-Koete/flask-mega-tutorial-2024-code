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

## Running the app as a Docker container

1. Command to run the mySQL server

```bash
docker run --name mysql -d -e MYSQL_RANDOM_ROOT_PASSWORD=yes \
    -e MYSQL_DATABASE=microblog -e MYSQL_USER=microblog \
    -e MYSQL_PASSWORD=<database-password> \
    --network microblog-network \
    mysql:latest
```

2. Command to run the Elastic Search server

```bash
docker run --name elasticsearch -d --rm -p 9200:9200 \
    -e discovery.type=single-node -e xpack.security.enabled=false \
    --network microblog-network \
    -t docker.elastic.co/elasticsearch/elasticsearch:8.11.1
```

3. Command to run the Flask application

```bash
docker run --name microblog -d -p 8000:5000 --rm -e SECRET_KEY=my-secret-key \
    -e MAIL_SERVER=smtp.googlemail.com -e MAIL_PORT=587 -e MAIL_USE_TLS=true \
    -e MAIL_USERNAME=<your-gmail-username> -e MAIL_PASSWORD=<your-gmail-password> \
    --network microblog-network \
    -e DATABASE_URL=mysql+pymysql://microblog:<database-password>@mysql/microblog \
    -e ELASTICSEARCH_URL=http://elasticsearch:9200 \
    microblog:latest
```

## Tutorial

Chapter 1 [pdf file](./tutorial/chapter-1.pdf) and [YouTube](https://youtu.be/9FBDda0NCwo)
