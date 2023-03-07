# HODL

## Pre-requirements
Python3 and pip installed

## Database Setup
#### Use local database:
In HODL/settings.py, DATABASE section, uncomment sqlight3 database details. Comment out postgresql database detail.  

#### Use AWS postgresql database:
In HODL/settings.py, DATABASE section, comment out sqlight3 database details. Uncomment out postgresql database detail. Create an .env file in the same directory as setting.py, store database variables there.  

## To run the project
run command below to install dependencies\
pip install -r requirements.txt 

run command below to migrate database \
python3 manage.py makemigrations \
python3 manage.py migrate

run command below to run the project\
python3 manage.py runserver 
