# Inventory Management System

# [IMS API](https://github.com/Moshood-Wale/ims-api.git)

## Technologies

* [Python 3.9](https://python.org) : Base programming language for development
* [Bash Scripting](https://www.codecademy.com/learn/learn-the-command-line/modules/bash-scripting) : Create convenient script for easy development experience
* [PostgreSQL](https://www.postgresql.org/) : Application relational databases for development, staging and production environments
* [Django Framework](https://www.djangoproject.com/) : Development framework used for the application
* [Django Rest Framework](https://www.django-rest-framework.org/) : Provides API development tools for easy API development
* [Github Actions](https://docs.github.com/en/free-pro-team@latest/actions) : Continuous Integration and Deployment
* [Docker Engine and Docker Compose](https://www.docker.com/) : Containerization of the application and services orchestration

## Description

- Product creation, deletion, update and retrieval.
- Adding product to cart and purchasing product
- Keeping track of product quantity in regards to purchase or add to cart functions, i.e the product quantity should reduce when a purchase is made, or when it is added to the "user's" cart; users should be informed when a product is "out of stock"
- Products should have (name, category, labels(e.g size, colour etc), quantity, price) A product can have one or more labels.

## Getting Started

Getting started with this project is very simple, all you need is to have Git and Docker Engine installed on your machine. Then open up your terminal and run this command `git clone https://github.com/Moshood-Wale/ims-api.git` to clone the project repository.

Change directory into the project folder `cd ims-api` and build the base python image used for the project that was specified in ***dockerfile*** by running ` docker build . ` *Note the dot (.) at end of the command*.

Spin up other services needed for the project that are specified in ***docker-compose.yml*** file by running the command `docker-compose up`. At this moment, your project should be up and running with a warning that *you have unapplied migrations*.

Open up another terminal and run this command `docker-compose exec api python app/manage.py makemigrations` for creating new migrations based on the models defined and also run `docker compose exec api python app/manage.py migrate` to apply migrations.

In summary, these are the lists of commands to run in listed order, to start up the project.

```docker
1. git clone https://github.com/Moshood-Wale/ims-api.git
2. cd ims-api
3. docker build .
4. docker-compose up
5. docker-compose exec api python app/manage.py makemigrations
6. docker-compose exec api python app/manage.py migrate
```
Once the project is up and running, kindly find the url to the Swagger documentation in the urls.py file of the project(core).
