'''
This is the main file for the EnSys chatbot. It initializes the Flask app and loads the chatbot with the API key.
Old model: ft:gpt-3.5-turbo-0125:ensys:restaurant:9IrHirrM 
'''
import nltk
import os
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('vader_lexicon')
nltk.download('wordnet')

from flask import Flask
from routes import initialize_routes
from bot import EnSysBot, load_config


# Load environment variables and get the API key
try:
    api_key = load_config()
    #engine = "ft:gpt-3.5-turbo-0125:ensys:restaurant-2:9SO7Maw7"
    engine ="ft:gpt-3.5-turbo-0125:ensys:empatheticd:9XQSt7AX"
    bot = EnSysBot(engine, api_key)
except Exception as e:
    raise e

# Initialize Flask app
app = Flask(__name__)

# Initialize routes
initialize_routes(app, bot)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
