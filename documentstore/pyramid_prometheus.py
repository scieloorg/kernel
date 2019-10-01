from time import time
import pkg_resources

from pyramid.tweens import EXCVIEW
from prometheus_client import start_http_server, Histogram, Gauge, Summary, Info

_VERSION = pkg_resources.get_distribution("scielo-kernel").version

APP_INFO = Info(
    "kernel",
    "Info about this instance of the application",
)
APP_INFO.info({"version": _VERSION})

REQUEST_DURATION_SECONDS = Histogram(
    "kernel_restfulapi_request_duration_seconds",
    "Time spent processing HTTP requests",
    ["handler", "method"],
)
REQUESTS_INPROGRESS = Gauge(
    "kernel_restfulapi_requests_inprogress",
    "Current number of HTTP requests being processed",
)
RESPONSE_SIZE_BYTES = Summary(
    "kernel_restfulapi_response_size_bytes",
    "Summary of response size for HTTP requests",
    ["handler"],
)


def tween_factory(handler, registry):
    def tween(request):
        REQUESTS_INPROGRESS.inc()
        response = None
        start = time()
        try:
            response = handler(request)
            return response

        finally:
            duration = time() - start
            if request.matched_route:
                route_pattern = request.matched_route.pattern
            else:
                route_pattern = ""
            REQUEST_DURATION_SECONDS.labels(route_pattern, request.method).observe(
                duration
            )
            if response:
                RESPONSE_SIZE_BYTES.labels(route_pattern).observe(
                    # content_length é None em casos de exceção
                    response.content_length
                    or 0
                )
            REQUESTS_INPROGRESS.dec()

    return tween


def includeme(config):
    settings = config.registry.settings
    if not settings["kernel.app.prometheus.enabled"]:
        return None

    try:
        start_http_server(settings["kernel.app.prometheus.port"])
    except OSError as exc:
        # https://github.com/prometheus/client_python/issues/155
        # TODO: Remover o tratamento do OSError quando o issue referenciado
        # acima tiver sido resolvido.
        if exc.errno != 98:
            raise

    config.add_tween("documentstore.pyramid_prometheus.tween_factory", over=EXCVIEW)
