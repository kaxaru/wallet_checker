# Wallet checker (Debank/ Rabby)

A completely identical solution is https://github.com/nazavod777/wallets_checker, only written in python. Since Go is not very convenient for me, I decided to make an implementation for myself


## data/config.json 
Enable/disable token/nft/pool parsing
2captcha_apikey - apikey with 2captcha

## wallets
There are two files in the wallets folder. The first one is for addresses, the second one is for mnemonics/private keys.
The format is the same everywhere. Possible variants:
1) mnemonic - takes the first 100 from the current mnemonic
2) mnemonic; number - where number is from the first to the current address in order.
3) mnemonic;; 3, 5, 7-10 - arbitrary order. Where 3, 5, 7, 8, 9, 10 accounts on the mnemonic will be used.

## Proxy(data/connection)
I use the web3easy proxy format 
address:port:login:password

proxy -> socks5