from backend.compliance.guardrails import (
    filter_compliant,
    has_fetched_at,
    has_required_blur_flag,
    is_compliant_camera,
    is_private_ip,
    is_residential_org,
    url_has_credentials,
    url_has_private_host,
)


class TestPrivateIP:
    def test_rfc1918_blocks(self):
        for ip in ("10.0.0.1", "10.255.255.255", "172.16.0.1", "172.31.255.255",
                   "192.168.0.1", "192.168.255.254"):
            assert is_private_ip(ip), ip

    def test_loopback_is_private(self):
        assert is_private_ip("127.0.0.1")
        assert is_private_ip("127.255.255.255")

    def test_link_local_is_private(self):
        assert is_private_ip("169.254.0.1")

    def test_public_ips_are_not_private(self):
        for ip in ("8.8.8.8", "1.1.1.1", "208.67.222.222", "9.9.9.9"):
            assert not is_private_ip(ip), ip

    def test_documentation_blocks_are_treated_as_private(self):
        # RFC 5737 TEST-NET blocks are reserved and must not appear in output.
        for ip in ("192.0.2.5", "198.51.100.5", "203.0.113.5"):
            assert is_private_ip(ip), ip

    def test_ipv6_loopback_and_ula(self):
        assert is_private_ip("::1")
        assert is_private_ip("fc00::1")
        assert is_private_ip("fe80::1")

    def test_hostnames_return_false(self):
        assert not is_private_ip("example.com")
        assert not is_private_ip("camera.example.org")


class TestURLChecks:
    def test_rfc1918_url_rejected(self):
        for url in (
            "http://10.0.0.1/stream",
            "http://192.168.1.1:8080",
            "rtsp://172.16.0.5/live",
            "http://127.0.0.1/cam",
        ):
            assert url_has_private_host(url), url

    def test_public_url_allowed(self):
        assert not url_has_private_host("http://camera.city.gov/feed.m3u8")
        assert not url_has_private_host("https://8.8.8.8/stream")

    def test_credentials_in_url_detected(self):
        assert url_has_credentials("http://admin:admin@camera.example.com/")
        assert url_has_credentials("rtsp://user:pass@1.2.3.4/live")
        assert not url_has_credentials("http://camera.example.com/login")


class TestResidential:
    def test_residential_patterns_detected(self):
        for label in (
            "Comcast Residential Internet",
            "Verizon Wireless",
            "AT&T Internet Services",
            "Spectrum Cable",
            "Residential DSL",
        ):
            assert is_residential_org(label), label

    def test_commercial_passes(self):
        for label in (
            "City of Philadelphia",
            "Pennsylvania DOT",
            "Akamai Technologies",
            "Cloudflare",
        ):
            assert not is_residential_org(label), label


class TestCameraResultGuardrails:
    def _good(self, **over):
        base = {
            "id": "osm_x",
            "lat": 39.0,
            "lon": -75.0,
            "source": "osm",
            "label": "test",
            "url": "https://camera.example.gov/feed",
            "thumbnail_url": None,
            "blur_required": True,
            "fetched_at": "2026-05-20T00:00:00+00:00",
        }
        base.update(over)
        return base

    def test_good_record_passes(self):
        ok, reasons = is_compliant_camera(self._good())
        assert ok, reasons

    def test_private_url_rejected(self):
        ok, reasons = is_compliant_camera(self._good(url="http://192.168.1.10/cam"))
        assert not ok and "private" in " ".join(reasons)

    def test_creds_in_url_rejected(self):
        ok, reasons = is_compliant_camera(
            self._good(url="http://admin:admin@cam.example.com/")
        )
        assert not ok and "credentials" in " ".join(reasons)

    def test_thumbnail_requires_blur_flag(self):
        ok, reasons = is_compliant_camera(
            {"url": "https://x.example.com/",
             "thumbnail_url": "https://x.example.com/thumb.jpg",
             "fetched_at": "2026-05-20T00:00:00+00:00"}
        )
        assert not ok and "blur_required" in " ".join(reasons)

    def test_missing_fetched_at_rejected(self):
        ok, reasons = is_compliant_camera({"url": "https://x.example.com/"})
        assert not ok and "fetched_at" in " ".join(reasons)

    def test_blur_flag_helper(self):
        assert has_required_blur_flag({"thumbnail_url": None})
        assert has_required_blur_flag({"thumbnail_url": "x", "blur_required": True})
        assert not has_required_blur_flag({"thumbnail_url": "x"})
        assert not has_required_blur_flag({"thumbnail_url": "x", "blur_required": "yes"})

    def test_fetched_at_helper(self):
        assert has_fetched_at({"fetched_at": "2026-05-20T00:00:00+00:00"})
        assert not has_fetched_at({})
        assert not has_fetched_at({"fetched_at": ""})


def test_filter_compliant_drops_bad_records():
    bad = {"url": "http://10.0.0.1/cam", "fetched_at": "2026-05-20T00:00:00+00:00"}
    good = {
        "id": "x", "url": "https://cam.example.gov/", "blur_required": True,
        "fetched_at": "2026-05-20T00:00:00+00:00",
    }
    out = filter_compliant([bad, good])
    assert out == [good]
