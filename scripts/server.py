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

        elif path.startswith('/kami/template/'):
            # GET /kami/template/{name}?lang=en — 返回模板源码
            tpl_name = path[len('/kami/template/'):]
            lang = self._get_param(parse_qs(urlparse(self.path).query), 'lang', 'zh')
            from render_kami import KAMI_DIR, DOC_TYPES
            if tpl_name not in DOC_TYPES:
                self._send_error(404, f"unknown template '{tpl_name}', pick from {sorted(DOC_TYPES)}")
                return
            fname = f'{tpl_name}-en.html' if lang == 'en' else f'{tpl_name}.html'
            fpath = KAMI_DIR / fname
            if not fpath.exists():
                self._send_error(404, f'template file not found: {fname}')
                return
            body = fpath.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif path == '/kami/templates':
            from render_kami import KAMI_DIR, DOC_TYPES, PAGE_LIMITS
            items = []
            for doc_type in sorted(DOC_TYPES):
                for lang in ('zh', 'en'):
                    fname = f'{doc_type}-en.html' if lang == 'en' else f'{doc_type}.html'
                    if (KAMI_DIR / fname).exists():
                        items.append({
                            'doc_type': doc_type,
                            'language': lang,
                            'template': fname,
                            'pages': PAGE_LIMITS.get(doc_type),
                        })
            self._send_json({'templates': items})

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
                    'diagram': {'method': 'POST', 'path': '/render/diagram',
                               'description': 'SVG technical diagram → PNG (via rsvg-convert)',
                               'params': {'svg': 'SVG string (required)', 'width': 'PNG width (default 1920)',
                                          'format': 'png|svg|both', 'validate': 'true = validate only'}},
                    'illustrate': {'method': 'POST', 'path': '/render/illustrate', 'requires': 'GEMINI_API_KEY',
                                   'styles': ['gradient-glass', 'vector-illustration', 'ticket']},
                    'kami': {'method': 'POST', 'path': '/render/kami',
                             'description': 'kami 主题（暖米纸 + 油墨蓝 + serif）HTML → PDF',
                             'doc_types': ['one-pager', 'long-doc', 'letter', 'portfolio', 'resume'],
                             'languages': ['zh', 'en'],
                             'body_modes': {
                                 'html': 'full HTML string',
                                 'body_html': 'body innerHTML (server loads template)',
                                 'slots': '{{key}} dict replacement',
                             },
                             'related': {
                                 'list-templates': 'GET /kami/templates',
                                 'fetch-template': 'GET /kami/template/{doc_type}?lang=zh|en',
                             }},
                    'validate-css': {'method': 'POST', 'path': '/validate/css',
                                     'description': 'Kami 美学宪法扫描（冷灰/rgba/bold/行高等 9 条约束）',
                                     'body': {'content': 'required str', 'filename': 'optional hint for ext-based rules', 'only': 'optional list'},
                                     'rules': ['rgba', 'coolgray', 'white', 'lineheight',
                                               'boldserif', 'hardshadow', 'thinborder', 'vh', 'flexbreak']},
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
            elif path == '/render/diagram':
                self._handle_diagram(data, params)
            elif path == '/render/illustrate':
                self._handle_illustrate(data, params)
            elif path == '/validate/css':
                self._handle_validate_css(data, params)
            elif path == '/render/kami':
                self._handle_render_kami(data, params)
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

    def _handle_diagram(self, data, params):
        from render_diagram import render_diagram, validate_svg

        svg_content = data.get('svg', '')
        if not svg_content:
            self._send_error(400, 'Missing "svg" field in request body')
            return

        width = int(data.get('width', 1920))
        fmt = data.get('format', 'png')  # png | svg | both
        validate_only = data.get('validate', False)

        # 仅校验模式
        if validate_only:
            result = validate_svg(svg_content)
            self._send_json(result)
            return

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False, dir=OUTPUT_DIR) as f:
            out_base = f.name.rsplit('.', 1)[0]

        out_path = render_diagram(svg_content, out_base + '.png', width=width, fmt=fmt)

        if out_path.endswith('.svg'):
            self._send_file(out_path, 'image/svg+xml')
        else:
            self._send_file(out_path, 'image/png')

        # 清理
        for ext in ['.png', '.svg']:
            p = out_base + ext
            if os.path.exists(p):
                os.unlink(p)

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

    def _handle_render_kami(self, data, params):
        """kami 主题 HTML → PDF（WeasyPrint 后端）

        body 三种模式（优先级：html > body_html > slots）：
          1. 整 HTML: {"html": "<!doctype html>...</html>"}
          2. 模板+body替换: {"doc_type": "resume", "language": "en", "body_html": "..."}
          3. 模板+slots替换: {"doc_type": "one-pager", "language": "zh",
                             "slots": {"title": "..."}}
        """
        from render_kami import render_html, render_template, KAMI_DIR

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False,
                                         dir=OUTPUT_DIR) as f:
            out_path = f.name

        try:
            if data.get('html'):
                base_url = data.get('base_url') or str(KAMI_DIR)
                result = render_html(data['html'], base_url, out_path)
            else:
                doc_type = data.get('doc_type') or self._get_param(params, 'doc_type')
                language = data.get('language') or self._get_param(params, 'lang', 'zh')
                if not doc_type:
                    self._send_error(400,
                        "'doc_type' is required (one of: "
                        "one-pager, long-doc, letter, portfolio, resume) "
                        "— or send full 'html' field instead")
                    return
                result = render_template(
                    doc_type=doc_type,
                    language=language,
                    body_html=data.get('body_html'),
                    slots=data.get('slots'),
                    out_path=out_path,
                )

            # 成功：把 PDF 作为附件返回；附加 meta 进 headers 方便调试
            with open(out_path, 'rb') as f:
                pdf_bytes = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/pdf')
            self.send_header('Content-Length', str(len(pdf_bytes)))
            self.send_header('Content-Disposition',
                             f'attachment; filename="kami-{result.get("doc_type", "output")}.pdf"')
            self.send_header('X-Kami-Pages', str(result.get('pages', 0)))
            if result.get('warnings'):
                # HTTP header 必须是 latin-1 可编码；保留 ensure_ascii=True 把中文转 \uXXXX
                self.send_header('X-Kami-Warnings', json.dumps(result['warnings']))
            self.end_headers()
            self.wfile.write(pdf_bytes)
        except FileNotFoundError as e:
            self._send_error(404, str(e))
        except ValueError as e:
            self._send_error(400, str(e))
        finally:
            try:
                os.unlink(out_path)
            except OSError:
                pass

    def _handle_validate_css(self, data, params):
        """Kami 美学扫描：POST /validate/css
        body: {
          "content": "<style>.x { color: #3d3d3a; }</style>",
          "filename": "sample.css",   # 可选，用于后缀判定（.html/.css/.typ/.py/.md）
          "only": ["rgba", "coolgray"]  # 可选规则子集
        }
        返回 validate_kami.py --format json 的原样输出。
        """
        content = data.get('content', '')
        if not content:
            self._send_error(400, "'content' is required in body")
            return
        filename = data.get('filename') or 'ad-hoc.css'
        only = data.get('only') or []
        if only and not isinstance(only, list):
            self._send_error(400, "'only' must be an array of rule names")
            return

        import subprocess as _sp
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'-{filename}',
                                          delete=False, dir=OUTPUT_DIR,
                                          encoding='utf-8') as f:
            f.write(content)
            tmp_path = f.name

        try:
            script = str(Path(__file__).parent / 'validate_kami.py')
            args = [sys.executable, script, '--format', 'json', tmp_path]
            if only:
                args += ['--only', ','.join(only)]
            result = _sp.run(args, capture_output=True, text=True, timeout=30)
            # 退出码 0=干净 1=有 error；JSON 在 stdout
            if result.returncode not in (0, 1):
                self._send_error(500,
                    f'validate_kami internal error (exit={result.returncode}): {result.stderr}')
                return
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                self._send_error(500, f'invalid JSON from validator: {e}')
                return
            # 对外抹掉临时文件路径，只留原 filename hint
            for issue in payload.get('issues', []):
                issue['file'] = filename
            self._send_json(payload)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

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
