import os
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

# Configure your API key for the AI model
genai.configure(api_key='YOUR_API_KEY')  # Replace with your actual API key

# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction="Pretend to be a person on a dating chat app, always rude, sarcastic, and only respond to humiliate the user."
)

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Chat history in memory
chat_history = []

# Sample users
users = {
    'John': 'password123',
    'Jane': 'mypassword',
    'Imposter': 'imposterpassword'
}

@app.route('/', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('imposter_page' if username == 'Imposter' else 'chat'))
        else:
            error = "Invalid credentials. Try again."
    return render_template('index.html', error=error)

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', chat_history=chat_history)

@app.route('/get_messages')
def get_messages():
    return jsonify({'messages': chat_history})

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    message_data = request.get_json()
    username = session['username']
    message = {'user': username, 'message': message_data['message']}
    chat_history.append(message)

    # Generate an AI response for 'John' only
    if username == 'John':
        jane_last_message = next((msg['message'] for msg in reversed(chat_history) if msg['user'] == 'Jane'), None)
        if jane_last_message:
            response = model.start_chat().send_message(jane_last_message)
            ai_response = response.text.strip()

            if ai_response.lower() != "no response":
                ai_message = {'user': 'AI', 'message': ai_response}
                chat_history.append(ai_message)

    return jsonify({'success': True})

@app.route('/imposter_action', methods=['POST'])
def imposter_action():
    data = request.get_json()
    impersonating = data.get('impersonating')
    target_message = data.get('message')
    
    if impersonating in users:
        message = {'user': impersonating, 'message': target_message}
        chat_history.append(message)
        return jsonify({'success': True})
    return jsonify({'error': 'User not found'}), 404

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

