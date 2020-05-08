"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                tmp_login = decoded.replace("login:", "").replace("\r\n", "")
                if self.chk_login(tmp_login):  # если уже такой существует
                    self.transport.write(
                        f"Логин <{tmp_login}> занят,выберите другой!".encode()
                    )
                    self.close_me()  # закрыть подключение
                else:
                    self.transport.write(
                        f"Привет, {tmp_login}!".encode()
                    )
                    self.login = tmp_login
                    self.send_history()
        else:
            self.send_message(decoded)

    def close_me(self):
        #тут в дальнейшем будут какие-то проверки перед закрытием
        self.transport.close()  # закрыть подключение, у сервера себя не удаляем, т.к. сработает connection_made() и там удалится

    def send_history(self):
        for msg in self.server.messages:
            self.transport.write(
                f"{msg}\r\n".encode()
            )

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        if len(self.server.messages) > 9:
            self.server.messages.pop(0)

        self.server.messages.append(format_string)

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")

    def chk_login(self, new_login: str):  # проверяем есть ли уже такой логин
        for client in self.server.clients:
            if client.login == new_login:
                return 1
        return 0


class Server:
    clients: list
    messages: list  # тут будем хранить историю сообщений

    def __init__(self):
        self.clients = []
        self.messages = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
