from pathlib import Path
from dotenv import load_dotenv
import os

root_env = Path(__file__).resolve().parent / ".env"
venv_env = Path(__file__).resolve().parent / ".venv" / ".env"
print('root_env', root_env.exists(), root_env)
print('venv_env', venv_env.exists(), venv_env)
load_dotenv(root_env)
print('after root load BOT_TOKEN=', os.getenv('BOT_TOKEN'))
load_dotenv(venv_env, override=True)
print('after venv load BOT_TOKEN=', os.getenv('BOT_TOKEN'))
print('ADMIN_IDS=', os.getenv('ADMIN_IDS'))
print('ADMIN_ID=', os.getenv('ADMIN_ID'))
