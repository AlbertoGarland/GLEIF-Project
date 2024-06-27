import os

APP_ENTRY_POINT = 'main.py'

dir_path = os.path.dirname(__file__)
path = os.path.join(dir_path, APP_ENTRY_POINT)

os.system('streamlit run "{}"'.format(path))
