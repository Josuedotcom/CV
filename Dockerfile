# CV Generator — portable container
# Python 3.11 + LaTeX + Streamlit bundled so anyone can run it with: docker build && docker run
# Base python:3.11-slim keeps the image small; LaTeX is installed with apt for both texlive-latex-extra and latexmk.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        texlive-latex-extra \
        texlive-fonts-recommended \
        lmodern \
        latexmk \
        wget \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN uv sync

EXPOSE 8501

CMD ["streamlit", "run", "web/app.py"]
