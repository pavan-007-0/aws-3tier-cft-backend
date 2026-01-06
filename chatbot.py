from flask import Blueprint, request, jsonify
from flask_limiter.util import get_remote_address
import requests
import json
from security import limiter
from db import get_connection

chatbot = Blueprint('chatbot', __name__)

class ChatbotService:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "llama2"  # Free model
        self.system_prompt = """You are a helpful AI assistant for an e-commerce website. You can help customers with:
        
        1. Product information and recommendations
        2. Order status and tracking
        3. General shopping assistance
        4. Account-related questions
        5. Return and refund policies
        
        Keep responses concise, friendly, and helpful. If you need specific product or order information, 
        ask for relevant details like product names, order numbers, or customer preferences.
        
        For complex issues that require human intervention, politely suggest contacting customer support.
        """
    
    def get_product_context(self, query):
        """Get relevant product information based on user query - OPTIMIZED"""
        try:
            connection = get_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Extract key search terms
            query_lower = query.lower()
            search_term = ""
            
            # Direct product matching
            if "mouse" in query_lower:
                search_term = "mouse"
            elif "headphone" in query_lower or "headset" in query_lower:
                search_term = "headphone"
            elif "laptop" in query_lower:
                search_term = "laptop"
            elif "watch" in query_lower:
                search_term = "watch"
            elif "speaker" in query_lower:
                search_term = "speaker"
            elif "phone" in query_lower or "mobile" in query_lower:
                search_term = "mobile"
            else:
                # Fallback to first word
                words = query_lower.split()
                search_term = words[0] if words else ""
            
            if search_term:
                # Simple, fast query
                cursor.execute("""
                    SELECT name, description, price, brand, quantity 
                    FROM products 
                    WHERE name LIKE %s 
                    AND quantity > 0 
                    AND status = 'active'
                    ORDER BY name
                    LIMIT 3
                """, (f"%{search_term}%",))
                
                products = cursor.fetchall()
                return products
            
        except Exception as e:
            print(f"Error getting product context: {e}")
        finally:
            if 'connection' in locals():
                connection.close()
        
        return []
    
    def generate_response(self, user_message, user_id=None):
        """Generate response using smart fallback (no Ollama delay)"""
        # Skip Ollama entirely and go straight to fast fallback responses
        return self.get_fallback_response(user_message)
    
    def get_fallback_response(self, user_message):
        """Fast fallback responses - OPTIMIZED"""
        message_lower = user_message.lower()
        
        # Quick product detection
        product_keywords = ['mouse', 'keyboard', 'laptop', 'headphone', 'gaming', 'phone', 'tablet', 'computer', 'monitor', 'speaker', 'camera', 'watch', 'product', 'buy', 'need', 'want']
        
        if any(word in message_lower for word in product_keywords):
            products = self.get_product_context(user_message)
            if products:
                # Simple, fast response
                if len(products) == 1:
                    p = products[0]
                    brand_info = f" by {p['brand']}" if p.get('brand') else ""
                    return f"Found: **{p['name']}**{brand_info} - ${p['price']}\n{p['description'][:60]}...\n\nIn stock: {p['quantity']} units. Would you like to know more?"
                else:
                    response = "Here's what I found:\n\n"
                    for p in products:
                        brand_info = f" by {p['brand']}" if p.get('brand') else ""
                        response += f"• **{p['name']}**{brand_info} - ${p['price']}\n"
                    response += "\nWhich one interests you?"
                    return response
            else:
                return f"Sorry, I couldn't find '{user_message}' in our inventory. Try 'mouse', 'headphones', 'laptop', or 'watch'."
        
        # Quick responses for common queries
        if any(word in message_lower for word in ['hello', 'hi', 'hey']):
            return "Hi! I can help you find products. What are you looking for?"
        
        elif any(word in message_lower for word in ['help', 'support']):
            return "I can help you find products, check prices, or answer questions. What do you need?"
        
        else:
            return "I can help you find products! Try asking for 'gaming mouse', 'headphones', 'laptop', etc."

chatbot_service = ChatbotService()

@chatbot.route('/message', methods=['POST'])
@limiter.limit("10 per minute")
def send_message():
    """Handle chat messages"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get user ID if provided (for personalized responses)
        user_id = data.get('user_id')
        
        # Generate AI response
        ai_response = chatbot_service.generate_response(user_message, user_id)
        
        # Skip logging for speed - uncomment if you need chat history
        # try:
        #     connection = get_connection()
        #     cursor = connection.cursor()
        #     cursor.execute("""
        #         INSERT INTO chat_logs (user_message, ai_response, user_id, timestamp)
        #         VALUES (%s, %s, %s, NOW())
        #     """, (user_message, ai_response, user_id))
        #     connection.commit()
        # except Exception as log_error:
        #     print(f"Error logging chat: {log_error}")
        # finally:
        #     if 'connection' in locals():
        #         connection.close()
        
        return jsonify({
            'response': ai_response,
            'timestamp': '2024-01-01T00:00:00Z'
        })
        
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@chatbot.route('/history', methods=['GET'])
@limiter.limit("5 per minute")
def get_history():
    """Get chat history for a user"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT user_message, ai_response, timestamp
            FROM chat_logs
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT 20
        """, (user_id,))
        
        history = cursor.fetchall()
        
        return jsonify({'history': history})
        
    except Exception as e:
        print(f"Chat history error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if 'connection' in locals():
            connection.close()