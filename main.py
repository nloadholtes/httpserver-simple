import socket


class SimpleHTTPServer:
    _socket = None
    METHODS_ACCEPTED = [
        "GET",
        "POST",
    ]

    def __init__(self, hostname="", port=8080) -> None:
        print("Initializing SimpleHTTPServer")
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((hostname, port))

    def serve(self):
        if self._socket is None:
            print("must initialize class first!")
            return -1
        self._socket.listen(1)
        while True:
            conn, addr = self._socket.accept()
            with conn:
                print("Ready for connection")
                while True:
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
        if start_line[0] not in self.METHODS_ACCEPTED:
            if len(start_line) < 3 or start_line[2] != "HTTP/1.1":
                return "HTTP/1.1 400 Bad request"
            return f"HTTP/1.1 405 Method not allowed\nI only support {self.METHODS_ACCEPTED}\n\n"

        response_data = "HTTP/1.1 200 OK\nNot Sure what to do next"

        return response_data

    def write_handler(self, conn, data):
        conn.sendall(bytes(f"{data} \n".encode("utf8")))
        return


def main():
    print("Hello from httpserver-simple!")
    server = SimpleHTTPServer()
    server.serve()


if __name__ == "__main__":
    main()
