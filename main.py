#%%

from functions import utils
from google import generativeai as genai

import warnings
from tqdm import TqdmExperimentalWarning

warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)


creds_folder = r'C:\Users\guilherme.luz.NETSHOES\Desktop\codes\Credentials'

gemini = utils.get_credentials(creds_folder,"GEMINI")

with open(gemini,'r') as key:
    gem = key.read().strip()

genai.configure(api_key=gem)

model = genai.GenerativeModel('gemini-1.5-flash')

response = model.generate_content(
    contents="Are you alive?"
)

print(response.text)






#%%