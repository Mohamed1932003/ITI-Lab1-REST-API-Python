# Egypt Gold & Currency Assistant

ITI Lab Assignment 1 - Working with a Public REST API Using Python.

A simple Python program that gets live prices from the internet and shows:

- Gold prices per gram in Egyptian pounds (24K, 22K, 21K, 18K) and silver
- Currency prices in Egyptian pounds (USD, EUR, GBP, SAR, AED, KWD)
- The change since the day before (green = up, red = down)
- A calculator for the value of your gold
- A currency converter

The data comes from the free **MetalpriceAPI**.

---

## Step 1: Get your free API key

1. Go to https://metalpriceapi.com
2. Click **Get Free API Key** (or **Sign Up**).
3. Create an account with your email. No credit card is needed.
4. Confirm your email if they ask you.
5. Log in and open the **Dashboard**.
6. Copy the **API Key** you see there (a long code of letters and numbers).

---

## Step 2: Download the project

```
git clone https://github.com/Mohamed1932003/ITI-Lab1-REST-API-Python.git
cd ITI-Lab1-REST-API-Python
```

---

## Step 3: Create the virtual environment and install the libraries

Windows:
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Mac / Linux:
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Step 4: Put your API key in a .env file

1. Make a copy of the file `.env.example` and name it `.env`
2. Open `.env` and replace `your_key_here` with your key:

```
METALPRICE_API_KEY=paste_your_key_here
```

Never share this file or upload it to GitHub. It is already in `.gitignore`.

---

## Step 5: Run the program

```
python main.py
```

Then choose from the menu:

```
1 Value my gold   2 Convert money   3 Show prices again   0 Exit
```

---

## Project files

| File | What it does |
|---|---|
| `main.py` | The program |
| `requirements.txt` | The libraries the program needs |
| `.env.example` | Example of the `.env` file |
| `.gitignore` | Files that should not be uploaded |

## How the requirements are covered

| Requirement | Where |
|---|---|
| API integration | `MetalPriceClient` sends the request with `requests` |
| JSON parsing | `response.json()` and `MarketSnapshot.from_json()` |
| Class | `MarketSnapshot` stores the prices, `MetalPriceClient` talks to the API |
| Formatted output | Tables and panels made with the `rich` library |
| Virtual environment | `venv` |
| Environment variables | The API key is in `.env` and loaded with `python-dotenv` |

## Notes

- The free plan updates prices once a day.
- The program saves the prices in `cache.json` for 6 hours, so it does not use your free requests every time.
- The prices are international prices. Gold shops in Egypt add workmanship, so their prices can be different.
- Data source: metalpriceapi.com
