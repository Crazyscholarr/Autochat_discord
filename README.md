# Autochat_discord

A Discord bot that automates chat interactions by sending and replying to messages in specified guilds and channels. Built with Python, it uses the Discord API, Grok for generating natural responses, and supports proxy usage for scalability.

## Features
- **Automated Chat**: Sends messages and replies to existing messages in Discord channels.

- **Grok Integration**: Generates human-like responses using xAI's Grok API.

- **Multi-account Support**: Manages multiple Discord accounts for simultaneous chatting.

- **Proxy Support**: Uses proxies to avoid rate limits and enhance anonymity.

- **Customizable Configuration**: Configures guilds, channels, message frequency, and more via config.yaml.

- **Colorful Logging**: Logs actions with colored output (account index in yellow, channel ID in yellow, message content in green).

- **Infinite Run Mode**: Runs continuously until manually stopped, with configurable pauses between messages.

- **Reply Detection**: Detects and responds to replies to the bot's messages with context-aware responses.

## Requirements

- Python 3.8  or higher
- Discord account tokens (stored in accounts.txt)
- Proxies (optional, stored in proxies.txt)
- Grok API key (from xAI)
- Capsolver API key (for solving captchas during guild joining)
## Installation 

- 1. Clone the repository (or download the code):
```bash
CMD 
git clone https://github.com/Crazyscholarr/Autochat_discord.git
cd Autochat_discord
```
- 2. Install dependencies:
```bash
pip install -r requirements.txt
```
- 3. Prepare configuration files:

     - Create accounts.txt with Discord tokens (one per line).
```plain
token1
token2
```
     - (Optional) Create proxies.txt with proxy addresses (one per line, format: host:port).
```plain
192.168.1.1:8080
192.168.1.2:8080
```


    - Update `` config.yaml `` with your settings (guilds, channels, API keys, etc.).
```bash
SETTINGS:
  THREADS: 5
  SHUFFLE_ACCOUNTS: true
  ACCOUNTS_RANGE: [0, 0]
  EXACT_ACCOUNTS_TO_USE: []
  ATTEMPTS: 3
  PAUSE_BETWEEN_ATTEMPTS: [3, 5]
AI_CHATTER:
  GUILDS:
    - GUILD_ID: "1335195624928313425"
      CHANNEL_IDS: ["1335474283610243113"]
      MESSAGES_PER_ACCOUNT: [1, 3]
  REPLY_PERCENTAGE: 50
  PAUSE_BETWEEN_MESSAGES: [30, 60]
  LEAVE_GUILD: false
GROK:
  API_KEYS: ["your_grok_api_key"]
  MODEL: "grok-3"
  PROXY_FOR_GROK: ""
CAPSOLVER:
  API_KEY: "your_capsolver_api_key"
PROXY:
  TIMEOUT: 5
```
### Usage

1. Run the bot:
```bash
python main.py

```

2. Monitor logs:

Logs are displayed in the terminal with colored output:
```plain
Example log:

[20:47:30 | 22-04-2025] [Crazyscholar @ Discord] | SUCCESS | Tài khoản - 1 | Trả lời tin nhắn trong channel 1335474283610243113: haha bò lạc vào nghe buồn cười ghê bác còn giữ khách quen đông không

```

3. Stop the bot:

Press ``Ctrl+C`` to stop the bot gracefully.

### Project Structure
```bash
Autochat_discord/
├── main.py               # Main script to run the bot
├── model/
│   └── discord/
│       ├── auth.py       # Handles Discord authentication
│       ├── chat.py       # Manages sending/replying to messages
│       ├── guild.py      # Manages guild joining/leaving
│       └── token_checker.py # Validates Discord tokens
├── utils/
│   ├── config.py         # Loads configuration from config.yaml
│   ├── constants.py      # Defines constants (e.g., Account class)
│   ├── proxy.py          # Handles proxy validation
│   └── writer.py         # Updates account status
├── prompts.py            # System prompts for Grok
├── capsolver.py          # Capsolver integration for captchas
├── config.yaml           # Configuration file
├── accounts.txt          # Discord account tokens
├── proxies.txt           # Proxy list (optional)
└── README.md             # Project documentation
```
### Contributing

Fork the repository.

Create a new branch (```git checkout -b feature/your-feature```).

Commit your changes (```git commit -m "Add your feature"```).

Push to the branch (``git push origin feature/your-feature``).

Open a Pull Request.

### License

This project is licensed under the MIT License.

### Contact

For issues or questions, contact Crazyscholarr or open an issue on GitHub.