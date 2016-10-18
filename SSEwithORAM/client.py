# -*- coding: utf-8 -*-
import socket


def main():
    target_host = "0.0.0.0"
    target_port = 9999

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:

        client.connect((target_host, target_port))

        client.send(b"GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")

        response = client.recv(4096)

        print(response)


if __name__ == '__main__':
    main()
