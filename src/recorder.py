import json
import os

date_format = "%Y/%m/%d %H:%M:%S"


class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


class Recorder(Singleton):
    def __init__(self) -> None:
        self.file_name = "record.json"

        self.record: dict = self._load_json()

    def _load_json(self) -> dict:
        data: dict = {"nogi": {}, "sakura": {}, "hinata": {}}
        if os.path.isfile(self.file_name):
            with open(self.file_name, encoding="utf-8") as f:
                data = json.load(f)

        return data

    def call_getter(self, group: str):
        if self.record.get(group) is not None:

            def getter(code: str):
                return self._getter(group, code)

            return getter
        else:
            raise

    def _getter(self, group: str, code: str) -> dict | None:
        return self.record[group].get(code)

    def dump_json(self) -> None:
        self.sort_record()
        with open(self.file_name, mode="w", encoding="utf-8") as f:
            json.dump(
                self.record,
                f,
                indent=4,
                ensure_ascii=False,
            )

    def sort_record(self):
        self.record["nogi"] = self.sort_by_code(self.record["nogi"])
        self.record["sakura"] = self.sort_by_code(self.record["sakura"])
        self.record["hinata"] = self.sort_by_code(self.record["hinata"])

    def sort_by_code(self, d: dict):
        return dict(sorted(d.items(), key=lambda x: int(x[0])))
