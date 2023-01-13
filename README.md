# Leek<br>[![GitHub Actions][actions-img]][actions-url] [![Patreon][patreon-img]][patreon-url] [![PayPal][paypal-img]][paypal-url] [![Discord][discord-img]][discord-url]

> WARNING: Please note that Leek is an experimental work in progress project, and as such, the API might change unexpectedly at any time.

Leek is a simple and easy to use Discord Bot Framework. It allows you to easily create and manage Discord Bots for any server, no matter the size.

## Download

* [GitHub Releases](https://github.com/LeekByLemon/Leek/releases)
* [GitHub Actions](https://github.com/LeekByLemon/Leek/actions) (experimental versions)

## Installation

Run the following command to install the latest version of Leek from master.

```
pip install https://github.com/LeekByLemon/Leek/archive/master.zip
```

If you want to install from git for developent purposes, run the following commands:

```
git clone https://github.com/LeekByLemon/Leek.git leek
cd leek
pip install -e .
```

## Usage

Leek allows you to configure your bot just by using a `.env` file. On this `.env` file, you can configure the following options:

* DISCORD_TOKEN: The Discord Bot Token (required)
* DISCORD_DEBUG: Whether Debug features are enabled or not (optional, set it to anything other than zero to enable)
* DISCORD_COGS: The Cogs to load by default (optional, separated by comas in the format `library.path:Class`)
* SQL_HOST: The host for the SQL connection (optional, defaults to `127.0.0.1`)
* SQL_PORT: The port for the SQL connection (optional, defaults to `3306`)
* SQL_USER: The user for the SQL connection (optional, but required if you want to use SQL support)
* SQL_PASSWORD: The password for the SQL connection (optional, but required if you want to use SQL support)
* SQL_DB: The name of the SQL database (optional, defaults to `discord`)

After setting the required configuration options, you can start the bot by using `python -m leek`.

[actions-img]: https://img.shields.io/github/actions/workflow/status/LeekByLemon/Leek/main.yml?branch=master&label=actions
[actions-url]: https://github.com/LeekByLemon/Leek/actions
[patreon-img]: https://img.shields.io/badge/support-patreon-FF424D.svg
[patreon-url]: https://www.patreon.com/lemonchan
[paypal-img]: https://img.shields.io/badge/support-paypal-0079C1.svg
[paypal-url]: https://paypal.me/justalemon
[discord-img]: https://img.shields.io/badge/discord-join-7289DA.svg
[discord-url]: https://discord.gg/Cf6sspj
