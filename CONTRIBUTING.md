# Contributing
When contributing to this repository, please first discuss the change you wish to make via issue before making a change.

Please note we have a code of conduct, please follow it in all your interactions with the project.

## How to run the project

### Prerequisites
This project is built to be run with `docker` and `docker-compose` due to relying on services such as postgres, grafana and prometheus. How ever, it is possible to run the project without docker, but you will have to have postgres, grafana and prometheus hosts. There is no current documentation of how to configure promethues or grafana.

Project has `requirements.txt` for dependencies related to the project and `requirements-dev.txt` for development dependencies. You can install them with `pip install -r requirements.txt` and `pip install -r requirements-dev.txt` respectively.

### Running backend with docker
1. Clone the repository
2. Move into the project directory
3. Create a new file to the root of project called `.env` and copy content of `.env-template` in there. You can  leave the database variables as they are if you wish to. In which case the database username will be `admin`, the password will be `admin` and database name will be set to `lemonapi`
4. Run `docker compose up --build` to build and run the project.
5. You should now be able access the api at `http://localhost:5001/docs` or `http://127.0.0.1:5001/docs`
6. You can shutdown the container by running `docker compose stop`

### Accessing metrics
Metrics services when ran locally are located in:
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

Login to grafana with credentils `admin:pass@123`. Follow the pictures in `metrics/images` for general idea of how to set it up.

This project comes with pre-made grafana dashboard that you can find in metrics/dashboard.json. There are some images in metrics/images on how to start the dashboard and how to configure it correctly. 

### Credentials
There are some default credentials for backend and grafana
##### Grafana
- Username: admin
- Password: pass@123

##### Backend
- Username: admin
- Password: weakadmin

##### PostgreSQL database
- Username: admin
- Password: admin

### Running backend without docker locally
1. Clone the repository
2. Move into the project directory
3. Install the dependencies with `pip install -r requirements.txt`
4. Modify the `.env` variables to match the ones in `.env-template`. You can  leave the database variables as they are if you wish to.
4. Modify the `lemonapi/utils/database.py` file section with `DB_URL` and modify the host part being after `@` sign to match your postgres host. You can leave the default values in `.env` as 
   they are if you wish to In which case the database username will be `admin`, the password will be `admin` and database name will be set to `lemonapi`.
   You can also pass whole connection string there.
6. All variables should be now set. Run the project with `uvicorn lemonapi.main:app --host=0.0.0.0 --port=5001 --log-level=info`
7. You should now be able access the api at `http://localhost:5001/docs` or `http://127.0.0.1:5001/docs`


## Pull Request Process

1. It's good practice to open an issue before making a pull request. This allows us to discuss the
   changes you wish to make, and to ensure that the changes are in line with the goals of the
   project. You may open a PR without an issue as well, but it may take longer for the PR to be
   reviewed. If possible, get an approval before making a PR.
2. Describe the changes you have made in the Pull Request. If you are adding a new feature, please
   include a description of the feature, and how it works. If you are fixing a bug, please include
   a description of the bug, and how you fixed it. Remember to write good commit messages that can
   be easily understood by others.
3. Remember to write clean and understandable code. This includes writing good commit messages, and using
   descriptive variable names. All checks of pre-commit hooks should pass before making a PR.
4. Update the README.md with details of changes to the interface, this includes new environment
   variables, exposed ports, useful file locations and container parameters.
5. You may merge the Pull Request in once the PR is reviewed and approved by the project owners, or
   if you do not have permission to do that, you may request the project owners to merge it for you.

## Code of Conduct

### Our Pledge

In the interest of fostering an open and welcoming environment, we as
contributors and maintainers pledge to making participation in our project and
our community a harassment-free experience for everyone, regardless of age, body
size, disability, ethnicity, gender identity and expression, level of experience,
nationality, personal appearance, race, religion, or sexual identity and
orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment
include:

* Using welcoming and inclusive language
* Being respectful of differing viewpoints and experiences
* Gracefully accepting constructive criticism
* Focusing on what is best for the community
* Showing empathy towards other community members

Examples of unacceptable behavior by participants include:

* The use of sexualized language or imagery and unwelcome sexual attention or
advances
* Trolling, insulting/derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or electronic
  address, without explicit permission
* Other conduct which could reasonably be considered inappropriate in a
  professional setting

### Our Responsibilities

Project maintainers are responsible for clarifying the standards of acceptable
behavior and are expected to take appropriate and fair corrective action in
response to any instances of unacceptable behavior.

Project maintainers have the right and responsibility to remove, edit, or
reject comments, commits, code, wiki edits, issues, and other contributions
that are not aligned to this Code of Conduct, or to ban temporarily or
permanently any contributor for other behaviors that they deem inappropriate,
threatening, offensive, or harmful.

### Scope

This Code of Conduct applies both within project spaces and in public spaces
when an individual is representing the project or its community. Examples of
representing a project or community include using an official project e-mail
address, posting via an official social media account, or acting as an appointed
representative at an online or offline event. Representation of a project may be
further defined and clarified by project maintainers.


### Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage]

[homepage]: http://contributor-covenant.org
