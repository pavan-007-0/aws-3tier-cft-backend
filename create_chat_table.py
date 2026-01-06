from db import get_connection

def create_chat_table():
    """Create chat_logs table for storing chat history"""
    try:
        connection = get_connection()
        cursor = connection.cursor()
        
        # Create chat_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_message TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                user_id VARCHAR(255),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id),
                INDEX idx_timestamp (timestamp)
            )
        """)
        
        connection.commit()
        print("Chat logs table created successfully!")
        
    except Exception as e:
        print(f"Error creating chat table: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    create_chat_table()