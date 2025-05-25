import socket


class SimpleHTTPServer:
    _socket = None

    def __init__(self, hostname="", port=8080) -> None:
        print("Initializing SimpleHTTPServer")
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((hostname, port))

    def serve(self):
        if self._socket is None:
            print("must initialize class first!")
            return -1
        self._socket.listen(1)
        conn, addr = self._socket.accept()
        with conn:
            print("Ready for connection")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                response_data = self.read_handler(data)
                self.write_handler(conn, response_data)
        print("Server stopping")

    def read_handler(self, data):
        print(f"RX: {data}")
        return data

    def write_handler(self, conn, data):
        conn.sendall(bytes(f"SERVER SAW: {data} \n".encode("utf8")))
        return


def main():
    print("Hello from httpserver-simple!")
    server = SimpleHTTPServer()
    server.serve()


if __name__ == "__main__":
    main()
