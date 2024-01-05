import json

from flask import Flask, render_template, request, jsonify
from quickstart import gmail_authenticate, find_unsubscribe_link, unsubscribe_by_link, get_latest_message_id_for_sender, save_unsubscribe_attempt

app = Flask(__name__)

def unsubscribe_from_senders(service, selected_senders):
    unsubscribe_results = {}
    for sender in selected_senders:
        # Check if already unsubscribed
        previous_status = check_unsubscribe_status(sender)
        if previous_status in ["Unsubscribed", "Unsubscribed successfully - resubscribe option found"]:
            unsubscribe_results[sender] = "Already unsubscribed"
            continue

        message_id = get_latest_message_id_for_sender(service, 'me', sender)
        if message_id:
            unsubscribe_link = find_unsubscribe_link(service, message_id)
            if unsubscribe_link:
                status = unsubscribe_by_link(unsubscribe_link, sender)
                unsubscribe_results[sender] = status
            else:
                unsubscribe_results[sender] = "No unsubscribe link found"
        else:
            unsubscribe_results[sender] = "No message found for sender"
        
        # Save each unsubscribe attempt to a file
        save_unsubscribe_attempt(sender, unsubscribe_results[sender])

    return unsubscribe_results

def check_unsubscribe_status(sender):
    try:
        with open('unsubscribe_attempts.json', 'r') as file:
            attempts = json.load(file)
            return attempts.get(sender, None)
    except FileNotFoundError:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        service = gmail_authenticate()
        if not service:
            return jsonify({'success': False, 'error': "Failed to authenticate with Gmail API"})

        selected_senders = request.form.getlist('senders')
        results = unsubscribe_from_senders(service, selected_senders)

        return render_template('results.html', results=results)

    with open('subscriptions.json', 'r') as file:
        subscriptions = json.load(file)
    return render_template('index.html', subscriptions=subscriptions)

@app.route('/unsubscribe-history')
def unsubscribe_history():
    try:
        with open('unsubscribe_attempts.json', 'r') as file:
            unsubscribe_attempts = json.load(file)
    except FileNotFoundError:
        unsubscribe_attempts = {}

    return render_template('unsubscribe-history.html', attempts=unsubscribe_attempts)

if __name__ == '__main__':
    app.run(port=8080)
