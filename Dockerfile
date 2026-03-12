FROM python:3.14-slim AS build
COPY . /src
RUN python -m pip install --upgrade pip \
    && python -m pip install setuptools wheel
RUN cd /src \
    && python setup.py bdist_wheel -d /deps


FROM python:3.14-slim

COPY --from=build /deps/* /deps/
COPY production.ini /app/config.ini
COPY requirements.txt .

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        libffi-dev \
        libxml2-dev \
        libxslt1-dev \
    && python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt \
    && python -m pip install --no-index --find-links=file:///deps -U scielo-kernel \
    && apt-get purge -y --auto-remove build-essential git libffi-dev libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/* \
    && rm requirements.txt \
    && rm -rf /deps

WORKDIR /app

ENV PYTHONUNBUFFERED 1

USER nobody
# CMD ["pserve", "/app/config.ini"]
CMD ["gunicorn", "documentstore.wsgi:application", "--bind", "0.0.0.0:6543", "--workers=3", "--threads=4", "--timeout=1000", "--log-level", "DEBUG"]
