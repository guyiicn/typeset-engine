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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv 2>/dev/null || true

# 增量安装（base image 已有 reportlab, matplotlib, pdfplumber 等）
RUN pip install --no-cache-dir \
    fpdf2 \
    cairosvg \
    python-docx \
    click \
    || echo "Some packages may have warnings, continuing"

# ═══════════════════════════════════════════
# 复制项目文件
# ═══════════════════════════════════════════
COPY . /app/

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

CMD ["python", "scripts/engine.py"]
