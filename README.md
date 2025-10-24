# Follow-Up Email Project

This project automates the process of sending follow-up emails for job applications. It uses Python to read application metadata from a JSON file and sends personalized emails based on that data.

## Project Structure

- `src/email_generator.py`: Contains the main logic for sending follow-up emails.
- `src/metadata/applications.json`: Stores metadata for the applications, including company names, roles, and email addresses.
- `.env`: Contains environment variables for SMTP configuration and email credentials.
- `requirements.txt`: Lists the Python dependencies required for the project.
- `README.md`: Documentation for the project.

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd follow-up-email
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory and add your SMTP configuration and email credentials:
   ```
   SMTP_HOST=<your_smtp_host>
   SMTP_PORT_SSL=<your_smtp_port>
   EMAIL=<your_email>
   APP_PASSWORD=<your_app_password>
   ```

4. Update the `src/metadata/applications.json` file with your application details.

## Usage

Run the email generator script to send follow-up emails:
```
python src/email_generator.py
```

## License

This project is licensed under the MIT License.