import os
import sys
import ssl
import httpx

# UTF-8 для Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Патчим httpx.HTTPTransport для отключения SSL проверки
_original_init = httpx.HTTPTransport.__init__


def _patched_init(self, *args, **kwargs):
    kwargs["verify"] = False
    _original_init(self, *args, **kwargs)


httpx.HTTPTransport.__init__ = _patched_init

# Токен GigaChat
GIGACHAT_TOKEN = "MDE5YzE5MWYtYWVmMy03MjUyLTg0MjgtMDcyODYzNjBkYzVkOmZhOWVlNmIzLThkYjgtNDM0Ny1hMWZlLWNlNWE0NWI3MTM2Nw=="


class GigaChatClient:
    def __init__(self):
        self._token = GIGACHAT_TOKEN if GIGACHAT_TOKEN else None

    def chat(self, message: str) -> str:
        """Отправить сообщение ИИ и получить ответ"""
        if not self._token:
            return "GigaChat not configured"

        try:
            from gigachat import GigaChat

            client = GigaChat(credentials=self._token)
            response = client.chat(message)
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"


gigachat_client = GigaChatClient()
