# Trader's Arena
Management Portal for FinCom's signature event: Trader's Arena.

## Setup
Create a `.env` file in the root directory containing the following variables:
- `SQLALCHEMY_DATABASE_URI`: The Database URI for SQLAlchemy.
- `USERS`: A comma separated list of usernames that can access the portal.
- `PASSWORD`: The password for all users. Right now there will just be a single password for all users.