# Installation
## environment installation
- install poetry if it's not in your environment (see [python-poerty/poerty](https://github.com/python-poetry/poetry))
- use [pyenv](https://github.com/pyenv/pyenv) or [conda](https://github.com/conda/conda) to create a virtual environment of python version=3.8 (env name=pr-latency-bot, we will use this environment name in the following text)
- install [mysql](https://dev.mysql.com/downloads/installer/) and create a database (here we name the database pr-latency-bot)

## run commands to start the program
### 1. install python dependencies
```
git clone https://github.com/PR-bots/PR-latency-bot.git
cd PR-latency-bot
conda activate pr-latency-bot
poetry install
poetry shell
```

### 2. migrate database
- change the configuration of your mysql database in .env.yaml file ("MYSQL" part)
- run the following commands to create tables in the target database
```
alembic upgrade head
```

### 3. run the service
- create a [new GitHub App](https://github.com/organizations/PR-bots/settings/apps/new) on GitHub web page according to the [instruction](https://docs.github.com/en/developers/apps/building-github-apps/creating-a-github-app).
  - set the "Webhook URL" to your service url+port
  - set repository permissions as follows:
    - Contents: Read-only
    - Discussions: Read-only
    - Metadata: Read-only
    - Pull requests: Read & write
  - subscribe to events:
    - Pull request
  - set the access of your GitHub App
    - Only on this account: create your own private App
    - Any account: create a public App
  - [optional] after creating your App, you can set the Display information by uploading a logo of your App
  - generate your own private key of your GitHub App (see [GitHub Doc](https://docs.github.com/en/developers/apps/building-github-apps/authenticating-with-github-apps#generating-a-private-key)), and download it to your own path.
- change the configuration of your installed App on GitHub in .env.yaml file ("APP" part)
  - change "APP_SLUG" according to your own settings, see [GitHub Doc](https://docs.github.com/en/rest/reference/apps#get-an-app) for more information.
  - change "PRIVATE_KEY_PATH" according to the path you store your private key (pem file).
  - change "PERSONAL_TOKEN" according to [GitHub Doc](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token#creating-a-token). Here it uses the personal token just for the initialization of service, as the APP_ID will change if you change the setting of your own deployed App. Therefore, it just uses the token to access your current APP_ID. (The personal token is the token of whom your App is created by. For organization accounts, please use the token of the member that is allowed to manage all GitHub Apps belonging to this organization.)
- change the configuration of the pull request latency making service in .env.yaml file ("SERVICE" part).
  - change the port ("PORT") of your service.
  - change the number of hours of "REMIND_EVERY_HOURS". This means how often do you want your pull requests receive the remind message.
  - change the number of hours needed for scheduler ("SCHEDULER") to cycle ("CYCLE_MINUTES"). This represents how often does the background scheduler run for 1-round check.
- start the service using the following commands (for windows server, you need to write your own shell). It will take some time for the training of the model. If your server's performance is not good, try running command ```python app/prediction_service/trainer.py``` and train the model at somewhere else before the start of the service.
```
poetry shell
bash pr-latency-bot.sh start
```
- stop/restart the service using the following commands (for windows server, you need to write your own shell):
```
bash pr-latency-bot.sh stop
bash pr-latency-bot.sh restart
```

### 4. install your GitHub App
find your app through your app's public link and install it to your target personal/organization account that want to use the app.

## That's it! You can use your own App now! Good luck!