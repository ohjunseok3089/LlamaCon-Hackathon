#!/usr/bin/env python3
"""
Test script for Llama functionality.
This script provides a simple command-line interface to interact with the Llama module.
"""

import sys
import os

# Add the parent directory to the path so we can import the llama module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llama import LlamaProcessor

def main():
    """
    Main function that runs a loop to take user input and process it.
    """
    print("Welcome to the Llama Test Interface")
    print("Type 'exit' or 'quit' to end the program")
    print("-" * 50)
    
    # Create an instance of LlamaProcessor
    llama_processor = LlamaProcessor()
    
    while True:
        # Get user input
        user_input = input("\nEnter your prompt: ")
        
        # Check if user wants to exit
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting the program. Goodbye!")
            break
        
        # Process the input and print the response
        try:
            print("\nProcessing your request...")
            response = llama_processor.process_text_stream(user_input)
            full_response = ""
            print("\nResponse:")
            for chunk in response.iter_lines():
                if chunk:
                    try:
                        decoded_chunk = chunk.decode("utf-8")[6:]
                        data = json.loads(decoded_chunk)
                        if "event" in data:
                            if data["event"]["event_type"] == "progress":
                                token = data["event"]["delta"]["text"]
                                full_response += token
                                print(token, end="", flush=True)
                            elif data["event"]["event_type"] == "complete":
                                break
                    except json.JSONDecodeError as e:
                        print("JSONDecodeError", e)
            print("-" * 50)
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
