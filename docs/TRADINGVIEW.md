# GnKAlgo TradingView inbound alert

POST the JSON body to your inbound webhook URL.

```json
{
  "symbol": "{{ticker}}",
  "action": "BUY",
  "qty": 1,
  "paper_mode": true
}
```

Optional header: `X-Gnkalgo-Secret: <secret shown once at creation>`
