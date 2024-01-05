import os
import datetime
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from bs4 import BeautifulSoup
import base64
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

CACHE_DIR = 'cache'
CACHE_EXPIRY_HOURS = 24  # Cache expiry time in hours

def gmail_authenticate():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret_30643909904-mjs4cc25qjpod0cm954hvhabsd7pfsv9.apps.googleusercontent.com.json", SCOPES)
            creds = flow.run_local_server(port=8080)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except Exception as e:
        print(f"Failed to create Gmail API client: {e}")
        return None
    

def is_cache_valid(cache_file):
    if not os.path.exists(cache_file):
        return False
    file_time = datetime.datetime.fromtimestamp(os.path.getmtime(cache_file))
    return (datetime.datetime.now() - file_time).total_seconds() < CACHE_EXPIRY_HOURS * 3600


def get_cache_file_name(user_id, max_results, past_days):
    return os.path.join(CACHE_DIR, f'cache_{user_id}_{max_results}_{past_days}.json')


def list_messages(service, user_id, max_results=100, past_days=90):
    """List messages from the Gmail account."""
    cache_file = get_cache_file_name(user_id, max_results, past_days)

    if is_cache_valid(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)

    try:
        messages = []
        after_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=past_days)).strftime('%Y/%m/%d')
        # Query to search for specific terms in both Promotions and Primary categories
        query = f'after:{after_date} ((category:promotions) OR (category:primary "newsletter" OR "Newsletter" OR "subscription"))'

        response = service.users().messages().list(userId=user_id, q=query).execute()
        messages.extend(response.get('messages', []))

        while 'nextPageToken' in response and len(messages) < max_results:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, pageToken=page_token, q=query).execute()
            messages.extend(response.get('messages', []))

        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        with open(cache_file, 'w') as f:
            json.dump(messages[:max_results], f)

        return messages[:max_results]
    except HttpError as error:
        print(f'An error occurred: {error}')
        return []


def generate_subscriptions_json(unique_senders):
    sorted_senders = sorted(unique_senders)
    with open('subscriptions.json', 'w') as file:
        json.dump(sorted_senders, file)


def get_email_sender(service, message_id):
    try:
        message = service.users().messages().get(userId='me', id=message_id, format='metadata', metadataHeaders=['From']).execute()
        headers = message.get('payload', {}).get('headers', [])
        sender_info = next((header['value'] for header in headers if header['name'] == 'From'), None)
        
        # Extract the sender's name from the sender_info
        sender_name = sender_info.split('<')[0].strip().strip('"')
        return sender_name
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None


def get_latest_message_id_for_sender(service, user_id, sender_name):
    try:
        query = f'from:({sender_name})'
        response = service.users().messages().list(userId=user_id, q=query, maxResults=1).execute()
        messages = response.get('messages', [])
        
        if not messages:
            return None
        
        return messages[0]['id']  # Return the ID of the first (latest) message
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None


def find_unsubscribe_link(service, message_id):
    try:
        # Fetch the email body
        message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        parts = message.get('payload').get('parts')
        body_data = None
        for part in parts:
            if part['mimeType'] == 'text/html':
                body_data = part['body']['data']
                break
        if not body_data:
            return None
        decoded_data = base64.urlsafe_b64decode(body_data).decode('utf-8')
        soup = BeautifulSoup(decoded_data, 'html.parser')

        # Using regex to find links with case-insensitive unsubscribe keywords
        unsubscribe_keywords = ['unsubscribe', 'click here', 'here', 'opt-out', 'opt out']
        secondary_keywords = ['click here', 'here']
        unsubscribe_links = []

        for a in soup.find_all('a', href=True):
            link_text = a.text.lower()
            if any(re.search(rf"\b{keyword}\b", link_text, re.IGNORECASE) for keyword in unsubscribe_keywords):
                unsubscribe_links.append(a['href'])
            elif any(re.search(rf"\b{keyword}\b", link_text, re.IGNORECASE) for keyword in secondary_keywords):
                unsubscribe_links.append(a['href'])

        # First, try to find a link specifically mentioning "unsubscribe"
        for link in unsubscribe_links:
            if any(keyword in link for keyword in unsubscribe_keywords):
                return link

        # If not found, return the last link as a fallback
        return unsubscribe_links[-1] if unsubscribe_links else None
    except Exception as e:
        print(f"Error finding unsubscribe link: {e}")
        return None
    

def save_unsubscribe_attempt(sender, status):
    try:
        with open('unsubscribe_attempts.json', 'r') as file:
            attempts = json.load(file)
    except FileNotFoundError:
        attempts = {}

    attempts[sender] = status
    with open('unsubscribe_attempts.json', 'w') as file:
        json.dump(attempts, file)


def selenium_unsubscribe(link):
    options = webdriver.EdgeOptions()
    options.use_chromium = True
    options.headless = True  # Set to False if you want to see the browser window

    driver = webdriver.Edge(options=options)
    try:
        driver.get(link)
        # Wait for any button or input of type button to be present
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//button | //input[@type='button']")))
        
        # Check for a "Resubscribe" button with case-insensitive match
        xpath_for_resubscribe = "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'resubscribe')]"
        resubscribe_elements = driver.find_elements(By.XPATH, xpath_for_resubscribe)
        if resubscribe_elements:
            return "Unsubscribed successfully - resubscribe option found"

        # Find both input of type button and button elements
        buttons = driver.find_elements(By.XPATH, "//button | //input[@type='button']")

        # Additional keywords to look for in buttons
        additional_keywords = ['confirm', 'yes', 'agree', 'ok']

        for button in buttons:
            # Check the text for <button> and value for <input>
            button_text = button.text.lower() if button.tag_name == "button" else button.get_attribute('value').lower()
            if 'unsubscribe' in button_text or any(keyword in button_text for keyword in additional_keywords):
                button.click()
                return "Unsubscribed"
        
        return "Unsubscribe button not found"
    except Exception as e:
        print(f"Error during unsubscription with Selenium: {e}")
        return "Error"
    finally:
        driver.quit()


def unsubscribe_by_link(link, sender):
    try:
        status = selenium_unsubscribe(link)
        save_unsubscribe_attempt(sender, status)  # Save the unsubscribe attempt
        return status
    except Exception as e:
        save_unsubscribe_attempt(sender, f"Error: {e}")  # Save the error
        return f"Error during unsubscription: {e}"


def main():
    service = gmail_authenticate()
    if not service:
        print("Failed to authenticate with Gmail API")
        return

    messages = list_messages(service, 'me', max_results=100, past_days=90)
    unique_senders = set()

    for msg in messages:
        sender = get_email_sender(service, msg['id'])
        if sender:
            unique_senders.add(sender)

    print(f"Unique senders ({len(unique_senders)}):")
    for sender in unique_senders:
        print(sender)

    # Generate a JSON file with the sorted list of unique email senders
    generate_subscriptions_json(unique_senders)

if __name__ == "__main__":
    main()
