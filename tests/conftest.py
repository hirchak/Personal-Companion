"""Disposable regression preflight port isolated from the owner's live core pilot.
No private root/records are inspected; the production preflight still binds a real loopback socket.
"""
import functools
import pytest

@pytest.fixture(autouse=True)
def isolated_preflight_port(monkeypatch):
 from apps.core import release,local_private
 from apps.core.storage import SafeError
 import socket
 with socket.socket() as s:
  s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 original_release=release.preflight;original_private=local_private.preflight
 @functools.wraps(original_release)
 def release_check(package,expected_hash,app,data,port_override=port,**kwargs):
  return original_release(package,expected_hash,app,data,kwargs.pop('port',port_override),**kwargs)
 @functools.wraps(original_private)
 def private_check(package,expected_hash,app,data,backup_directory,port_override=port,**kwargs):
  return original_private(package,expected_hash,app,data,backup_directory,kwargs.pop('port',port_override),**kwargs)
 monkeypatch.setattr(release,'preflight',release_check)
 monkeypatch.setattr(local_private,'preflight',private_check)
 # require_preflight historically explicitly passes8765: keep its port check real but isolated.
 def required(package,expected_hash,app,data,port_override=port):
  result=original_release(package,expected_hash,app,data,port_override)
  if result['status']!='PASS':raise SafeError('PREFLIGHT_INCOMPATIBLE')
  return result
 monkeypatch.setattr(release,'require_preflight',required)

 yield port
