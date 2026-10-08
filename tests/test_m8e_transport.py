"""Fixed-host transport regression with synthetic socket peers; no networking/auth."""
import pytest

from apps.core import local_provider_tunnel as tunnel


class Peer:
    def __init__(self, packets):
        self.packets=list(packets)
        self.sent=[]
        self.timeouts=[]
        self.closed=False

    def recv(self, size):
        return self.packets.pop(0)

    def sendall(self, data):
        self.sent.append(data)

    def settimeout(self, value):
        self.timeouts.append(value)

    def close(self):
        self.closed=True


def client_for(header):
    return Peer([bytes([byte]) for byte in header]+[b'ORIGINAL_SYNTHETIC_OPAQUE_TLS_CLIENT',b''])


def test_ipv6_first_network_uses_ipv4_fixed_host_and_opaque_relay(monkeypatch):
    client=client_for(b'CONNECT chatgpt.com:443 HTTP/1.1\r\n\r\n')
    upstream=Peer([b'ORIGINAL_SYNTHETIC_OPAQUE_TLS_SERVER'])
    connections=[]
    upstream.connect=lambda destination:connections.append(destination)
    def socket_for(family, kind):
        if family==tunnel.socket.AF_INET6:raise TimeoutError('ORIGINAL SYNTHETIC unreachable IPv6')
        assert family==tunnel.socket.AF_INET and kind==tunnel.socket.SOCK_STREAM
        return upstream
    # The previous any-family connector waits on an unreachable IPv6 route.
    monkeypatch.setattr(tunnel.socket,'create_connection',lambda *a,**k:(_ for _ in ()).throw(TimeoutError('ORIGINAL SYNTHETIC IPv6-first timeout')))
    monkeypatch.setattr(tunnel.socket,'socket',socket_for)
    ready=iter([client,upstream,client])
    monkeypatch.setattr(tunnel.select,'select',lambda *args:([next(ready)],[],[]))
    tunnel.serve_client(client)
    assert connections==[('chatgpt.com',443)]
    assert client.sent==[b'HTTP/1.1 200 Connection Established\r\n\r\n',b'ORIGINAL_SYNTHETIC_OPAQUE_TLS_SERVER']
    assert upstream.sent==[b'ORIGINAL_SYNTHETIC_OPAQUE_TLS_CLIENT']
    assert client.closed and upstream.closed
    assert client.timeouts==[10,None] and upstream.timeouts==[10,None]


@pytest.mark.parametrize('header',[
    b'CONNECT api.openai.com:443 HTTP/1.1\r\n\r\n',
    b'CONNECT chatgpt.com:80 HTTP/1.1\r\n\r\n',
    b'CONNECT ORIGINAL_SYNTHETIC_UNKNOWN:443 HTTP/1.1\r\n\r\n',
    b'GET https://chatgpt.com/ HTTP/1.1\r\n\r\n',
])
def test_unknown_destination_or_protocol_cannot_open_socket(monkeypatch,header):
    client=client_for(header)
    monkeypatch.setattr(tunnel.socket,'socket',lambda *a,**k:pytest.fail('UNAPPROVED_DESTINATION_SOCKET'))
    tunnel.serve_client(client)
    assert client.sent==[b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n']
    assert client.closed


@pytest.mark.parametrize('failure',[TimeoutError,OSError])
def test_connect_failure_closes_peers_without_success_or_raw_error(monkeypatch,failure):
    client=client_for(b'CONNECT chatgpt.com:443 HTTP/1.0\r\n\r\n')
    upstream=Peer([])
    def connect(destination):raise failure('ORIGINAL_SYNTHETIC_SECRET_LIKE_RPC_ERROR')
    upstream.connect=connect
    monkeypatch.setattr(tunnel.socket,'socket',lambda *a:upstream)
    tunnel.serve_client(client)
    assert client.sent==[] and upstream.sent==[]
    assert client.closed and upstream.closed
