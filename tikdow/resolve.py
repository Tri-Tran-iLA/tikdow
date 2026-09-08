"""Resolve TikTok short links in the cancellable worker process."""
import json
import sys
from .core import validate_url, is_short_url


def resolve_url(url):
    from curl_cffi import requests
    url = validate_url(url)
    with requests.Session(impersonate='chrome') as session:
        # Validate every redirect destination before requesting it.
        for _ in range(8):
            response = session.get(url, allow_redirects=False, timeout=20, stream=True)
            try:
                if response.status_code in (301, 302, 303, 307, 308):
                    from urllib.parse import urljoin
                    url = validate_url(urljoin(url, response.headers.get('Location', '')))
                    if not is_short_url(url):
                        return url
                    continue
                response.raise_for_status()
                if is_short_url(url):
                    raise ValueError('Cannot resolve short link. Paste the full post URL / Hãy dán link bài đầy đủ.')
                return url
            finally:
                response.close()
    raise ValueError('Too many redirects / Quá nhiều chuyển hướng.')


if __name__ == '__main__':
    try:
        print('TIKDOW_URL:' + json.dumps(resolve_url(sys.argv[1])), flush=True)
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
