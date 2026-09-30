"""Process-local runtime deny-egress; never modifies OS/network configuration."""
import ipaddress
import sys


def loopback(host):
    if host == 'localhost':
        return True
    if host is None or host == '':
        return False  # empty bind hosts mean wildcard interfaces, never loopback
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def deny_egress():
    def audit(event, args):
        if event in {'socket.connect', 'socket.bind', 'socket.sendto', 'socket.sendmsg'}:
            address = args[1]
            # sendmsg without an address uses an already-connected socket, whose
            # destination was checked at connect. Unconnected sendmsg cannot send.
            if address is None and event == 'socket.sendmsg':
                return
            if not isinstance(address, tuple):
                raise PermissionError('M1_NON_IP_SOCKET_DENIED')
            if not loopback(address[0]):
                raise PermissionError('M1_EGRESS_DENIED')
        if event in {'socket.getaddrinfo', 'socket.gethostbyname', 'socket.gethostbyaddr'}:
            if not loopback(args[0]):
                raise PermissionError('M1_EGRESS_DENIED')
        if event == 'socket.getnameinfo' and not loopback(args[0][0]):
            raise PermissionError('M1_EGRESS_DENIED')
    sys.addaudithook(audit)
