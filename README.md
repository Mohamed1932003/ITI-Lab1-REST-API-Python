# Lab Assignment 1 - Egypt Gold & Currency Assistant

A command-line assistant that uses the **MetalpriceAPI** REST API to show
today's gold prices per gram in EGP (24K / 22K / 21K / 18K), silver, and the
main currencies against the Egyptian pound, with the change since yesterday.
It can also calculate the value of your gold and convert between currencies.

## Requirements covered
| Requirement | Where |
|---|---|
| API integration | `MetalPriceClient._request()` uses `requests` |
| JSON parsing | `response.json()` + `MarketSnapshot.from_json()` |
| Class implementation | `MarketSnapshot` (data) and `MetalPriceClient` (API + cache) |
| Formatted output | `show_dashboard()`, `value_my_gold()`, `convert_money()` using `rich` |
| Virtual environment | `venv/` |
| Environment variables | `METALPRICE_API_KEY` in `.env`, loaded with `python-dotenv` |

## Setup and run (Windows)
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## API key
1. Create a free account at https://metalpriceapi.com and copy your key.
2. Copy `.env.example` to `.env` and put the key in it:
```
METALPRICE_API_KEY=your_key_here
```
`.env` and `cache.json` are listed in `.gitignore`.

## Notes
- Responses are cached in `cache.json` for 6 hours to save the free quota.
- Prices are international prices at the official exchange rate.
  Shop prices in Egypt add workmanship and may differ.
- Data source: metalpriceapi.com (attribution required on the free plan).
