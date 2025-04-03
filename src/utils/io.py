import os
import json


def read_json(file_path: str) -> dict:
    text = read_text(file_path)
    return json.loads(text)


def write_json(file_path: str, obj: dict, encoding: str = "utf-8") -> None:
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    write_text(file_path, text, encoding=encoding)


def read_text(file_path: str, encoding: str = "utf-8") -> str:
    bytes = read_binary(file_path)
    return bytes.decode(encoding)


def write_text(file_path: str, text: str, encoding: str = "utf-8") -> None:
    bytes = text.encode(encoding)
    write_binary(file_path, bytes)


def read_binary(file_path: str) -> bytes:
    with open(file_path, "rb") as f:
        return f.read()


def write_binary(file_path: str, data: bytes) -> None:
    dir_path = os.path.dirname(file_path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(data)
