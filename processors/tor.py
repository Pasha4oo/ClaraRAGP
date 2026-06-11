from os import path, getpid
from requests import Session

import sys
import socket
import subprocess

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

        self.run()
        self.connect()

        self.new_ip()

    def get_ip(self) -> str:
        """Returns IP via httpbin.org"""
        try:
            return self.session.get('https://api.ipify.org/', timeout=10).text.strip()
        except Exception:
            logger.error("Unknown ip:", exc_info=True)

            return None

    def run(self):
        tor = path.expandvars(path.join(path.dirname(__file__), "tor", "tor", "tor.exe"))
        flags = subprocess.CREATE_NO_WINDOW

        if b"tor.exe" not in subprocess.check_output('tasklist /FI "IMAGENAME eq tor.exe"', creationflags=flags):
            proc = subprocess.Popen([tor], creationflags=flags, stdout=subprocess.PIPE, text=True, errors='ignore')
            logger.info("Loading tor")

            for line in proc.stdout:
                if "Bootstrapped 100%" in line:
                    logger.info("Tor loaded successfully")
                    break
            
            subprocess.run('taskkill /f /fi "WINDOWTITLE eq tor_timer_watcher"', creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            p_name = path.basename(sys.executable)
            
            watcher = f'cmd.exe /k "title tor_timer_watcher && tasklist /FI "PID eq {getpid()}" /NH | find "{getpid()}" && timeout /t 300 /nobreak & tasklist /FI "IMAGENAME eq {p_name}" 2>nul | find "{p_name}" >nul || taskkill /f /im tor.exe & exit"'
            subprocess.Popen(watcher, creationflags=flags | subprocess.DETACHED_PROCESS)

        else:
            try:
                with socket.create_connection(('127.0.0.1', 9050), timeout=1):
                    logger.info("Tor already loaded")

            except Exception:
                subprocess.run('taskkill /f /im tor.exe', creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.run()

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
