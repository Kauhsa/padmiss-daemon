import json
import os
import sys
import logging
from typing import Union, List, Optional
from enum import Enum
from pydantic import BaseModel, UrlStr, DirectoryPath, Schema

log = logging.getLogger(__name__)

class ScannerConfig(BaseModel):
    id_vendor: str
    id_product: str
    port_number: Optional[int]
    bus: Optional[int]

class FifoConfig(BaseModel):
    path: str

class DeviceConfig(BaseModel):
    path: str
    type: str
    config: Optional[ScannerConfig]
    fifo_config: Optional[FifoConfig]

class PadmissConfig(BaseModel):
    padmiss_api_url: UrlStr
    api_key: str
    scores_dir: str
    backup_dir: str
    profile_dir_name: str
    hide_on_start: bool
    webserver: Optional[bool]
    devices: List[DeviceConfig]

class PadmissConfigManager(object):
    changed = []

    def hasValidConfig(self):
        path = self._get_config_path()
        return os.path.isfile(path)

    def __init__(self, custom_config_file_path=None):
        self._custom_config_file_path = custom_config_file_path

    def _get_path_inside_padmiss_dir(self, *path):
        if os.name == 'nt':
            return os.path.join(os.getenv('APPDATA'), 'Padmiss', *path)
        else:
            return os.path.join(os.path.expanduser('~'), '.padmiss', *path)

    def _get_default_config(self):
        return PadmissConfig(
            padmiss_api_url='https://api.padmiss.com/',
            api_key='',
            scores_dir='',
            backup_dir=self._get_path_inside_padmiss_dir('backups'),
            profile_dir_name='StepMania 5',
            hide_on_start=False,
            webserver=False,
            devices=[]
        )

    def _get_config_path(self):
        if self._custom_config_file_path is not None:
            return self._custom_config_file_path

        return self._get_path_inside_padmiss_dir('config.json')

    def _create_initial_directories_if_necessary(self):
        if self._custom_config_file_path is not None:
            return

        initial_dirs = [
            self._get_path_inside_padmiss_dir(),
            self._get_path_inside_padmiss_dir('backups')
        ]

        root_config_path = self._get_path_inside_padmiss_dir()

        if not os.path.isdir(root_config_path):
            for dir_to_create in initial_dirs:
                log.info('Directory "%s" does not exist, creating', dir_to_create)
                os.makedirs(dir_to_create)

        path = self._get_config_path()
        if not os.path.exists(path):
            log.info('Saving default config')
            self.save_config(self._get_default_config())


    def save_config(self, config):
        folder = self._get_path_inside_padmiss_dir()
        if not os.path.isdir(folder):
            os.makedirs(folder)

        path = self._get_config_path()
        log.info("Saving to: " + path)

        with open(path, 'w') as f:
            f.write(config.json(sort_keys=True, indent=4))

        for f in self.changed:
            f()

    def load_config(self):
        self._create_initial_directories_if_necessary()
        return PadmissConfig.parse_file(self._get_config_path())

manager = PadmissConfigManager()

def getManager():
    return manager