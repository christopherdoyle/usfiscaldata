from fiscaldata import FiscalData, Filter

client = FiscalData()
endpoint = client.v2.debt.tror.data_act_compliance
filter_ = Filter()
filter_["record_date"] <= "2016-01-01"
response = endpoint(filter=filter_)
while True:
    count = response.meta["count"]
    print(f"Retrieved {count} records")
    if count == 0:
        break
    response = response.next_page()
    if response is None:
        break
