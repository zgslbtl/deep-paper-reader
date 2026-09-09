"""Serve a built reader on loopback only; Ctrl-C stops it."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder');p.add_argument('--port',type=int,default=8765)
    args=p.parse_args();folder=Path(args.folder).resolve()
    if not (folder/'.deep-paper-reader-build').exists():p.exit(1,'ERROR: expected a built reader directory.\n')
    class Handler(SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Cache-Control','no-cache')
            self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'")
            super().end_headers()
    with ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(folder))) as server:
        print(f'Deep Paper Reader: http://127.0.0.1:{server.server_port}',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:print('\nStopped.')
