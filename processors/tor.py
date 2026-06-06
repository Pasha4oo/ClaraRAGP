from os import path
from requests import Session

import socket

from logs import logger


class Tor(object):
    def __init__(self):
        self.SOCKS = "socks5h://127.0.0.1:9050"
        self.CONTROL = 9051
        self.COOKIE_PATHS = [
            path.expandvars(r'%APPDATA%\tor\control_auth_cookie'),
            path.expandvars(r'%LOCALAPPDATA%\tor\control_auth_cookie'),
            'control_auth_cookie'
        ]

        self.session = Session()
        self.session.proxies = {'http': self.SOCKS, 'https': self.SOCKS}
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'ru'
        })

        self.cookie = None
        self.sock = None

        self.connect()

        self.new_ip()

    def get_ip(self) -> str:
        """Returns IP via httpbin.org"""
        try:
            return self.session.get('https://httpbin.org/ip', timeout=10).json()['origin']
        except Exception:
            logger.error("Unknown ip:", exc_info=True)

            return None


    def connect(self):
        """Connects to tor"""
        for p in self.COOKIE_PATHS:
            if path.isfile(p):
                with open(p, 'rb') as f:
                    self.cookie = f.read().hex()
                break

        if not self.cookie:
            logger.error("Tor cookie not founded")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(10)

        try:
            self.sock.connect(('127.0.0.1', self.CONTROL))

            #self._read_until(self.sock, b'\r\n', timeout=2)

            self.sock.sendall(f'AUTHENTICATE {self.cookie}\r\n'.encode())
            resp = self._read_until(self.sock, b'\r\n', timeout=5).decode(errors='ignore')
            if not resp.startswith('250'):
                logger.error("Authentication error")

        except:
            logger.error("Connect to tor error:", exc_info=True)

    def new_ip(self):
        """Changes IP via Tor Control"""
        try:
            self.sock.sendall(b'SIGNAL NEWNYM\r\n')
            resp = self._read_until(self.sock, b'\r\n', timeout=5).decode(errors='ignore')
            if not resp.startswith('250'):
                logger.error(f"NEWNYM error: {resp}")

            logger.info("IP was changed successfully")

        except Exception as e:
            logger.error("Get new tor ip error:", exc_info=True)

    def _read_until(self, sock, delimiter, timeout: int = 5) -> str:
        """Reads socket"""
        data = b''
        sock.settimeout(timeout)
        try:
            while not data.endswith(delimiter):
                chunk = sock.recv(1)
                if not chunk:
                    break
                data += chunk
        except socket.timeout:
            pass
        return data
