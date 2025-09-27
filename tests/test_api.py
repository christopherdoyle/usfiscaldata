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
