"""
Lab Assignment 1 - Working with a Public REST API Using Python
Project: Egypt Gold & Currency Assistant

A command-line assistant that uses the MetalpriceAPI REST API to:
  1. Show today's gold prices per gram in EGP (24K / 21K / 18K) + silver,
     and the main currencies against the Egyptian pound, with the change
     since yesterday.
  2. Calculate how much your gold is worth (grams + karat + workmanship).
  3. Convert any amount between EGP, USD, EUR, GBP, SAR, AED and KWD.

To save the free plan's monthly quota, every response is cached in
cache.json and reused for a few hours.

API docs: https://metalpriceapi.com/documentation
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

API_BASE = "https://api.metalpriceapi.com/v1"
SYMBOLS = ["EGP", "EUR", "GBP", "SAR", "AED", "KWD", "XAU", "XAG"]
CURRENCY_NAMES = {
    "USD": "US Dollar",
    "EUR": "Euro",
    "GBP": "British Pound",
    "SAR": "Saudi Riyal",
    "AED": "UAE Dirham",
    "KWD": "Kuwaiti Dinar",
    "EGP": "Egyptian Pound",
}
GRAMS_PER_OUNCE = 31.1034768
KARATS = (24, 22, 21, 18)
CACHE_FILE = Path(__file__).with_name("cache.json")
CACHE_HOURS = 6

console = Console()


# ---------------------------------------------------------------------------
# 1) Class that stores and organizes the data returned by the API
# ---------------------------------------------------------------------------
class MarketSnapshot:
    """Prices of one day. All rates are 'units per 1 USD', like the API."""

    def __init__(self, rates, timestamp):
        self.rates = rates
        self.timestamp = timestamp

    @classmethod
    def from_json(cls, data):
        rates = {code: float(data["rates"][code]) for code in SYMBOLS}
        rates["USD"] = 1.0
        return cls(rates, data.get("timestamp", int(time.time())))

    @property
    def updated_at(self):
        return datetime.fromtimestamp(self.timestamp, timezone.utc).strftime("%d %b %Y")

    def to_egp(self, code):
        """Price of 1 unit of a currency in Egyptian pounds."""
        return self.rates["EGP"] / self.rates[code]

    def convert(self, amount, from_code, to_code):
        usd = amount / self.rates[from_code]
        return usd * self.rates[to_code]

    def ounce_usd(self, metal):
        return 1 / self.rates[metal]

    def gold_gram_egp(self, karat=24):
        gram_24k = self.ounce_usd("XAU") / GRAMS_PER_OUNCE * self.rates["EGP"]
        return gram_24k * karat / 24

    def silver_gram_egp(self):
        return self.ounce_usd("XAG") / GRAMS_PER_OUNCE * self.rates["EGP"]


# ---------------------------------------------------------------------------
# 2) Client class that talks to the REST API (with a small file cache)
# ---------------------------------------------------------------------------
class MetalPriceClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.cache = self._load_cache()
        # One session = one secure connection reused for all requests,
        # so the slow connection setup happens only once.
        self.session = requests.Session()

    def _load_cache(self):
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save_cache(self):
        CACHE_FILE.write_text(json.dumps(self.cache, indent=2), encoding="utf-8")

    def _request(self, endpoint):
        params = {"api_key": self.api_key, "base": "USD",
                  "currencies": ",".join(SYMBOLS)}
        try:
            response = self.session.get(f"{API_BASE}/{endpoint}", params=params,
                                        timeout=(20, 30))
            data = response.json()                      # JSON -> Python dict
        except requests.exceptions.Timeout:
            raise RuntimeError("The server is too slow right now. Try again in a minute.")
        except requests.exceptions.RequestException as error:
            raise RuntimeError(f"Could not reach the server: {error}")
        except ValueError:
            raise RuntimeError(f"Unexpected reply from the server ({response.status_code}).")

        if not data.get("success"):
            error = data.get("error", {})
            code = error.get("code", error.get("statusCode"))
            info = error.get("info", error.get("message"))
            messages = {
                101: "No API key was sent. Check your .env file.",
                102: "The API key is invalid. Check your .env file.",
                104: "Too many requests. Try again in a minute.",
                105: "This month's free quota is used up.",
            }
            raise RuntimeError(messages.get(code, f"API error {code}: {info}"))
        return data

    def get_snapshot(self, endpoint):
        """endpoint is 'latest' or a date like '2026-11-17'."""
        entry = self.cache.get(endpoint)
        if entry and time.time() - entry["saved_at"] < CACHE_HOURS * 3600:
            return MarketSnapshot.from_json(entry["data"])

        data = self._request(endpoint)
        self.cache[endpoint] = {"saved_at": time.time(), "data": data}
        self._save_cache()
        return MarketSnapshot.from_json(data)


# ---------------------------------------------------------------------------
# 3) Formatted output
# ---------------------------------------------------------------------------
def change_text(today, yesterday):
    if yesterday is None or yesterday == 0:
        return "[dim]-[/dim]"
    percent = (today - yesterday) / yesterday * 100
    if abs(percent) < 0.01:
        return "[dim]0.00%[/dim]"
    if percent > 0:
        return f"[green]+{percent:.2f}%[/green]"
    return f"[red]{percent:.2f}%[/red]"


def show_dashboard(today, yesterday):
    gold = Table(title="Gold & Silver (per gram)", header_style="bold yellow")
    gold.add_column("Item")
    gold.add_column("Price (EGP)", justify="right")
    gold.add_column("vs yesterday", justify="right")
    for karat in KARATS:
        old = yesterday.gold_gram_egp(karat) if yesterday else None
        gold.add_row(f"Gold {karat}K", f"{today.gold_gram_egp(karat):,.2f}",
                     change_text(today.gold_gram_egp(karat), old))
    gold.add_row("Gold pound (8 g, 21K)", f"{today.gold_gram_egp(21) * 8:,.2f}",
                 change_text(today.gold_gram_egp(21),
                             yesterday.gold_gram_egp(21) if yesterday else None))
    gold.add_row("Silver 999", f"{today.silver_gram_egp():,.2f}",
                 change_text(today.silver_gram_egp(),
                             yesterday.silver_gram_egp() if yesterday else None))

    money = Table(title="Currencies in Egyptian pounds", header_style="bold cyan")
    money.add_column("Currency")
    money.add_column("1 unit = EGP", justify="right")
    money.add_column("vs yesterday", justify="right")
    for code in ("USD", "EUR", "GBP", "SAR", "AED", "KWD"):
        old = yesterday.to_egp(code) if yesterday else None
        money.add_row(f"{code}  {CURRENCY_NAMES[code]}", f"{today.to_egp(code):,.2f}",
                      change_text(today.to_egp(code), old))

    console.print()
    console.print(gold)
    console.print(money)
    console.print(
        f"[dim]Global ounce: ${today.ounce_usd('XAU'):,.2f}  |  "
        f"Prices of: {today.updated_at}  |  Data: metalpriceapi.com\n"
        "Note: these are international prices at the official rate; "
        "shop prices in Egypt add workmanship and may differ.[/dim]"
    )


def ask_number(prompt, default=None):
    while True:
        text = console.input(prompt).strip()
        if not text and default is not None:
            return default
        try:
            value = float(text)
            if value >= 0:
                return value
        except ValueError:
            pass
        console.print("[yellow]Please enter a positive number.[/yellow]")


def value_my_gold(today):
    console.print("\n[bold yellow]Value of your gold[/bold yellow]")
    grams = ask_number("Weight in grams: ")
    karat = 0
    while karat not in KARATS:
        karat = int(ask_number(f"Karat {KARATS}: "))
    making = ask_number("Workmanship per gram in EGP (Enter = 0): ", default=0)

    gram_price = today.gold_gram_egp(karat)
    selling = grams * gram_price
    buying = grams * (gram_price + making)

    table = Table(show_header=False, box=None)
    table.add_column(style="bold")
    table.add_column(justify="right")
    table.add_row("Gram price", f"{gram_price:,.2f} EGP")
    table.add_row("Value if you sell", f"[green]{selling:,.2f} EGP[/green]")
    if making:
        table.add_row("Cost if you buy new", f"{buying:,.2f} EGP")
        table.add_row("Workmanship you pay", f"[red]{buying - selling:,.2f} EGP[/red]")
    table.add_row("In US dollars", f"${today.convert(selling, 'EGP', 'USD'):,.2f}")
    console.print(Panel(table, title=f"{grams:g} g of {karat}K gold", border_style="yellow"))


def convert_money(today):
    console.print("\n[bold cyan]Currency converter[/bold cyan]")
    codes = list(CURRENCY_NAMES)
    console.print("Available: " + ", ".join(codes))
    amount = ask_number("Amount: ")
    from_code = console.input("From (e.g. USD): ").strip().upper()
    to_code = console.input("To (e.g. EGP): ").strip().upper()
    if from_code not in codes or to_code not in codes:
        console.print("[yellow]Unknown currency code.[/yellow]")
        return
    result = today.convert(amount, from_code, to_code)
    console.print(Panel(f"[bold]{amount:,.2f} {from_code}  =  {result:,.2f} {to_code}[/bold]",
                        border_style="cyan"))


# ---------------------------------------------------------------------------
# 4) Main program
# ---------------------------------------------------------------------------
def load_api_key():
    load_dotenv()                                       # reads the .env file
    key = os.getenv("METALPRICE_API_KEY")
    if not key or key == "your_key_here":
        console.print("[red]Put your METALPRICE_API_KEY in the .env file first.[/red]")
        sys.exit(1)
    return key


def main():
    console.print(Panel.fit("[bold yellow]Egypt Gold & Currency Assistant[/bold yellow]",
                            border_style="yellow"))
    client = MetalPriceClient(load_api_key())

    with console.status("Fetching prices from the server "
                        "(the first time can take up to 30 seconds)..."):
        try:
            today = client.get_snapshot("latest")
        except RuntimeError as error:
            console.print(f"[red]{error}[/red]")
            sys.exit(1)
        # On the free plan "latest" is the previous day's closing price,
        # so we compare it with the day before the date of that price.
        price_day = datetime.fromtimestamp(today.timestamp, timezone.utc).date()
        day_before = (price_day - timedelta(days=1)).isoformat()
        try:
            yesterday = client.get_snapshot(day_before)
        except RuntimeError:
            yesterday = None                # the dashboard still works without it

    show_dashboard(today, yesterday)

    while True:
        console.print("\n[bold]1[/bold] Value my gold   [bold]2[/bold] Convert money   "
                      "[bold]3[/bold] Show prices again   [bold]0[/bold] Exit")
        choice = console.input("Choose: ").strip()
        if choice == "1":
            value_my_gold(today)
        elif choice == "2":
            convert_money(today)
        elif choice == "3":
            show_dashboard(today, yesterday)
        elif choice == "0":
            console.print("Bye!")
            break
        else:
            console.print("[yellow]Choose 0, 1, 2 or 3.[/yellow]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:          # Ctrl+C -> exit quietly, no traceback
        console.print("\n[yellow]Stopped. Bye![/yellow]")
