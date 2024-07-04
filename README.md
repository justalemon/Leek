# Leek<br>[![GitHub Actions][actions-img]][actions-url] [![Patreon][patreon-img]][patreon-url] [![PayPal][paypal-img]][paypal-url] [![Discord][discord-img]][discord-url]

Leek is a simple and easy to use Discord Bot created by Lemon. It contains a very diverse set of tools that can be enabled or disabled as you wish.

Right now, it has the following features:

- Hyperping: Reports Healthchecks to Hyperping when the Bot is running
- Log Diagnoser: Diagnoses the Log files of ScriptHookVDotNet, giving a quick suggestion for fixes
- Native Lookup: Allows you to search for GTA V and RDR2 natives from Discord
- Moderation: Some simple moderation functions that are not yet implemented in Discord
- Tags: Allows you to write, save and show different Tags with messages

## Download

* [GitHub Image](https://github.com/justalemon/Leek/pkgs/container/leek)
* [GitHub Releases](https://github.com/justalemon/Leek/releases)
* [GitHub Actions](https://github.com/justalemon/Leek/actions) (experimental versions)

## Installation

The recommended way to use the Leek bot is via the Docker container. You can pull the image with `docker pull ghcr.io/justalemon/leek`, which can then be used directly or via Docker Compose. You can use the provided [docker-compose.yml](docker-compose.yml) as a template.

You can also install the Python package directly to the system interpreter with `pip install https://github.com/justalemon/Leek/archive/master.zip`. 

If you want to install from git for development purposes, you can also run the following commands:

```
git clone https://github.com/justalemon/Leek.git leek
cd leek
pip install -e .
```

## Usage

Leek allows you to configure your bot just by using environment variables via the terminal or a .env files. The following configuration options are available:

#### Bot

* DISCORD_TOKEN: The Discord Bot Token (required)
* DISCORD_DEBUG: Whether Debug features are enabled or not (optional, set it to anything other than zero to enable)
* DISCORD_COGS: The Cogs to load by default (optional, separated by comas in the format `library.path:Class`)
* SQL_HOST: The host for the SQL connection (optional, defaults to `127.0.0.1`)
* SQL_PORT: The port for the SQL connection (optional, defaults to `3306`)
* SQL_USER: The user for the SQL connection (optional, but required if you want to use SQL support)
* SQL_PASSWORD: The password for the SQL connection (optional, but required if you want to use SQL support)
* SQL_DB: The name of the SQL database (optional, defaults to `discord`)

#### Hyperping

- HYPERPING_URL: The URL that will be used for the pings
- HYPERPING_DELAY: The delay used to trigger between each ping

#### Mod Comments

- MODCOMMENTS_DRIVER: The Selenium driver to use for fetching the web pages

After setting the required configuration options, you can start the bot as usual. If you are using the package directly, you can start the bot by using `python -m leek`.

[actions-img]: https://img.shields.io/github/actions/workflow/status/justalemon/Leek/main.yml?branch=master&label=actions
[actions-url]: https://github.com/justalemon/Leek/actions
[patreon-img]: https://img.shields.io/badge/support-patreon-FF424D.svg
[patreon-url]: https://www.patreon.com/lemonchan
[paypal-img]: https://img.shields.io/badge/support-paypal-0079C1.svg
[paypal-url]: https://paypal.me/justalemon
[discord-img]: https://img.shields.io/badge/discord-join-7289DA.svg
[discord-url]: https://discord.gg/Cf6sspj
