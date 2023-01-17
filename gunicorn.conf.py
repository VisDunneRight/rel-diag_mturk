import os
from dotenv import load_dotenv


env = os.path.join(os.getcwd(), '.env.production')
print(env)
if os.path.exists(env):
    load_dotenv(env)