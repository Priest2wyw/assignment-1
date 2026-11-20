"""Read-only artifact viewer. Run with Python; no third-party dependencies."""
from __future__ import annotations

import argparse
import json
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "artifacts"
PAGE = Path(__file__).with_suffix(".html")


def artifact_path(root: Path, name: str) -> Path:
    root = root.resolve()
    path = (root / name).resolve()
    if Path(name).is_absolute() or not path.is_relative_to(root) or path.suffix != ".json":
        raise ValueError("只能查看 artifacts 目录内的 JSON 文件。")
    return path


def list_files(root: Path) -> list[dict]:
    result = []
    for path in sorted(root.rglob("*.json")):
        try:
            name = path.relative_to(root).as_posix()
            safe_path = artifact_path(root, name)
            if safe_path.is_file():
                stat = safe_path.stat()
                result.append({"name": name, "size": stat.st_size, "modified": stat.st_mtime})
        except (OSError, ValueError):
            continue
    return result


def read_artifact(root: Path, name: str):
    return json.loads(artifact_path(root, name).read_text(encoding="utf-8"))


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, root: Path, **kwargs):
        self.root = root
        super().__init__(*args, **kwargs)

    def respond(self, status, body, content_type="application/json; charset=utf-8"):
        payload = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        url = urlsplit(self.path)
        try:
            if url.path == "/":
                self.respond(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            elif url.path == "/api/files":
                self.respond(200, {"files": list_files(self.root)})
            elif url.path == "/api/artifact":
                name = parse_qs(url.query).get("name", [""])[0]
                self.respond(200, {"data": read_artifact(self.root, name)})
            else:
                self.respond(404, {"error": "地址不存在。"})
        except FileNotFoundError:
            self.respond(404, {"error": "文件不存在，请刷新文件列表。"})
        except (json.JSONDecodeError, UnicodeError):
            self.respond(422, {"error": "JSON 无法解析；文件可能尚未写完，请稍后刷新。"})
        except ValueError as exc:
            self.respond(400, {"error": str(exc)})
        except OSError:
            self.respond(500, {"error": "无法读取文件。"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8105)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), partial(Handler, root=args.root.resolve()))
    print(f"Artifact viewer: http://{args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
