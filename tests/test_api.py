import pytest
import requests

from fiscaldata import api


class TestEndpointBuilder:
    def test(self):
        class Stub:
            def __init__(self):
                self.call_log = []

            def do_request(self, *a, **kw):
                self.call_log.append((a, kw))

        o = Stub()
        builder = api.EndpointBuilder(o, path_segments=[])
        builder.v1.imaginary.api(page=100)

        assert o.call_log == [(("v1/imaginary/api", {"page": 100}), {})]


class TestFiscalData:
    def test_getattr_returns_endpoint_builder(self):
        fd = api.FiscalData()
        eb = fd.v1.accounting.od.auctions_query
        assert isinstance(eb, api.EndpointBuilder)
        assert eb._path_segments == ["v1", "accounting", "od", "auctions_query"]

    def test_format_request_params(self):
        fd = api.FiscalData()
        f = api.Filter()
        f["field1"] == "value1"
        params = {
            "filter": f,
            "sort": "field2",
            "page": 50,
        }
        formatted = fd.format_request_params(params)
        assert formatted == {
            "filter": "field1:eq:value1",
            "sort": "field2",
            "page": "50",
        }

    def test_format_request_params_with_in(self):
        fd = api.FiscalData()
        f = api.Filter()
        f["field1"].isin(["a", "b", "c"])
        params = {
            "filter": f,
            "sort": "field2",
            "page": 50,
        }
        formatted = fd.format_request_params(params)
        assert formatted == {
            "filter": "field1:in:(a,b,c)",
            "sort": "field2",
            "page": "50",
        }

    def test_do_request_success(self, requests_mock):
        requests_mock.get(
            "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query",
            json={
                "data": [{"a": 1}, {"a": 2}],
                "meta": {"count": 2, "total-count": 100, "total-pages": 50},
                "links": {"self": "", "first": "", "last": "", "next": "", "prev": ""},
            },
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

        fd = api.FiscalData()
        resp = fd.do_request(
            "v1/accounting/od/auctions_query",
            {"page": "1", "sort": "field"},
        )
        assert isinstance(resp, api.Response)
        assert resp.data == [{"a": 1}, {"a": 2}]
        assert resp.meta == {"count": 2, "total-count": 100, "total-pages": 50}
        assert resp.links == {
            "self": "",
            "first": "",
            "last": "",
            "next": "",
            "prev": "",
        }
        assert resp._endpoint == "v1/accounting/od/auctions_query"
        assert resp._params == {"page": "1", "sort": "field"}

    def test_do_request__given_non_json_response__raises(self, requests_mock):
        requests_mock.get(
            "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query",
            text="Not JSON",
            status_code=200,  # OK status but not JSON
            headers={"Content-Type": "text/plain"},
        )

        fd = api.FiscalData()
        with pytest.raises(NotImplementedError, match="Expected json"):
            fd.do_request(
                "v1/accounting/od/auctions_query",
                {"page": "1", "sort": "field"},
            )

    def test_do_request_failure(self, requests_mock):
        requests_mock.get(
            "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query",
            json={
                "error": "Bad Request",
                "message": "Invalid filter",
            },
            status_code=400,
            headers={"Content-Type": "application/json"},
        )

        fd = api.FiscalData()
        with pytest.raises(requests.HTTPError, match="400 Client Error"):
            fd.do_request(
                "v1/accounting/od/auctions_query",
                {"page": "1", "sort": "field"},
            )
