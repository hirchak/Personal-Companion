"""Process-local runtime deny-egress; never modifies OS/network configuration."""
import ipaddress
import sys

def loopback(host):
    if host in {'localhost', None, ''}:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False

def deny_egress():
    def audit(event, args):
        if event in {'socket.connect', 'socket.bind'}:
            address = args[1]
            if isinstance(address, tuple) and not loopback(address[0]):
                raise PermissionError('M1_EGRESS_DENIED')
            if not isinstance(address, tuple):
                raise PermissionError('M1_NON_IP_SOCKET_DENIED')
        if event == 'socket.getaddrinfo' and not loopback(args[0]):
            raise PermissionError('M1_EGRESS_DENIED')
    sys.addaudithook(audit)
