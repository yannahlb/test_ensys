import os, random
import openai
import pandas as pd
from dotenv import load_dotenv
from model import EmotionModel
from preprocess import TextPreprocessor
from feedback_analyzer import FeedbackAnalyzer

def load_config():
    dotenv_path = os.path.join(os.path.dirname(__file__), 'static', 'key.env')
    load_dotenv(dotenv_path)
    return os.getenv('OPENAI_API_KEY')

class EnSysBot:
    def __init__(self, engine, api_key):
        self.engine = engine
        self.api_key = api_key
        self.last_topic = None
        self.conversation = []
        self.feedback = []
        self.feedback_data = []
        self.preprocessor = TextPreprocessor()
        self.model = EmotionModel(engine)
        openai.api_key = self.api_key

        # Load restaurant data
        self.restaurant_data = self.load_restaurant_data()
        self.menu_categories = ['dessert', 'drinks', 'main course', 'pasta', 'salad', 'sides']
        
        # Add a pre-prompt that establishes the bot's identity
        self.pre_prompt = (
            "You are EnSys, a friendly and knowledgeable customer service chatbot. "
            "You assist customers with their inquiries about the menu, take feedback, "
            "and provide recommendations based on their preferences. "
            "Please ensure to maintain a helpful and polite tone in your responses."
        )

    def add_system_message(self, content):
        self.conversation.append({"role": "system", "content": content})

    def add_user_message(self, content):
        self.conversation.append({"role": "user", "content": content})
        self.feedback.append(content)

    def save_chat_history(self, filename='chat_history.txt'):
        with open(filename, 'a') as file:
            for message in self.conversation:
                file.write(f"{message['role'].capitalize()}: {message['content']}\n")
            file.write("\n--- End of Conversation ---\n\n")

    def generate_response(self, prompt):
        # Add the user's message to the conversation
        self.add_user_message(prompt)

        # Preprocess the user's prompt
        preprocessed_prompt = self.preprocessor.preprocess(prompt)
        sentiment = self.preprocessor.get_sentiment(prompt)

        response = ""  # Initialize the response variable

        # Check if the user's input matches a specific dish within each menu category
        for cat, items in self.get_menu().items():
            for item in items:
                if item['name'].lower() in preprocessed_prompt:
                    # Call generate_dish_response method for the specific dish
                    dish_response = self.generate_dish_response(item)
                    self.add_system_message(dish_response)
                    self.save_chat_history()  # Save the chat history
                    print("Bot:", dish_response)
                    return dish_response

        # Handle feedback-related queries
        feedback_query_response = self.handle_feedback_query(preprocessed_prompt)
        if feedback_query_response:
            self.save_chat_history()  # Save the chat history
            return feedback_query_response

        # Check if the user's input indicates positive sentiment towards a food item
        if sentiment['compound'] > 0.05 and 'no' not in preprocessed_prompt.lower():
            response = self.generate_gpt_response(prompt, sentiment, context="positive")
            self.add_system_message(response)
            self.save_chat_history()  # Save the chat history
            print("Bot:", response)
            return response

        # Check if the user's input indicates negative sentiment towards a food item
        elif sentiment['compound'] < -0.05:
            response = self.generate_gpt_response(prompt, sentiment, context="negative")
            self.add_system_message(response)
            self.save_chat_history()  # Save the chat history
            print("Bot:", response)
            return response

        # Check if the user's input praises the menu
        menu_praise_keywords = ['love menu', 'like menu', 'great menu', 'awesome menu', 'amazing menu', 'menu is good']
        if any(keyword in preprocessed_prompt for keyword in menu_praise_keywords):
            sentiment_score = sentiment['compound']
            if sentiment_score > 0.05:
                response = self.get_menu_praise_response()
                self.add_system_message(response)
                self.save_chat_history()  # Save the chat history
                print("Bot:", response)
                return response

        # Check if the user's input is related to the restaurant name
        restaurant_name_keywords = ['restaurant name', 'name of this place', 'called', 'called this', 'name', 'tell place', 'this place']
        if any(keyword in preprocessed_prompt for keyword in restaurant_name_keywords):
            # Generate a response with the restaurant's name
            restaurant_name = self.get_restaurant_name_response()
            # Mix canned and generated response
            canned_responses = [
                f"The name of this place is {restaurant_name}.",
                f"You're dining at {restaurant_name}."
            ]
            # Randomly select a response
            response = random.choice(canned_responses)
            self.add_system_message(response)
            self.save_chat_history()  # Save the chat history
            print("Bot:", response)
            return response

        # Check if the user's input is related to the restaurant profile
        restaurant_profile_keywords = ['restaurant profile', 'about the restaurant', 'tell me about', 'more about this place', 'more about this restaurant', 'tell atin-atehan', 'tell restaurant']
        if any(keyword in preprocessed_prompt for keyword in restaurant_profile_keywords):
            # Get the restaurant profile from the CSV data
            restaurant_profile = self.get_restaurant_profile_response()
            if restaurant_profile:
                # Generate a prompt to ask for more information about the restaurant profile
                prompt = f"Could you provide more details about {restaurant_profile}?"
                # Generate a response using OpenAI model
                response = self.generate_gpt_response(prompt, sentiment, context="restaurant_profile")
                self.save_chat_history()  # Save the chat history
                print("Restaurant Profile:", response)
                return response
            else:
                response = "I'm sorry, but I couldn't find information about the restaurant profile at the moment."
                self.add_system_message(response)
                self.save_chat_history()  # Save the chat history
                print("Bot:", response)
                return response

        # Check if the user's input is related to the menu
        if 'menu' in preprocessed_prompt:
            # If sentiment is neutral, respond with category list
            if -0.05 <= sentiment['compound'] <= 0.05:
                response = self.get_menu_category_response()
                self.add_system_message(response)
                self.save_chat_history()  # Save the chat history
                print("Bot:", response)
                return response

        # Check if the user's input matches a specific category
        for category in self.menu_categories:
            if category.lower() in preprocessed_prompt:
                menu = self.get_menu()
                if category.lower() in menu:
                    # Start with the category name followed by a colon and newline
                    formatted_menu = f"{category.capitalize()}:\n"
                    # Add each menu item on a new line preceded by its index
                    for idx, item in enumerate(menu[category.lower()], start=1):
                        formatted_menu += f"{idx}. {item['name']}\n"
                    response = formatted_menu.strip()  # Remove any trailing newlines
                    self.add_system_message(response)
                    self.last_topic = category.lower()
                    self.save_chat_history()  # Save the chat history
                    print("Bot:", response)
                    return response


        # Check if the user's input is related to recommendations
        recommendation_keywords = ['recommend', 'suggest']
        if any(keyword in preprocessed_prompt for keyword in recommendation_keywords):
            # Sample recommendations
            recommendations = [
                "Our chef's special pasta dish is highly recommended!",
                "If you're a seafood lover, you might enjoy our grilled salmon.",
                "For something light and refreshing, consider trying our seasonal salad.",
                "How about indulging in our decadent chocolate lava cake for dessert?"
            ]
            response = "Sure! Here are some recommendations based on our popular dishes:\n\n" + "\n".join(recommendations)
            self.add_system_message(response)
            self.save_chat_history()  # Save the chat history
            print("Bot:", response)
            return response

        # Check if the user's input is a number after a menu list
        if preprocessed_prompt.isdigit() and self.last_topic:
            selected_index = int(preprocessed_prompt) - 1
            menu_items = self.get_menu().get(self.last_topic, [])
            if 0 <= selected_index < len(menu_items):
                selected_dish = menu_items[selected_index]
                response = self.generate_dish_response(selected_dish)
                self.add_system_message(response)
                self.save_chat_history()  # Save the chat history
                print("Bot:", response)
                return response
            else:
                response = "I'm sorry, but that selection is out of range. Please choose a valid number from the menu."
                self.add_system_message(response)
                self.save_chat_history()  # Save the chat history
                print("Bot:", response)
                return response

        # Use the last relevant topic if available
        if self.last_topic:
            response = f"Can you tell me more about {self.last_topic}?"
            self.add_system_message(response)
            self.save_chat_history()  # Save the chat history
            print("Bot:", response)
            return response

        # Use OpenAI to understand the context and generate a response
        try:
            response = self.generate_gpt_response(prompt, sentiment)
            self.add_system_message(response)
            self.save_chat_history()  # Save the chat history
            print("Bot:", response)
            return response

        except Exception as e:
            print("Error:", e)
            return "I encountered an error while processing your request."

    def handle_feedback_query(self, preprocessed_prompt):
        # Check if the user's input indicates feedback-related queries
        if 'like' in preprocessed_prompt or 'dislike' in preprocessed_prompt or 'suggestions' in preprocessed_prompt:
            # Extract relevant information from the user input
            feedback_type = None
            if 'like' in preprocessed_prompt:
                feedback_type = 'like'
            elif 'dislike' in preprocessed_prompt:
                feedback_type = 'dislike'
            elif 'suggestions' in preprocessed_prompt:
                feedback_type = 'suggestion'

            if feedback_type:
                # Analyze the user's feedback
                feedback_analysis = self.analyze_feedback(feedback_type, preprocessed_prompt)
                # Add the system response for feedback-related queries
                feedback_response = f"Thank you for your {feedback_type}! We appreciate your input and will use it to improve our services."
                self.add_system_message(feedback_response)
                self.save_chat_history()  # Save the chat history
                print("Bot:", feedback_response)
                return feedback_response
        return None

    def get_restaurant_name_response(self):
        if not self.restaurant_data.empty:
            return self.restaurant_data['Restaurant Name'].iloc[0]
        else:
            return "Our restaurant is Atin-atehan, we're glad to serve you!"  # Fallback if the restaurant name is not available
    
    def get_restaurant_profile_response(self):
        if not self.restaurant_data.empty:
            return self.restaurant_data['Restaurant Profile'].iloc[0]
        else:
            return "Sorry, I couldn't retrieve information about the restaurant profile at the moment."

    def get_menu(self):
        menu = {}
        if not self.restaurant_data.empty:
            for dish_type in self.restaurant_data['Dish Type'].unique():
                menu[dish_type.lower()] = []
                group_df = self.restaurant_data[self.restaurant_data['Dish Type'].str.lower() == dish_type.lower()]
                if not group_df.empty:
                    for _, row in group_df.iterrows():
                        # Ensure unique items
                        if row['Dish Name'] not in [item['name'] for item in menu[dish_type.lower()]]:
                            menu[dish_type.lower()].append({
                                'name': row['Dish Name'],
                                'description': row['Description']
                            })
        return menu

    def load_restaurant_data(self):
        file_path = 'Atin-atehan.csv'
        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']  # List of encodings to try
        
        for encoding in encodings:
            try:
                return pd.read_csv(file_path, encoding=encoding)
            except UnicodeDecodeError:
                print(f"Failed to read CSV with encoding '{encoding}'. Trying next encoding...")
        
        print("Unable to read CSV file with any of the specified encodings.")
        return pd.DataFrame()  # Return an empty DataFrame if all encodings fail

    def generate_dish_response(self, dish):
        return f"{dish['name']}: {dish['description']}"

    def get_menu_praise_response(self):
        return "Thank you for your kind words about our menu! We strive to offer a variety of delicious options to suit every taste."

    def get_menu_category_response(self):
        return "Our menu is divided into several categories including Dessert, Drinks, Main Course, Pasta, Salad, and Sides. Which category would you like to explore?"

    def generate_gpt_response(self, prompt, sentiment, context=None):
        messages = [{"role": "system", "content": self.pre_prompt}]
        messages.extend(self.conversation)

        # Add additional context if provided
        if context:
            context_message = f"Context: {context}. Sentiment: {sentiment}"
            messages.append({"role": "system", "content": context_message})

        messages.append({"role": "user", "content": prompt})

        try:
            response = openai.ChatCompletion.create(
                model=self.engine,
                messages=messages
            )
            return response.choices[0].message['content'].strip()
        except openai.error.OpenAIError as e:
            print("Error with OpenAI API:", e)
            return "I'm sorry, but I couldn't process your request at the moment."

    def train_emotion_model(self, dataset_path):
        self.model.train_model(dataset_path)

    def process_feedback(self, feedback):
        analyzer = FeedbackAnalyzer()
        analysis = analyzer.analyze_feedback(feedback)
        return analysis
    
    def analyze_feedback(self, feedback_type, preprocessed_prompt):
        feedback_analysis = self.model.predict_emotion(preprocessed_prompt)
        self.feedback_data.append({
            'type': feedback_type,
            'content': preprocessed_prompt,
            'analysis': feedback_analysis
        })

    def end_chat(self):
        self.save_conversation()
        # Create an instance of FeedbackAnalyzer
        feedback_analyzer = FeedbackAnalyzer(self.feedback)
        # Analyze the feedback
        self.feedback_data = feedback_analyzer.analyze_feedback()

    def save_conversation(self):
        for message in self.conversation:
            if message["role"] == "user":
                self.feedback.append(message["content"])
        self.conversation = []

    def display_feedback_analysis(self):
        if self.feedback_data:
            print("Feedback Analysis Report:")
            print(self.feedback_analyzer.interpret_feedback())
        else:
            print("No feedback to analyze.")


if __name__ == "__main__":
    api_key = input("Enter your OpenAI API key: ")
    bot = EnSysBot("ft:gpt-3.5-turbo-0125:ensys:restaurant-2:9SO7Maw7", api_key)
   
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            bot.end_chat()
            break
        response = bot.generate_response(user_input)
        print("EnSysBot:", response)