from usfiscaldata import filter_


class TestFilter:
    def test_empty_filter(self):
        filter = filter_.Filter()
        assert filter.format_for_param() == ""

    def test_equals(self):
        filter = filter_.Filter()
        filter["a"] = "b"
        assert filter.format_for_param() == "a:eq:b"

    def test_lt(self):
        filter = filter_.Filter()
        filter["a"] < "b"
        assert filter.format_for_param() == "a:lt:b"

    def test_lte(self):
        filter = filter_.Filter()
        filter["a"] <= "b"
        assert filter.format_for_param() == "a:lte:b"

    def test_gt(self):
        filter = filter_.Filter()
        filter["a"] > "b"
        assert filter.format_for_param() == "a:gt:b"

    def test_gte(self):
        filter = filter_.Filter()
        filter["a"] >= "b"
        assert filter.format_for_param() == "a:gte:b"

    def test_isin_method(self):
        filter = filter_.Filter()
        filter["a"].isin(["b", "c"])
        assert filter.format_for_param() == "a:in:(b,c)"

    def test_isin_symbol(self):
        filter = filter_.Filter()
        filter["a"] ^ ["b", "c"]
        assert filter.format_for_param() == "a:in:(b,c)"

    def test_set_many_filters(self):
        filter = filter_.Filter()
        filter["a"] == 1
        filter["b"] >= 2
        filter["c"] ^ (5, 10)
        assert filter.format_for_param() == "a:eq:1,b:gte:2,c:in:(5,10)"
