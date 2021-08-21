from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

from app.utils.config_loader import ConfigLoader

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from app.db.tables import sqlalchemy_orm
target_metadata = sqlalchemy_orm.Base.metadata

env = ConfigLoader().load_env()
connection_url = "mysql+pymysql://{user}:{password}@{host}:{port}/{db}".format(user=env["MYSQL"]["USER"], password=env["MYSQL"]["PASSWORD"], host=env["MYSQL"]["HOST"], port=env["MYSQL"]["PORT"], db=env["MYSQL"]["DB"])
config.set_main_option("sqlalchemy.url", connection_url) # we need to add this in main option, because the configuration of sqlalchemy.url is in .env.yaml, not in alembic.ini

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
