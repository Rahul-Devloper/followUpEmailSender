# Follow-Up Email Sender

An automated tool for sending personalized follow-up emails for job applications using Python.

## 📋 Features

- Automated email sending with rate limiting
- Configurable SMTP settings
- JSON-based application metadata
- Dry run mode for testing
- Logging support

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- SMTP server access (Yahoo Mail account)
- Application password for SMTP authentication

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Rahul-Devloper/followUpEmailSender.git
   cd follow-up-email
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   Create a `.env` file in the project root: SMTP is subject to your sender email address domain. Each SMTP is different. Check your email sender's SMTP config and put them in your .env accordingly.
   ```env
   EMAIL=your-email@mail.com
   APP_PASSWORD=your-app-password
   SMTP_HOST=smtp.mail.domain.com
   SMTP_PORT_SSL=portNumber
   RATE_LIMIT_SECONDS=1.0
   SMTP_DEBUG=True
   SENDER_NAME=Your Name
   ```

   For other email providers:
   - Gmail: Use `smtp.gmail.com` and port `465`
   - Outlook: Use `smtp-mail.outlook.com` and port `587`
   - Custom domain: Check your email provider's SMTP settings

   Note: Make sure to:
   - Generate an app password from your email provider's security settings
   - Never commit the `.env` file to version control
   - Keep your APP_PASSWORD secure
## 📁 Project Structure

```
follow-up-email/
├── src/
│   ├── email_generator.py
│   └── metadata/
│       └── applications.json
├── .env
├── requirements.txt
└── README.md
```

## 📝 Configuration

### Application Metadata

Update `src/metadata/applications.json` with your application details:

```json
{
  "applications": [
    {
      "company": "Example Corp",
      "role": "Software Engineer",
      "emails": [
        "hr@example.com",
        "recruiting@example.com"
      ]
    }
  ]
}
```

### Debug Mode

Set `DRY_RUN = True` in the code to test without sending actual emails.

## 🔧 Usage

Run the email sender:
```bash
python src/email_generator.py
```

## 📚 Logging

The application logs all operations to the console with timestamps and severity levels.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.