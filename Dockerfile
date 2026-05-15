# typeset-engine — 统一文档渲染引擎
# PDF / PPTX / DOCX 生成 + 中文字体 + 图表/技术图/AI配图
# 自包含构建：不依赖任何外部 base image
FROM python:3.12-slim-bookworm

LABEL maintainer="guyii"
LABEL description="Typeset Engine: PDF/PPTX/DOCX rendering with CJK fonts (standalone)"
LABEL version="3.0"

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ═══════════════════════════════════════════
# 系统依赖：CLI 工具 + WeasyPrint/Cairo + Chrome 运行库 + 字体
# ═══════════════════════════════════════════
RUN apt-get update && apt-get install -y --no-install-recommends \
        # 渲染相关 CLI
        poppler-utils \
        imagemagick \
        diffutils \
        librsvg2-bin \
        ffmpeg \
        # 下载 typst 用
        curl \
        xz-utils \
        ca-certificates \
        # WeasyPrint / Cairo / Pango 运行时
        libcairo2 \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libharfbuzz0b \
        libgdk-pixbuf-2.0-0 \
        libffi8 \
        shared-mime-info \
        # Kaleido(v1) 需要的 Chrome 运行库
        libnss3 libatk-bridge2.0-0 libatk1.0-0 libcups2 libxcomposite1 \
        libxdamage1 libxfixes3 libxrandr2 libgbm1 libxkbcommon0 \
        libasound2 libdrm2 libxshmfence1 libx11-xcb1 \
        # 字体（中文 + 拉丁替代）
        fonts-noto-cjk \
        fonts-noto-cjk-extra \
        fonts-arphic-ukai \
        fonts-arphic-uming \
        fonts-cwtex-fs \
        fonts-cwtex-heib \
        fonts-cwtex-kai \
        fonts-cwtex-ming \
        fonts-liberation \
        fontconfig \
    && fc-cache -fv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ═══════════════════════════════════════════
# Python 依赖
# ═══════════════════════════════════════════
RUN pip install --upgrade pip wheel \
 && pip install \
        # 文档生成
        python-docx \
        python-pptx \
        weasyprint \
        fpdf2 \
        reportlab \
        pypdf \
        pdfplumber \
        # 图表 / 图像
        plotly \
        "kaleido>=1.0.0" \
        pillow \
        cairosvg \
        matplotlib \
        # AI / 工具
        google-genai \
        python-dotenv \
        click \
        jsonschema

# ═══════════════════════════════════════════
# Kaleido v1 需要 Chrome（无头），由 plotly 提供脚本下载
# ═══════════════════════════════════════════
RUN plotly_get_chrome -y

# ═══════════════════════════════════════════
# Typst 0.14.0（PDF 排版引擎）
# ═══════════════════════════════════════════
RUN curl -fsSL https://github.com/typst/typst/releases/download/v0.14.0/typst-x86_64-unknown-linux-musl.tar.xz \
        | tar -xJ --strip-components=1 -C /usr/local/bin/ typst-x86_64-unknown-linux-musl/typst \
 && typst --version

# ═══════════════════════════════════════════
# 项目文件
# ═══════════════════════════════════════════
COPY . /app/

# 安装项目自带字体（方正小标宋、SimHei、仿宋等）
RUN if [ -d /app/fonts ]; then \
        cp -f /app/fonts/*.ttf /app/fonts/*.TTF /app/fonts/*.TTC /app/fonts/*.otf \
              /usr/local/share/fonts/ 2>/dev/null || true; \
        fc-cache -fv; \
    fi

# 注册字体到 matplotlib 缓存
RUN python -c "import matplotlib.font_manager as fm; \
fm._load_fontmanager(try_read_cache=False); \
print(f'Fonts registered: {len(fm.fontManager.ttflist)}'); \
cjk = sorted({f.name for f in fm.fontManager.ttflist if 'CJK' in f.name or 'WenQuanYi' in f.name or 'Noto' in f.name}); \
print(f'CJK families: {len(cjk)} -> {cjk[:8]}')"

# Smoke test
RUN python -c "import docx, pptx, plotly, weasyprint, pypdf, PIL, matplotlib, click; print('Python deps OK')" \
 && which typst rsvg-convert ffmpeg

EXPOSE 9090

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9090/health', timeout=5)" || exit 1

CMD ["python", "scripts/server.py"]
