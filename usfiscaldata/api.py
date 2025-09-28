import urllib
import logging
from dataclasses import dataclass

import requests

from usfiscaldata.filter_ import Filter


BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/"

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Response:
    response: requests.Response
    data: list
    meta: dict
    links: dict
    _fiscal_data: "FiscalData"
    _endpoint: str
    _params: dict

    def __repr__(self):
        return f"{self.__class__.__name__}(reponse={self.response}, data=<{len(self.data)} items>)"

    @property
    def df(self):
        import pandas as pd
        from usfiscaldata.datatypes import cast_df

        df = pd.DataFrame(self.data)
        df = cast_df(
            df, data_types=self.meta["dataTypes"], data_formats=self.meta["dataFormats"]
        )
        return df

    def next_page(self):
        return self._get_page("next")

    def prev_page(self):
        return self._get_page("prev")

    def first_page(self):
        return self._get_page("first")

    def last_page(self):
        return self._get_page("last")

    def _get_page(self, which):
        link = self.links.get(which)
        if not link:
            return None
        # link is a query string like '&page%5Bnumber%5D=2&page%5Bsize%5D=100'
        # Remove leading '&' if present
        params = dict(urllib.parse.parse_qsl(link.lstrip("&")))
        return self._fiscal_data.do_request(self._endpoint, {**self._params, **params})

    def log_metadata(self):
        meta_fields = [
            ("count", "Record count for the response"),
            ("total-count", "Total number of rows"),
            ("total-pages", "Total number of pages"),
        ]
        for key, desc in meta_fields:
            logger.info("%s: %s", desc, self.meta.get(key, "-"))


class EndpointBuilder:
    """Proxy class for FiscalData dot-accessor endpoint construction."""

    def __init__(self, fiscal_data, path_segments=None):
        self._fiscal_data = fiscal_data
        self._path_segments = path_segments or []

    def __getattr__(self, name):
        return EndpointBuilder(self._fiscal_data, self._path_segments + [name])

    def __call__(self, **params) -> Response:
        return self._fiscal_data.do_request(self.endpoint, params)

    @property
    def endpoint(self):
        return "/".join(self._path_segments)

    def all(self, **params) -> Response:
        """Fetch all pages of results for the endpoint.

        This method will make multiple requests to fetch all available data, based on the
        `total-pages` metadata field in the response.

        Note that this may result in a large number of requests and a large amount of data
        being loaded into memory. Use with caution.

        Example:

            >>> api = FiscalData()
            >>> endpoint = api.v2.debt.tror.data_act_compliance
            >>> response = endpoint.all()  # doctest: +SKIP

        """
        logger.info("Fetching all pages of results for '%s'", self.endpoint)
        params = params.copy()
        params["page[number]"] = 1
        params["page[size]"] = 100
        logger.info("Requesting page 1/unknown")
        first_response = self(**params)
        total_pages = first_response.meta.get("total-pages", 1)
        total_count = first_response.meta.get("total-count", 0)
        logger.info("Total count = %d", total_count)
        all_data = first_response.data.copy()

        for page in range(2, total_pages + 1):
            logger.info("Requesting page %d/%d", page, total_pages)
            params.update({"page[number]": page})
            page_response = self(**params)
            all_data.extend(page_response.data)

        if len(all_data) != total_count:
            logger.warning(
                "Expected count (%d) does not match actual count of returned data (%d)",
                total_count,
                len(all_data),
            )

        return Response(
            response=first_response.response,
            data=all_data,
            meta=first_response.meta,
            links=first_response.links,
            _fiscal_data=self._fiscal_data,
            _endpoint="/".join(self._path_segments),
            _params=params,
        )


class FiscalData:
    """Interface to the Treasury FiscalData API.

    Access to the APi endpoints is via dynamic attributes corresponding to the endpoint
    URL parts. See example below.

    Example:

        >>> api = FiscalData()
        >>> endpoint = api.v2.debt.tror.data_act_compliance
        >>> response = endpoint()  # doctest: +SKIP

    """

    def __call__(self, endpoint: str) -> EndpointBuilder:
        parts = endpoint.split(".")
        return EndpointBuilder(self, parts)

    def __getattr__(self, name) -> EndpointBuilder:
        return EndpointBuilder(self, [name])

    @staticmethod
    def format_request_params(params: dict) -> dict:
        formatted_params = {}
        for key, value in params.items():
            if key == "filter" and isinstance(value, Filter):
                formatted_value = value.format_for_param()
            else:
                formatted_value = str(value)
            formatted_params[key] = formatted_value
        return formatted_params

    def do_request(self, endpoint: str, params: dict) -> Response:
        formatted_params = self.format_request_params(params)
        full_url = urllib.parse.urljoin(BASE_URL, endpoint)
        response = requests.get(full_url, params=formatted_params)
        return self.handle_response(response, endpoint, params)

    def handle_response(self, response: requests.Response, endpoint=None, params=None):
        content_type = response.headers.get("Content-Type", "unknown")
        if content_type != "application/json":
            raise NotImplementedError(f"Expected json, got '{content_type}'")
        full_data = response.json()

        if not response.ok:
            error = full_data.get("error", "unknown error")
            msg = full_data.get("message", "unknown error")
            logger.error("Request failure (%s): '%s'", error, msg)
        response.raise_for_status()

        data = full_data.get("data", {})
        meta = full_data.get("meta", {})
        links = full_data.get("links", {})
        return Response(
            response=response,
            data=data,
            meta=meta,
            links=links,
            _fiscal_data=self,
            _endpoint=endpoint,
            _params=params or {},
        )
