"""Optional fallback: serve the adjacent Reader on a free loopback port and open it."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder',nargs='?',default=str(Path(__file__).resolve().parents[1]))
    p.add_argument('--no-open',action='store_true')
    args=p.parse_args();root=Path(args.folder).resolve()
    if not (root/'index.html').is_file():p.exit(1,'Reader index.html not found.\n')
    with ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(root))) as server:
        url=f'http://127.0.0.1:{server.server_port}/'
        print(url,flush=True)
        print('Keep this window open while reading. Ctrl-C stops the fallback server.',flush=True)
        if not args.no_open:webbrowser.open(url)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
