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
                # Print and echo
                print(data)
                conn.sendall(bytes(f"SERVER SAW: {data} \n".encode("utf8")))
        print("Server stopping")


def main():
    print("Hello from httpserver-simple!")
    server = SimpleHTTPServer()
    server.serve()


if __name__ == "__main__":
    main()
