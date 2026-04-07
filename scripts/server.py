#!/usr/bin/env python3
"""
typeset-engine HTTP API Server

轻量 HTTP 服务，让其他 agent 通过 curl 调用全部渲染能力。
端口: 9090

启动:
  python scripts/server.py
  # 或
  docker run -d -p 9090:9090 -v /data:/app/output typeset-engine:v1 python scripts/server.py

调用:
  curl -X POST http://localhost:9090/render/pdf -H "Content-Type: application/json" -d @data.json -o report.pdf
"""

import json
import os
import sys
import tempfile
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, str(Path(__file__).parent))

OUTPUT_DIR = os.environ.get('OUTPUT_DIR', '/app/output')
PORT = int(os.environ.get('PORT', '9090'))


class TypesetHandler(BaseHTTPRequestHandler):

    def _send_file(self, filepath, content_type='application/octet-stream'):
        """发送文件响应"""
        with open(filepath, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(filepath)}"')
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, obj, status=200):
        """发送 JSON 响应"""
        data = json.dumps(obj, ensure_ascii=False, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_error(self, status, message):
        self._send_json({'error': message}, status)

    def _read_body(self):
        """读取请求体 JSON"""
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return {}
        body = self.rfile.read(length)
        return json.loads(body.decode('utf-8'))

    # ─── GET ────────────────────────────────────

    def do_GET(self):
        path = urlparse(self.path).path

        if path == '/health':
            self._send_json({'status': 'ok', 'engine': 'typeset-engine', 'version': '1.0'})

        elif path == '/styles':
            from render_pptx_ai import list_styles
            self._send_json(list_styles())

        elif path == '/fonts':
            import matplotlib.font_manager as fm
            fonts = sorted(set(f.name for f in fm.fontManager.ttflist))
            self._send_json({'count': len(fonts), 'fonts': fonts})

        elif path == '/capabilities':
            self._send_json({
                'commands': {
                    'pdf': {'method': 'POST', 'path': '/render/pdf', 'themes': ['cicc', 'ms', 'cms', 'dachen']},
                    'docx': {'method': 'POST', 'path': '/render/docx', 'themes': ['cicc', 'ms', 'cms', 'dachen']},
                    'pptx': {'method': 'POST', 'path': '/render/pptx'},
                    'pptx-ai': {'method': 'POST', 'path': '/render/pptx-ai', 'requires': 'GEMINI_API_KEY'},
                    'chart': {'method': 'POST', 'path': '/render/chart',
                              'types': ['bar', 'line', 'area', 'pie', 'waterfall', 'scatter',
                                        'heatmap', 'radar', 'funnel', 'gauge', 'treemap',
                                        'candlestick', 'combo'],
                              'themes': ['default', 'cicc', 'goldman', 'dark']},
                    'illustrate': {'method': 'POST', 'path': '/render/illustrate', 'requires': 'GEMINI_API_KEY',
                                   'styles': ['gradient-glass', 'vector-illustration', 'ticket']},
                },
                'styles_endpoint': '/styles',
                'health_endpoint': '/health',
            })

        else:
            self._send_error(404, f'Unknown endpoint: {path}')

    # ─── POST ───────────────────────────────────

    def do_POST(self):
        path = urlparse(self.path).path
        params = parse_qs(urlparse(self.path).query)

        try:
            data = self._read_body()
        except Exception as e:
            self._send_error(400, f'Invalid JSON: {e}')
            return

        try:
            if path == '/render/pdf':
                self._handle_pdf(data, params)
            elif path == '/render/docx':
                self._handle_docx(data, params)
            elif path == '/render/pptx':
                self._handle_pptx(data, params)
            elif path == '/render/pptx-ai':
                self._handle_pptx_ai(data, params)
            elif path == '/render/chart':
                self._handle_chart(data, params)
            elif path == '/render/illustrate':
                self._handle_illustrate(data, params)
            else:
                self._send_error(404, f'Unknown endpoint: {path}')
        except Exception as e:
            traceback.print_exc()
            self._send_error(500, str(e))

    def _get_param(self, params, key, default=''):
        """从 query params 或 JSON body 获取参数"""
        if key in params:
            return params[key][0]
        return default

    # ─── Handlers ───────────────────────────────

    def _handle_pdf(self, data, params):
        from render_pdf import render_pdf
        theme = data.pop('theme', None) or self._get_param(params, 'theme', 'cicc')

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False, dir=OUTPUT_DIR) as f:
            out_path = f.name

        render_pdf(data, out_path, theme=theme)
        self._send_file(out_path, 'application/pdf')
        os.unlink(out_path)

    def _handle_docx(self, data, params):
        from render_docx import render_docx
        theme = data.pop('theme', None) or self._get_param(params, 'theme', 'cicc')

        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False, dir=OUTPUT_DIR) as f:
            out_path = f.name

        render_docx(data, out_path, theme=theme)
        self._send_file(out_path,
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        os.unlink(out_path)

    def _handle_pptx(self, data, params):
        from render_pptx import render_pptx
        template = data.pop('template', None) or self._get_param(params, 'template', 'default')

        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False, dir=OUTPUT_DIR) as f:
            out_path = f.name

        render_pptx(data, out_path, template=template)
        self._send_file(out_path,
                        'application/vnd.openxmlformats-officedocument.presentationml.presentation')
        os.unlink(out_path)

    def _handle_pptx_ai(self, data, params):
        import shutil
        from render_pptx_ai import render_pptx_ai

        style = data.pop('style', None) or self._get_param(params, 'style', 'gradient-glass')
        resolution = data.pop('resolution', None) or self._get_param(params, 'resolution', '2K')
        video = data.pop('video', True)

        with tempfile.TemporaryDirectory(prefix='pptx_ai_', dir=OUTPUT_DIR) as out_dir:
            result = render_pptx_ai(data, out_dir, style=style, resolution=resolution, video=video)

            # 打包成 zip
            import zipfile
            zip_path = out_dir + '.zip'
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(out_dir):
                    for file in files:
                        filepath = os.path.join(root, file)
                        arcname = os.path.relpath(filepath, out_dir)
                        zf.write(filepath, arcname)

            self._send_file(zip_path, 'application/zip')
            os.unlink(zip_path)

    def _handle_chart(self, data, params):
        from render_charts import render_chart

        chart_type = data.pop('type', None) or self._get_param(params, 'type', 'bar')
        theme = data.pop('theme', None) or self._get_param(params, 'theme', 'default')
        chart_data = data.get('data', data)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False, dir=OUTPUT_DIR) as f:
            out_path = f.name

        render_chart(chart_type, chart_data, out_path, theme)
        self._send_file(out_path, 'image/png')
        os.unlink(out_path)

    def _handle_illustrate(self, data, params):
        from render_illustrate import generate_illustration

        content = data.get('content', '')
        style = data.get('style', 'gradient-glass')
        title = data.get('title', '')
        ratio = data.get('ratio', '16:9')
        cover = data.get('cover', False)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False, dir=OUTPUT_DIR) as f:
            out_path = f.name

        result = generate_illustration(content, out_path, style, title, ratio, cover)
        if result:
            self._send_file(out_path, 'image/png')
            os.unlink(out_path)
        else:
            self._send_error(500, 'Image generation failed')

    # ─── Logging ────────────────────────────────

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    server = HTTPServer(('0.0.0.0', PORT), TypesetHandler)
    print(f'typeset-engine HTTP API running on port {PORT}')
    print(f'Output directory: {OUTPUT_DIR}')
    print(f'Endpoints: /health /capabilities /styles /render/*')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down...')
        server.server_close()


if __name__ == '__main__':
    main()
