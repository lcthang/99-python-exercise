# Backend Tech Challenge
An exercise to assess your skills with Python, [Tornado](http://tornadoweb.org/) (Web Framework), writing non-blocking/asynchronous code, and microservices architecture.

## Architecture
- listing_service.py: listing microservice
- user_service.py: user microservice
- public_api.py: API gateway for external parties
- listings.db: db for listing microservice
- users.db: db for user microserivce

## Setup
Setup in Windows:
```bash
# Locate the path for the Python 3 installation
C:\Python3

# Create the virtual environment in a folder named "env" in the current directory
virtualenv -p C:\Python3\python.exe env

# Start the virtual environment
env\Scripts\activate

# Install the required dependencies/libraries
pip install -r python-libs.txt
```

### Run services
```bash
# Run the listing service
python listing_service.py

# Run the user service
python user_service.py

# Run the public api
python public_api.py
```

## Author: Le Cong Thang (Terence Le)
