Wallet checker (Debank / Rabby)

A Python implementation of the same idea as https://github.com/nazavod777/wallets_checker.

Project structure

- `main.py` is the entry point.
- `configure.py` contains runtime configuration and menu setup.
- `app/` contains the application code.
- `data/` contains config and proxy files.
- `wallets/` contains address and wallet input files.
- `results/` contains output files.

Run

```powershell
python main.py
```

data/config.json

Use `data/config.json.example` as a template.

- `debank_config.parse_tokens` enables token parsing
- `debank_config.parse_nfts` enables NFT parsing
- `debank_config.parse_pools` enables pool parsing
- `two_captcha_apikey` is your 2captcha API key
- `proxy_format` is the proxy scheme, for example `http` or `socks5`

wallets

There are two runtime files in the `wallets` folder:

- `address.txt` for raw addresses
- `wallets.txt` for mnemonics / private keys

Supported wallet formats:

1. `mnemonic` -> takes the first 100 wallets from the mnemonic
2. `mnemonic;number` -> takes wallets from 1 to `number`
3. `mnemonic;;3,5,7-10` -> takes specific wallet indexes from the mnemonic

Proxy (`data/connection.txt`)

Use `data/connection.txt.example` as a template.

Format:

`host:port:login:password`
