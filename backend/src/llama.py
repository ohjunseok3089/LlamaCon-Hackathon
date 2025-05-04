from utils.prompts.llama_prompt import SYSTEM_PROMPT
from utils.configs.llama_endpoints import BASE_URL, LLAMA_API_KEY
import os
import requests

class LlamaProcessor:
    def __init__(self):
        self.is_stream = False
        self.is_conversation_loop = True
        self.conversation = []
        self.max_conversation_length = 10

    def chat_completion(self, messages, model="Llama-3.3-8B-Instruct", max_tokens=256):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLAMA_API_KEY}"
        }

        payload = {
            "messages": messages,
            "model": model,
            "max_tokens": max_tokens,
            "stream": False
        }    
        response = requests.post(
            f"{BASE_URL}/chat/completions", 
            headers=headers, 
            json=payload
        )
        return response.json()

    def process_text(self, user_prompt):    
        """Process text-only inputs"""
        if not self.conversation:
            self.conversation.append({"role": "system", "content": SYSTEM_PROMPT})
        
        if self.is_conversation_loop:
            self.conversation.append({"role": "user", "content": user_prompt})
            self.conversation[1:] = self.conversation[-self.max_conversation_length + 1:]
        else:
            self.conversation = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}]
            
        response = self.chat_completion(self.conversation)

        try:
            # Extract assistant's message
            assistant_content = response["completion_message"]["content"]["text"]
            assistant_stop_reason = response["completion_message"]["stop_reason"]

            # Add assistant's response to conversation history
            if self.is_conversation_loop:
                self.conversation.append({
                    "role": "assistant", 
                    "content": assistant_content,
                    "stop_reason": assistant_stop_reason
                })

            return assistant_content

        except KeyError as e:
            print(f"Error parsing response: {e}")
            print(f"Raw response: {response}")
            return f"Error: {str(response)}"

    def chat_completion_stream(self, model="Llama-4-Maverick-17B-128E-Instruct-FP8", messages=[], max_tokens=256):
        # Define headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLAMA_API_KEY}"
        }
        
        # Add Accept header for streaming
        if self.is_stream:
            headers["Accept"] = "text/event-stream"
        

        payload = {
            "model": model,
            "messages": messages,
            "stream": self.is_stream,
            "max_tokens": max_tokens
        }
        
        response = requests.post(
            f"{BASE_URL}/chat/completions", 
            headers=headers, 
            json=payload,
            stream=self.is_stream
        )
        return response.json()

    def process_images(self, images, user_prompt):
        if not self.conversation:
            self.conversation.append({"role": "system", "content": SYSTEM_PROMPT})
        content = []
        user_text_content = {}
        user_image_content = {}

        system_prompt = SYSTEM_PROMPT

        if user_prompt is not None:
            user_text_content["text"] = user_prompt
            user_text_content["type"] = "text"
            content.append(user_text_content)

        for image in images:
            user_image_content["image_url"] = {"url": image} # Image must be base64 encoded
            user_image_content["type"] = "image"
            content.append(user_image_content)
        
        if self.is_conversation_loop:
            self.conversation.append({"role": "user", "content": content})
            self.conversation[1:] = self.conversation[-self.max_conversation_length + 1:]
        else:
            self.conversation = [{"role": "system", "content": system_prompt}, {"role": "user", "content": content}]
            
        response = self.chat_completion(self.conversation)

        try:
            # Extract assistant's message
            assistant_content = response["completion_message"]["content"]["text"]
            assistant_stop_reason = response["completion_message"]["stop_reason"]

            # Display response
            print(f"\nAssistant: {assistant_content}")

            # Add assistant's response to conversation history
            if self.is_conversation_loop:
                self.conversation.append({
                    "role": "assistant", 
                    "content": assistant_content,
                    "stop_reason": assistant_stop_reason
                })

        except KeyError as e:
            print(f"Error parsing response: {e}")
            print(f"Raw response: {response}")

        return response