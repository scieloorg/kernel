FROM python:3.7-alpine AS build
COPY . /src
RUN pip install --upgrade pip \
    && pip install wheel
RUN cd /src \
    && python setup.py bdist_wheel -d /deps


FROM python:3.7-alpine
MAINTAINER scielo-dev@googlegroups.com

COPY --from=build /deps/* /deps/
COPY production.ini /app/config.ini
COPY requirements.txt .

RUN apk add --no-cache --virtual .build-deps \
        make gcc libxml2-dev libxslt-dev musl-dev g++ git libffi-dev \
    && apk add libxml2 libxslt \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-index --find-links=file:///deps -U scielo-kernel \
    && apk --purge del .build-deps \
    && rm requirements.txt \
    && rm -rf /deps

WORKDIR /app

ENV PYTHONUNBUFFERED 1

USER nobody
# CMD ["pserve", "/app/config.ini"]
CMD ["gunicorn", "documentstore.wsgi:application", "--bind", "0.0.0.0:6543", "--workers=3", "--worker-class=gevent", "--timeout=1000", "--worker-connections=1000", "--log-level DEBUG"]
