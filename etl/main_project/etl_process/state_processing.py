import abc
import json
from json import JSONDecodeError
from typing import Any, Optional
from pathlib import Path


class BaseStorage:
    @abc.abstractmethod
    def save_state(self, state: dict) -> None:
        """Сохранить состояние в постоянное хранилище"""
        pass

    @abc.abstractmethod
    def retrieve_state(self) -> dict:
        """Загрузить состояние локально из постоянного хранилища"""
        pass


class JsonFileStorage(BaseStorage):
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path
        file_path_obj = Path(self.file_path)
        if not file_path_obj.exists():
            with open(self.file_path, 'w') as creating_new_csv_file:
                pass
        if not type(self.file_path) == str:
            self.file_path = None

    def save_state(self, state: dict) -> None:
        """Сохранить состояние в постоянное хранилище"""

        if self.file_path is not None:
            try:
                with open(self.file_path, 'w') as storage_file:
                    json.dump(state, storage_file)
            except JSONDecodeError:
                return None

        return None

    def retrieve_state(self) -> dict:
        """Загрузить состояние локально из постоянного хранилища"""
        if self.file_path is None:
            data = {}
            return data

        else:
            with open(self.file_path) as storage_file:
                try:
                    data = json.load(storage_file)
                    return data
                except JSONDecodeError:
                    data = {}
                    return data


class State:
    """
    Класс для хранения состояния при работе с данными, чтобы постоянно не перечитывать данные с начала.
    Здесь представлена реализация с сохранением состояния в файл.
    """

    def __init__(self, storage: JsonFileStorage):
        self.storage = storage

    def set_state(self, key: str, value: Any) -> None:
        """Установить состояние для определённого ключа"""
        current_state = self.storage.retrieve_state()
        current_state[key] = value
        self.storage.save_state(current_state)
        return None

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу"""
        key_state = self.storage.retrieve_state().get(key)
        return key_state