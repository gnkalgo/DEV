"""Curated instrument master — security_id values for Dhan NSE_EQ where known."""

INSTRUMENTS = [
    {"symbol": "NIFTY50", "display_name": "Nifty 50", "exchange": "NSE", "segment": "INDEX", "security_id": "13", "instrument_token": "13"},
    {"symbol": "BANKNIFTY", "display_name": "Nifty Bank", "exchange": "NSE", "segment": "INDEX", "security_id": "25", "instrument_token": "25"},
    {"symbol": "FINNIFTY", "display_name": "Nifty Fin Service", "exchange": "NSE", "segment": "INDEX", "security_id": "27", "instrument_token": "27"},
    {"symbol": "NIFTYNEXT50", "display_name": "Nifty Next 50", "exchange": "NSE", "segment": "INDEX", "security_id": "38", "instrument_token": "38"},
    {"symbol": "NIFTYMIDCAP", "display_name": "Nifty Midcap 100", "exchange": "NSE", "segment": "INDEX", "security_id": "442", "instrument_token": "442"},
    {"symbol": "INDIAVIX", "display_name": "India VIX", "exchange": "NSE", "segment": "INDEX", "security_id": "21", "instrument_token": "21"},
    {"symbol": "SENSEX", "display_name": "SENSEX", "exchange": "BSE", "segment": "INDEX", "security_id": "1", "instrument_token": "1"},
    {"symbol": "RELIANCE", "display_name": "Reliance Industries", "exchange": "NSE", "segment": "EQUITY", "security_id": "2885", "instrument_token": "2885"},
    {"symbol": "TCS", "display_name": "Tata Consultancy Services", "exchange": "NSE", "segment": "EQUITY", "security_id": "11536", "instrument_token": "11536"},
    {"symbol": "INFY", "display_name": "Infosys", "exchange": "NSE", "segment": "EQUITY", "security_id": "1594", "instrument_token": "1594"},
    {"symbol": "HDFCBANK", "display_name": "HDFC Bank", "exchange": "NSE", "segment": "EQUITY", "security_id": "1333", "instrument_token": "1333"},
    {"symbol": "ICICIBANK", "display_name": "ICICI Bank", "exchange": "NSE", "segment": "EQUITY", "security_id": "4963", "instrument_token": "4963"},
    {"symbol": "SBIN", "display_name": "State Bank of India", "exchange": "NSE", "segment": "EQUITY", "security_id": "3045", "instrument_token": "3045"},
    {"symbol": "NIFTY", "display_name": "Nifty 50", "exchange": "NSE", "segment": "INDEX", "security_id": "13", "instrument_token": "13"},
]

_SYMBOL_ALIASES = {
    "NIFTY": "NIFTY50",
    "NIFTY 50": "NIFTY50",
    "BANK NIFTY": "BANKNIFTY",
    "NIFTY BANK": "BANKNIFTY",
}
