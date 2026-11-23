from urllib.parse import urljoin
from urllib import robotparser

import requests


class RobotsInfo:
    def __init__(self, exists=False, content="", declared_sitemaps=None, error=None):
        self.exists = exists
        self.content = content
        self.declared_sitemaps = declared_sitemaps or []
        self.error = error
        self.parser = robotparser.RobotFileParser()

    def allows(self, url: str, user_agent: str) -> bool:
        if not self.exists:
            return True
        return self.parser.can_fetch(user_agent, url)


def fetch_robots(base_url: str, session: requests.Session, user_agent: str, timeout: float) -> RobotsInfo:
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        response = session.get(robots_url, timeout=timeout, headers={"User-Agent": user_agent})
        if response.status_code >= 400:
            return RobotsInfo(exists=False, error=f"robots.txt returned HTTP {response.status_code}")
        content = response.text
    except requests.RequestException as exc:
        return RobotsInfo(exists=False, error=str(exc))

    parser = robotparser.RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(content.splitlines())
    sitemaps = []
    for line in content.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            if key.strip().lower() == "sitemap" and value.strip():
                sitemaps.append(value.strip())

    info = RobotsInfo(exists=True, content=content, declared_sitemaps=sitemaps)
    info.parser = parser
    return info
