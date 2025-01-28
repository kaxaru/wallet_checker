import httpx
import ssl
from urllib.parse import urlparse
from httpx import Proxy

def get_client(proxy: str = None) -> httpx.Client:
    transport = httpx.HTTPTransport()
    _pr = proxy['http']
    if proxy:
        parsed_proxy = urlparse(_pr)
        if parsed_proxy.scheme not in ["http", "https", "socks4", "socks5"]:
            raise ValueError(f"Unsupported proxy scheme: {parsed_proxy.scheme}")

    proxy_object = Proxy(url=_pr)
    # transport = httpx.HTTPTransport(proxy=proxy_object)
    # Настройка TLS
    ssl_context = ssl.create_default_context()
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
    ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1  # Renegotiation not allowed

    ssl_context.set_ciphers(
        ":".join(
            [
                "TLS_AES_128_GCM_SHA256",
                "TLS_AES_256_GCM_SHA384",
                "TLS_CHACHA20_POLY1305_SHA256",
                "ECDHE-ECDSA-AES128-GCM-SHA256",
                "ECDHE-RSA-AES128-GCM-SHA256",
                "ECDHE-ECDSA-AES256-GCM-SHA384",
                "ECDHE-RSA-AES256-GCM-SHA384",
                "ECDHE-ECDSA-CHACHA20-POLY1305",
                "ECDHE-RSA-CHACHA20-POLY1305",
            ]
        )
    )
    # ssl_context.set_ecdh_curve("secp521r1")
    # ssl_context.set_ecdh_curve("secp256k1")
    ssl_context.set_ecdh_curve("prime256v1")
    ssl_context.set_ecdh_curve("secp384r1")
    # ssl_context.set_ecdh_curve("X25519:P-256:P-384")
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE  # отключение проверки сертификатов

    transport = httpx.HTTPTransport(proxy=proxy_object)

    transport = httpx.HTTPTransport(
        http2=True,
        verify=ssl_context,
        retries=3,
        trust_env=False,  # Отключение доверия к переменным окружения
    )
    client = httpx.Client(
        http2=True,
        transport= transport,
        proxies=proxy_object,
        timeout=httpx.Timeout(15.0, connect=15.0),
        limits=httpx.Limits(max_connections=None, max_keepalive_connections=10),
    )

    return client