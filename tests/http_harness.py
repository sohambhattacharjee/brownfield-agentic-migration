"""Issue raw HTTP/1.0 requests to a handler over a local socket pair.

This exercises BaseHTTPRequestHandler parsing, routing, and response framing
without binding a TCP port or opening a network listener.
"""
import json
import socket
import threading


def request_json(handler_class, method, path):
    client, server = socket.socketpair()
    client.settimeout(3)
    worker = threading.Thread(
        target=handler_class, args=(server, ("local", 0), None), daemon=True
    )
    worker.start()
    try:
        request = "%s %s HTTP/1.0\r\nHost: study\r\nConnection: close\r\n\r\n" % (method, path)
        client.sendall(request.encode("ascii"))
        response = bytearray()
        expected_size = None
        while expected_size is None or len(response) < expected_size:
            chunk = client.recv(4096)
            if not chunk:
                break
            response.extend(chunk)
            marker = response.find(b"\r\n\r\n")
            if marker >= 0 and expected_size is None:
                headers = response[:marker].decode("iso-8859-1").split("\r\n")
                content_length = next((int(line.split(":", 1)[1].strip())
                                       for line in headers[1:]
                                       if line.lower().startswith("content-length:")), 0)
                expected_size = marker + 4 + content_length
    finally:
        client.close()
        worker.join(timeout=3)
        server.close()
    if worker.is_alive():
        raise RuntimeError("HTTP handler did not close the local request")
    head, body = bytes(response).split(b"\r\n\r\n", 1)
    status = int(head.split(b" ", 2)[1])
    return status, json.loads(body.decode("utf-8"))
