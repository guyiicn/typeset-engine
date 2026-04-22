# typeset-engine — 统一文档渲染引擎
# PDF / PPTX / DOCX 生成 + 中文字体 + 文件对比
# 基于 finrobot 镜像（已有字体和基础依赖）
FROM finrobot:v2

LABEL maintainer="guyii"
LABEL description="Typeset Engine: PDF/PPTX/DOCX rendering with CJK fonts"
LABEL version="1.0"

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 系统依赖（base image 已有字体和大部分工具）
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    imagemagick \
    diffutils \
    librsvg2-bin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv 2>/dev/null || true

# 增量安装
RUN pip install --no-cache-dir \
    fpdf2 \
    cairosvg \
    python-docx \
    click \
    plotly \
    "kaleido>=1.0.0" \
    google-genai \
    python-dotenv \
    weasyprint \
    pypdf \
    || echo "Some packages may have warnings, continuing"

# Chrome 系统依赖 + 中文字体 + 公文字体 + FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk-bridge2.0-0 libcups2 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libxkbcommon0 libpango-1.0-0 \
    libcairo2 libasound2 \
    fonts-noto-cjk \
    fonts-arphic-ukai \
    fonts-arphic-uming \
    fonts-cwtex-fs \
    fonts-cwtex-heib \
    fonts-cwtex-kai \
    fonts-cwtex-ming \
    fonts-liberation \
    ffmpeg \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

# Kaleido v1 需要 Chrome — 必须成功安装
RUN plotly_get_chrome -y

# Typst 排版引擎（PDF 生成）— 先装 curl+xz，下载安装，再清理
RUN apt-get update && apt-get install -y --no-install-recommends curl xz-utils \
    && curl -fsSL https://github.com/typst/typst/releases/download/v0.14.0/typst-x86_64-unknown-linux-musl.tar.xz \
       | tar -xJ --strip-components=1 -C /usr/local/bin/ \
    && typst --version \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ═══════════════════════════════════════════
# 复制项目文件
# ═══════════════════════════════════════════
COPY . /app/

# 安装项目自带字体（方正小标宋、SimHei、仿宋等）
RUN if [ -d /app/fonts ]; then \
        cp /app/fonts/*.ttf /app/fonts/*.TTF /app/fonts/*.TTC /app/fonts/*.otf \
           /usr/local/share/fonts/ 2>/dev/null; \
        fc-cache -fv; \
    fi

# 注册字体到 matplotlib
RUN python -c "\
import matplotlib.font_manager as fm; \
fm._load_fontmanager(try_read_cache=False); \
print(f'Fonts registered: {len(fm.fontManager.ttflist)}'); \
cjk = [f.name for f in fm.fontManager.ttflist if 'CJK' in f.name or 'WenQuanYi' in f.name]; \
print(f'CJK fonts: {len(set(cjk))}'); \
"

# 修复并验证
RUN pip install --no-cache-dir python-pptx python-docx && \
    python -c "import reportlab, pptx, click; print('All OK')"

EXPOSE 9090

# 默认启动 HTTP API 服务；也可覆盖为 CLI 模式
CMD ["python", "scripts/server.py"]
