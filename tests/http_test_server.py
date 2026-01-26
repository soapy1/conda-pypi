# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""
Local test server based on http.server
ref: https://github.com/conda/conda/blob/25.11.0/tests/http_test_server.py
"""
# TODO: once conda 26.1 is released, import conda.testing.http_test_server
# and remove this file

import contextlib
import http.server
import queue
import socket
import threading
import json


def run_test_server(directory: str) -> http.server.ThreadingHTTPServer:
    """
    Run a test server on a random port. Inspect returned server to get port,
    shutdown etc.
    """

    class DualStackServer(http.server.ThreadingHTTPServer):
        daemon_threads = False  # These are per-request threads
        allow_reuse_address = True  # Good for tests
        request_queue_size = 64  # Should be more than the number of test packages

        def server_bind(self):
            # suppress exception when protocol is IPv4
            with contextlib.suppress(Exception):
                self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            return super().server_bind()

        def finish_request(self, request, client_address):
            self.RequestHandlerClass(request, client_address, self, directory=directory)

    def start_server(queue):
        with DualStackServer(
            ("127.0.0.1", 0), http.server.SimpleHTTPRequestHandler
        ) as httpd:
            host, port = httpd.socket.getsockname()[:2]
            queue.put(httpd)
            url_host = f"[{host}]" if ":" in host else host
            print(f"Serving HTTP on {host} port {port} (http://{url_host}:{port}/) ...")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nKeyboard interrupt received, exiting.")

    started = queue.Queue()

    threading.Thread(target=start_server, args=(started,), daemon=True).start()

    return started.get(timeout=1)


if __name__ == "__main__":
    from pathlib import Path

    HERE = Path(__file__).parent
    base = HERE / "conda_local_channel"
    http = run_test_server(str(base))

    http_sock_name = http.socket.getsockname()
    print(f"http://{http_sock_name[0]}:{http_sock_name[1]}")

    noarch_repodata = base / "noarch/repodata.json"
    repodata = {}
    with open(noarch_repodata) as f:
        repodata = json.loads(f.read())
        for pkg, data in repodata["packages.whl"].items():
            data["url"] = f"http://{http_sock_name[0]}:{http_sock_name[1]}/noarch/{data['fn']}"
    
    with open(noarch_repodata, 'w') as json_file:
        json.dump(repodata, json_file, indent=4)
    
    def main(stdscr):
        while True:
            ch = stdscr.getch()
            if ch == 27:  # ESC key
                http.shutdown()
                break

    try:
        while True:
            input()
    except KeyboardInterrupt:
        http.shutdown()
        print("\nServer stopped.")