import socket


class SimpleHTTPServer:
    _socket = None
    METHODS_MAP = {}
    SUPPORTED_PROTOCOL = "HTTP/1.1"

    def __init__(self, hostname="", port=8080) -> None:
        print("Initializing SimpleHTTPServer")
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((hostname, port))
        self.METHODS_MAP = {
            "GET": self.get_handler,
            "POST": self.post_handler,
            "PUT": self.put_handler,
            "DELETE": self.delete_handler,
            "HEAD": self.head_handler,
        }

    def get_handler(self, *args, **kwargs):
        return self._basic_ok("You called GET, Not Sure what to do next")

    def post_handler(self, *args, **kwargs):
        return self._basic_ok("You called POST, Not Sure what to do next")

    def put_handler(self, *args, **kwargs):
        return self._basic_ok("You called PUT, Not Sure what to do next", "201 Created")

    def delete_handler(self, *args, **kwargs):
        return self._basic_ok(
            "You called DELETE, Not Sure what to do next", "204 No Content"
        )

    def head_handler(self, *args, **kwargs):
        return self._basic_ok("")

    def serve(self):
        if self._socket is None:
            print("must initialize class first!")
            return -1
        self._socket.listen(1)
        while True:
            conn, addr = self._socket.accept()
            with conn:
                print("Ready for connection")
                data = conn.recv(1024)
                if not data:
                    break
                response_data = self.read_handler(data)
                self.write_handler(conn, response_data)
            print("Ending connection")
        print("Server stopping")

    def read_handler(self, data):
        s_data = data.decode("utf8")
        print(f"RX: {data}")
        lines = s_data.split("\n")
        try:
            start_line = lines[0].split(" ")
        except TypeError:
            print(f"Error trying to read: {lines[0]}")
            return "HTTP/1.1 400 Bad Request\nGet out of here with that\n\n"
        if start_line[0] not in self.METHODS_MAP:
            if len(start_line) < 3 or start_line[2] != "HTTP/1.1":
                return "HTTP/1.1 400 Bad request"
            return f"HTTP/1.1 405 Method not allowed\nI only support {self.METHODS_MAP}\n\n"

        response_data = self.METHODS_MAP[start_line[0]](start_line, lines)
        if not response_data:
            print("No response data, returning basic OK")
            response_data = self._basic_error(
                "Uhhh, something didn't work", "500 Internal Server Error"
            )
        return response_data

    def _basic_ok(self, msg=None, response_code="200 Ok"):
        msg_len = len(msg) if msg else 0
        return f"""{self.SUPPORTED_PROTOCOL} {response_code}\r
Content-Length: {msg_len}\r
Content-Type: text/html\r
\r
{msg}
"""

    def _basic_error(self, msg=None, error_code="400 Whoops"):
        msg_len = len(msg) if msg else 0
        return f"""{self.SUPPORTED_PROTOCOL} {error_code}\r
Content-Length: {msg_len}\r
Content-Type: text/html\r
\r
{msg}
"""

    def write_handler(self, conn, data):
        conn.sendall(bytes(f"{data} \n".encode("utf8")))
        conn.close()
        return


def main():
    print("Hello from httpserver-simple!")
    server = SimpleHTTPServer()
    server.serve()


if __name__ == "__main__":
    main()
