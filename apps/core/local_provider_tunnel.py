"""Fixed-destination TLS-blind local transport for the native subscription client.

Executed isolated (-I -S). Never parses TLS, prompts, auth or content; no persistence/logs.
The only accepted destination is the existing ChatGPT subscription host and port.
"""
import select
import socket
import threading

DESTINATION = ('chatgpt.com', 443)


def connect_request(header):
    try:
        first = header.split(b'\r\n', 1)[0].decode('ascii')
    except UnicodeError:
        return False
    return first in ('CONNECT chatgpt.com:443 HTTP/1.1', 'CONNECT chatgpt.com:443 HTTP/1.0')


def serve_client(client):
    upstream = None
    try:
        client.settimeout(10)
        header = bytearray()
        while b'\r\n\r\n' not in header:
            chunk = client.recv(1)
            if not chunk or len(header) >= 8192:
                return
            header.extend(chunk)
        if not connect_request(bytes(header)):
            client.sendall(b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n')
            return
        # This Mac can resolve IPv6 while that route stalls. An explicit IPv4
        # socket avoids waiting on IPv6 before the SDK's routing deadline.
        # DNS still selects the fixed subscription host; TLS stays end-to-end.
        upstream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upstream.settimeout(10)
        upstream.connect(DESTINATION)
        client.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
        client.settimeout(None)
        upstream.settimeout(None)
        while True:
            ready, _, _ = select.select([client, upstream], [], [], 120)
            if not ready:
                return
            for source in ready:
                data = source.recv(16384)
                if not data:
                    return
                (upstream if source is client else client).sendall(data)
    except (OSError, ValueError):
        pass
    finally:
        client.close()
        if upstream is not None:
            upstream.close()


def main():
    with socket.socket() as server:
        server.bind(('127.0.0.1', 0))
        server.listen(8)
        print(server.getsockname()[1], flush=True)
        slots = threading.BoundedSemaphore(8)
        def guarded(client):
            try:
                serve_client(client)
            finally:
                slots.release()
        while True:
            client, _ = server.accept()
            if not slots.acquire(blocking=False):
                client.close()
                continue
            threading.Thread(target=guarded, args=(client,), daemon=True).start()


if __name__ == '__main__':
    main()
