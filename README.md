# 🌱on-leads

## About
On-leads is part of the on-lamp group's initiative to automate CRM management using AI agents for various functions. This tool provides functionalities to automate lead research and contact management. Currently, it integrates with Notion, but we aim to extend it to other platforms as well. We believe that AI agents do not necessarily need new interfaces and should not always be visible. Instead, they should perform tasks in the background, communicating with us and each other without requiring a new graphical interface. The beauty lies in integrating with existing solutions. For this reason, we have an input mechanism that works like a worker taking commands from Telegram and outputs that are handled within Notion, just like a smart worker.

## License

This project is licensed under the MIT License - see below:

```
MIT License

Copyright (c) 2024 Onlamp

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Core Functionalities

### Web Contact Scraping
The bot includes a powerful web scraping feature that helps you gather contact information from websites:
- Command: `/crawl <url>`
- Automatically extracts email addresses from the provided webpage
- Creates new lead entries in your Notion database
- Stores additional context like name and profile

### Automated Email Draft Generation
The bot can automatically generate personalized first-contact emails:
- Single lead: `/draft <lead_id> <prompt>` 
- Batch processing: `/draft_all <prompt>`
- Uses AI to generate contextually relevant email content
- Considers lead's profile
- Automatically saves drafts to your Notion emails database
- Links emails to corresponding leads in the database

## Future Development & Contributions

We are actively working on new features including:
- Advanced contact enrichment using multiple data sources
- Automated follow-up email scheduling
- Integration with additional CRM platforms
- Smart lead scoring based on interaction history
- Custom AI agent training capabilities

We welcome community contributions! If you have ideas for new features or improvements, please:
1. Open an issue to discuss your proposal
2. Submit a pull request with your implementation
3. Help us make on-leads even better for everyone

## Setup

### 1. Create Virtual Environment
```bash
python -m venv venv
```

### 2. Activate Virtual Environment
#### On Windows:
```bash
.\venv\Scripts\activate
```

#### On Unix or MacOS:
```bash
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up Notion Integration
1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Name your integration (e.g., "on-leads")
4. Select the workspace where you'll create your databases
5. For Capabilities, ensure the following are enabled:
   - Read content
   - Update content
   - Insert content
6. Submit to create the integration
7. Copy the "Internal Integration Token" - you'll need this for the `NOTION_TOKEN` in your `.env` file

### 5. Set up Notion Databases
Before configuring the environment variables, you need to create two databases in your Notion workspace:

1. **Leads Database** with the following properties:
   - Name (Title)
   - Contact_Status (Select)
   - Profile (Rich Text)
   - Linkedin (URL)
   - Company (Relation)
   - ID (Unique ID)
   - Emails (Relation)
   - Email_Address (Email)

2. **Emails Database** with these properties:
   - Recipient (Relation)
   - Text (Rich Text)
   - Email_Status (Select)
   - Type (Select)
   - Object (Title)

The exact schema definitions can be found in `src/constants/schemas.py`. Make sure to create these databases with the exact property names and types as specified.

To get the database IDs:
1. Open each database in your browser
2. The URL will look like: `https://www.notion.so/{workspace}/{database_id}?v={view_id}`
3. Copy the `database_id` portion (32 characters long) for each database
4. You'll need these IDs for the `.env` configuration

Important: After creating each database, you must share it with your integration:
1. Open the database
2. Click the `...` menu in the top-right corner
3. Click "Add connections"
4. Select your integration from the list
5. Repeat for both databases

### 6. Create a Telegram Bot
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Start a chat with BotFather and send the command `/newbot`
3. Follow the instructions to:
   - Choose a name for your bot
   - Choose a username for your bot (must end in 'bot')
4. BotFather will give you a token. Save this token as you'll need it for the `.env` file

### 7. Configure Environment Variables
1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit the `.env` file and fill in your credentials:
   - `TELEGRAM_TOKEN`: Your Telegram Bot Token
   - `NOTION_TOKEN`: Your Notion API Integration Token
   - `GOOGLE_API_KEY`: Your Google API Key for Gemini AI
   - `NOTION_LEADS_DATABASE_ID`: Your Notion Leads Database ID
   - `NOTION_EMAILS_DATABASE_ID`: Your Notion Emails Database ID
   - `FIRECRAWL_API_KEY`: Your Firecrawl API key
   - `OPENAI_API_KEY`: Your OpenAI API key

## Running the Telegram Bot

Simply run:
```bash
python bot.py
```

The bot will automatically load the configuration from the `.env` file and start running.
