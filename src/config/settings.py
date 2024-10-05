import os

app_name = "API Nationaal wegenbestand"
app_version = "0.6.3"

DOCS_FAVICON = "/static/favicon.svg"

# configure "Servers" dropdown in Swagger UI
AUTO_SERVERS = False
SERVERS = [
    {
        "name": app_name,
        "url": os.environ.get("API_ROOT_URL"),
    }
]

SECRET_KEY = os.environ.get("APP_SECRET")
PREFERRED_URL_SCHEME = "https"

DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PWD = os.environ.get("DB_PWD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_SSL = os.environ.get("DB_SSL")
