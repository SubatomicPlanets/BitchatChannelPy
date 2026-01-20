# BitchatChannelPy
<img width="700" alt="Picture" src="https://github.com/user-attachments/assets/f31e4c21-1337-4b06-a59c-2deca1f0a8c2" />

A simple Python script that is compatible with the Bitchat IOS and Android apps

## Features
- Connect to any Bitchat geohash channel
- Change your name with the `/name` command
- Customizable parameters in the script for full control
- The best feature of them all: Simplicity. The entire script is just 150 lines long!

> [!NOTE]
> Direct messages, Bluetooth mesh, and TOR are **not** supported.


## How to run:
```
git clone https://github.com/SubatomicPlanets/BitchatChannelPy.git
cd BitchatChannelPy
// make a venv here if needed
pip install -r requirements.txt
py BitchatChannel.py
```

## Who is this for?
- Anyone wanting a simple CLI interface for Bitchat
- Anyone wanting to understand Bitchat better
- Anyone who wants to write a simple bot or something interesting! The possibilities are endless!

## Security
- Any security-related code is handled by the [rust-nostr](https://github.com/rust-nostr/nostr) library
- Nothing is saved permanently! Of course, if you would like to save some info, then you can quickly add some code to do so!
- The Relay CSV file is directly downloaded from the official Bitchat repository. If you want the up-to-date version or simply don't trust my file, then download it yourself [here](https://github.com/permissionlesstech/bitchat/blob/main/relays/online_relays_gps.csv)
