# Gmail Unsubscribe Script

**This Python script automates the process of unsubscribing from emails in your Gmail account.** It uses the Gmail API, BeautifulSoup for parsing email content, and Selenium with the Edge WebDriver for browser automation.

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3
- [Edge WebDriver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)
- A Google Cloud account

## Setup Instructions

### 1. Clone the Repository
- Clone the repository to your local machine using the following command:
```bash
git clone https://github.com/MatteoGuidii/Algorithm_Unsub_Management.git
```
Navigate to the cloned repository's directory:
```bash
cd email-subscriptions-managment
```

### 2. Download Edge WebDriver
- Download the Edge WebDriver from the [Microsoft Edge Developer website](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/) and place the executable in the same directory as the project.

### 3. Google Cloud Console Configuration
- Navigate to the [Google Cloud Console](https://console.cloud.google.com/).
- Create a new project or select an existing one.
- Enable the Gmail API for your project.
- Go to "Credentials" and create OAuth 2.0 client credentials.
- Add `http://localhost:8080/` to the Authorized redirect URIs.
- Download the client configuration JSON file and place it in the project folder.

### 4. Client Secret File
- Replace the `client_secret_30643909904-mjs4cc25qjpod0cm954hvhabsd7pfsv9.apps.googleusercontent.com.json` in `quickstart.py` with the path to your downloaded client secret file.

### 5. Install Python Dependencies
- Install the required Python libraries using:
  ```bash
  pip install google-auth
  pip install google-auth-oauthlib
  pip install google-api-python-client
  pip install bs4
  pip install selenium

### Running the Scripts
To run the script, execute the following command in your terminal:
```bash
  python quickstart.py
  python home.py
```
Follow the on-screen instructions to authenticate your Gmail account.

### Important Notes
- **Compatibility:** This script currently operates effectively with the **Edge** browser. Please note that this is an initial approach and the script may have limitations or encounter issues in its current form.
- **Development Status:** The script is a **work in progress**. Expect continuous updates and improvements as development progresses.
- **Security:** It is crucial to keep your client secret file secure and confidential. Do not share this file publicly, as it contains sensitive information essential for accessing your Gmail account through the script.
- **Permissions:** Ensure that you have read and write access to the Gmail account you're using with the script. In the Google Cloud Console, under the "Test Users" section, include the email address that you will use with the script. This step is necessary for the script to function correctly and access your emails.
- **Usage:** This script is intended for personal use. Users should respect privacy, adhere to applicable laws, and follow Gmail's terms of service when using this script.

### License
This project is licensed under the MIT License. This means you can freely use, modify, distribute, and sell this software, with the only requirement being to include the original copyright and license notice in any copies or substantial portions of the software.

For the full license text, see the [LICENSE](LICENSE.md) file in this repository.
