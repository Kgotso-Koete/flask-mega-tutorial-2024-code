# Welcome to Microblog!

This is a personal implementation of the Flask Mega-Tutorial by Miguel Grinberg. This project follows along with the tutorial to build a microblogging application using Flask, SQLAlchemy, and other modern web technologies.

## About the Tutorial

The [Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world) is a comprehensive tutorial series that teaches web development using the Flask framework. The tutorial covers everything from basic routing to advanced features like full-text search, background jobs, and deployment.

PDF versions of each chapter are available in the `tutorial/` directory of this repository.

## Special Thanks and Acknowledgments

Huge thanks to [Miguel Grinberg](https://blog.miguelgrinberg.com/) for creating and maintaining this excellent tutorial. His clear explanations and practical examples have been invaluable in learning Flask and web development best practices.

- Original tutorial: [Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)
- Original repository: [github.com/miguelgrinberg/microblog](https://github.com/miguelgrinberg/microblog)

# Flask Mega Tutorial

## Getting Started

### Prerequisites

- Python 3.12.3
- Virtual environment (recommended)
- pip (Python package installer)
- Docker (for running Elasticsearch)
- Ubuntu 24.04.3 LTS (or any other Linux distribution)

Requirements for Heroku

- psycopg2-binary==2.9.9
- gunicorn==21.2.0

---

### How to run this application locally

You can run the application by executing these 6 steps manually using the instructions from the README, or by executing the `complete-setup.sh` script.

1. Set up the Python virtual environment
2. Install packages within the virtual environment
3. Run database migrations
4. Set up background tasks (post exports) with Redis
5. Run the Elastic Search server within a Docker container
6. Run the application
7. Visit the application at `http://localhost:5000`

You can run the application by executing the `complete-setup.sh` script (originally used onUbuntu 24.04.3 LTS). Please read the scrips before executing them because they will make changes to your system such as (re)installing Redis and Elastic Search (via Docker).

Make the automation scripts executable:

```bash
chmod +x complete-setup.sh
chmod +x start-worker.sh
```

Run steps 1 to 6 by executing the following commands:

```bash
./complete-setup.sh
```

Run the background Redis cue in a separate window:

```bash
./start-worker.sh
```

---

### 1.Set up the Python virtual environment

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

### 2. Install packages within the virtual environment

Install necessary packages using the following command in a virtual environment terminal:

```bash
pip install -r requirements.txt
```

--

### 3. Run database migrations

Please run step and and 2 of the following commands to migrate the database before you first run the application.

After making any changes to the database models, you'll need to create and apply the same migrations:

1. Create a new migration (after modifying your models):

   ```bash
   flask db migrate -m "Description of changes"
   ```

2. Apply the migration to update your database:

   ```bash
   flask db upgrade
   ```

3. To check the current database revision:

   ```bash
   flask db current
   ```

4. To rollback the last migration:
   ```bash
   flask db downgrade
   ```

---

### 4. Set up background tasks (post exports) with Redis

This project uses Redis for task queue management. Follow these steps to set up Redis:

1. Install Redis server:

   ```bash
   sudo apt update
   sudo apt install redis-server
   ```

2. Start the Redis service:

   ```bash
   sudo systemctl start redis
   ```

3. (Optional) To enable Redis to start on boot:

   ```bash
   sudo systemctl enable redis
   ```

4. Verify Redis is running:

   ```bash
   redis-cli ping
   ```

   You should see `PONG` as the response.

5. Install the Python Redis client:

   ```bash
   pip install redis
   ```

6. Start the RQ worker in a separate terminal where the virtual environment is ACTIVATED (leave it running):
   ```bash
   rq worker microblog-tasks
   ```

---

### 5. Run the Elastic Search server within a Docker container

Follow these steps to run the Elastic Search server within a Docker container:

```bash
   # Stop any existing Elasticsearch container
   docker stop elasticsearch

   # Remove any problematic data (optional but recommended for development)
   docker volume prune -f

   # Start Elasticsearch with optimized settings
   docker run --name elasticsearch -d --rm -p 9200:9200 \
   --memory="4GB" \
   -e discovery.type=single-node \
   -e xpack.security.enabled=false \
   -e ES_JAVA_OPTS="-Xms2g -Xmx2g" \
   -e xpack.security.enrollment.enabled=false \
   -e cluster.routing.allocation.disk.threshold_enabled=false \
   -e bootstrap.memory_lock=true \
   --ulimit memlock=-1:-1 \
   -t docker.elastic.co/elasticsearch/elasticsearch:8.11.1

   # Wait for startup (30-60 seconds), then verify health
   sleep 30
   curl -X GET "http://localhost:9200/_cluster/health"
```

Index the posts:

```bash
   # In a terminal where your virtual environment is activated:
flask shell
>>> from app.models import Post
>>> Post.reindex()
>>> exit()
```

---

### 6. Run the application

Follow these steps to run the Flask application:

```bash
   flask run
```

---

### Heroku Redis Setup

For production deployment on Heroku, use the Heroku Redis add-on:

1. Add the Heroku Redis add-on (mini plan, which is the most cost-effective):

   ```bash
   heroku addons:create heroku-redis:mini
   ```

   Note: The mini plan is free for development but has limitations. For production, consider a higher plan.

2. The Redis URL will be automatically set in the `REDIS_URL` config var in Heroku.

3. The RQ worker will automatically use the Heroku Redis instance when deployed.

4. To check the Redis connection status:
   ```bash
   heroku redis:info -a your-app-name
   ```

- Flask 3.1.0
- Flask-SQLAlchemy 3.1.1
- Flask-Migrate 4.1.0
- Flask-WTF 1.2.2
- And other required dependencies

Dump a list pf installed packages using the command:

```bash
pip freeze > requirements.txt
```

## Debugging email serverr

Run `aiosmtpd -n -c aiosmtpd.handlers.Debugging -l localhost:8025` if debug is set to 0.

## Running the app as a Docker container

Any time a change is made to the application or the Dockerfile, the container image needs to be rebuilt:

```bash
docker build -t microblog:latest .
```

1. Command to run the MySQL server:

```bash
docker run --name mysql -d -e MYSQL_RANDOM_ROOT_PASSWORD=yes \
    -e MYSQL_DATABASE=microblog -e MYSQL_USER=microblog \
    -e MYSQL_PASSWORD=<database-password> \
    --network microblog-network \
    mysql:latest
```

2. Command to run the Redis server:

```bash
docker run --name redis -d -p 6379:6379 \
    --network microblog-network \
    redis:latest
```

3. Command to run the Elasticsearch server:

```bash
docker run --name elasticsearch -d --rm -p 9200:9200 \
    -e discovery.type=single-node -e xpack.security.enabled=false \
    --network microblog-network \
    -t docker.elastic.co/elasticsearch/elasticsearch:8.11.1
```

4. Command to run the Flask application:

```bash
docker run --name microblog -d -p 8000:5000 --rm -e SECRET_KEY=my-secret-key \
    -e MAIL_SERVER=smtp.googlemail.com -e MAIL_PORT=587 -e MAIL_USE_TLS=true \
    -e MAIL_USERNAME=<your-gmail-username> -e MAIL_PASSWORD=<your-gmail-password> \
    --network microblog-network \
    -e DATABASE_URL=mysql+pymysql://microblog:<database-password>@mysql/microblog \
    -e ELASTICSEARCH_URL=http://elasticsearch:9200 \
    -e REDIS_URL=redis://redis:6379/0 \
    -e MS_TRANSLATOR_KEY=<paste-your-key-here> \
    microblog:latest
```

5. Run the RQ worker in a separate terminal:

```bash
docker run --name rq-worker -d --rm -e SECRET_KEY=my-secret-key \
    -e MAIL_SERVER=smtp.googlemail.com -e MAIL_PORT=587 -e MAIL_USE_TLS=true \
    -e MAIL_USERNAME=<your-gmail-username> -e MAIL_PASSWORD=<your-gmail-password> \
    --network microblog-network \
    -e DATABASE_URL=mysql+pymysql://microblog:<database-password>@mysql/microblog \
    -e REDIS_URL=redis://redis:6379/0 \
    --entrypoint venv/bin/rq \
    microblog:latest worker -u redis://redis:6379/0 microblog-tasks
```

Note: The RQ worker command overrides the default container entrypoint to run the RQ worker instead of the web application. The worker needs access to the same code and environment variables as the main application to process background tasks.

## Heroku Deployment Notes

### Add-ons

This application uses the following Heroku add-ons. You can list them using:

```bash
heroku addons
```

### Elasticsearch Version Compatibility

**Important Note on Elasticsearch Versions:**

There is a known issue with SearchBox (Heroku's Elasticsearch add-on) and Elasticsearch versions. The most recent version of Elasticsearch that can be used with SearchBox is 7.x, while this project was developed using the Python module version 8.11.

#### Fix for SearchBox Compatibility:
1. Downgrade the following dependencies to version 7.x:
   - elasticsearch
   - elastic-transport
   - urllib3 (to version <2.0.0)

2. Use Elasticsearch 7 for local development with Docker
3. Update the Elasticsearch parameters in `search.py` to match v7 style

This is due to major changes in Elastic's licensing with v8, which affects SearchBox's ability to release their own versioning of the tool.

Related GitHub issue: [elastic/elasticsearch-ruby#1429](https://github.com/elastic/elasticsearch-ruby/issues/1429)

### Current Add-ons Configuration:

```
Add-on            Plan        Price        Max price State
───────────────── ─────────── ──────────── ───────── ───────
heroku-postgresql essential-0 ~$0.007/hour $5/month  created
 └─ as DATABASE

heroku-redis      mini        ~$0.004/hour $3/month  created
 └─ as REDIS

searchbox         starter     free         free      created
 └─ as SEARCHBOX
```

To check detailed information about any add-on, use:

```bash
heroku addons:info heroku-redis  # For Redis
heroku addons:info heroku-postgresql  # For PostgreSQL
```

### more on the Elasticsearch Setup

#### Quick Start

To run Elasticsearch for this application:

```bash
# Stop any existing Elasticsearch container
docker stop elasticsearch

# Remove any problematic data (optional but recommended for development)
docker volume prune -f

# Start Elasticsearch with optimized settings
docker run --name elasticsearch -d --rm -p 9200:9200 \
  --memory="4GB" \
  -e discovery.type=single-node \
  -e xpack.security.enabled=false \
  -e ES_JAVA_OPTS="-Xms2g -Xmx2g" \
  -e xpack.security.enrollment.enabled=false \
  -e cluster.routing.allocation.disk.threshold_enabled=false \
  -e bootstrap.memory_lock=true \
  --ulimit memlock=-1:-1 \
  -t docker.elastic.co/elasticsearch/elasticsearch:8.11.1

# Wait for startup (30-60 seconds), then verify health
sleep 30
curl -X GET "http://localhost:9200/_cluster/health"
```

#### Environment Configuration

Add to your `.env` file:

```bash
ELASTICSEARCH_URL=http://localhost:9200
```

#### Troubleshooting

##### If Elasticsearch cluster shows "red" status:

1. **Check cluster health:**

   ```bash
   curl -X GET "http://localhost:9200/_cluster/health"
   ```

2. **Restart with fresh data:**
   ```bash
   docker stop elasticsearch
   docker volume prune -f
   # Run the startup command above
   ```

##### If posts save slowly or search fails:

- Elasticsearch is likely in red status or not responding
- Follow the restart procedure above
- Temporarily disable search by commenting out `ELASTICSEARCH_URL` in `.env`

#### Alternative: Use Stable Version

If issues persist, try Elasticsearch 7.17:

```bash
docker stop elasticsearch

docker run --name elasticsearch -d --rm -p 9200:9200 \
  --memory="2GB" \
  -e discovery.type=single-node \
  -e xpack.security.enabled=false \
  -e ES_JAVA_OPTS="-Xms1g -Xmx1g" \
  -t docker.elastic.co/elasticsearch/elasticsearch:7.17.0
```

#### Memory Requirements

- **Minimum**: 4GB total system RAM (2GB for Elasticsearch)
- **Recommended**: 8GB+ total system RAM for development

#### Verification Commands

```bash
# Check if container is running
docker ps

# Check cluster health (should show "green" status)
curl -X GET "http://localhost:9200/_cluster/health"

# Check Elasticsearch info
curl -X GET "http://localhost:9200"

# View container logs
docker logs elasticsearch
```

### Tutorial

Chapter 1 [pdf file](./tutorial/chapter-1.pdf) and [YouTube](https://youtu.be/9FBDda0NCwo)
