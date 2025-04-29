import os
# from . import logger
import shutil
import re

def get_credentials(creds_dir, credential):
    try:
        credential = credential + '.json'
        full_path = os.path.join(creds_dir, credential) 

        if os.path.exists(full_path):
            # logger.info(f'Credencial {credential} capturada.')
            print(f'Credencial {credential} capturada.')
            return full_path
        else:
            # logger.info(f'A credencial {credential} não existe no diretório {creds_dir} fornecido.')
            print(f'A credencial {credential} não existe no diretório {creds_dir} fornecido.')
        
    except Exception as e:
        # logger.error(f'Erro ao capturar as credenciais: {e}')
        print(f'Erro ao capturar as credenciais: {e}')
