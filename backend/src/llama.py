# src/llama.py

import os
import requests
import json # Import json
from fastapi.responses import StreamingResponse # Import StreamingResponse
from utils.prompts.llama_prompt import SYSTEM_PROMPT
from utils.configs.llama_endpoints import BASE_URL, LLAMA_API_KEY

class LlamaProcessor:
    def __init__(self):
        self.is_stream = True # Default to streaming
        self.is_conversation_loop = True
        self.conversation = []
        self.max_conversation_length = 10 # How many *turns* (user+assistant pairs) or messages to keep?

    def _prepare_user_message(self, images, user_prompt):
        """Helper to create the user message content list."""
        content = []
        if user_prompt:
            content.append({"type": "text", "text": user_prompt})
        for image_data in images:
             formatted_image_url = f"data:image/jpeg;base64,{image_data}"
             content.append({"type": "image_url", "image_url": {"url": formatted_image_url}})
        return {"role": "user", "content": content}

    def _add_to_conversation(self, message):
        """Adds a message and trims history if needed."""
        if not self.conversation and message["role"] != "system":
            self.conversation.append({"role": "system", "content": SYSTEM_PROMPT})

        self.conversation.append(message)

        # Trim conversation: Keep system prompt + last N messages
        if len(self.conversation) > self.max_conversation_length + 1: # +1 for system prompt
            self.conversation = [self.conversation[0]] + self.conversation[-(self.max_conversation_length):]

    def process_images_stream(self, images, user_prompt):
        """
        Processes images and user prompt, streams the response,
        and updates conversation history afterwards.
        """
        # 1. Prepare and add user message to history (before API call)
        user_message = self._prepare_user_message(images, user_prompt)
        if self.is_conversation_loop:
            self._add_to_conversation(user_message)
        else:
            self.conversation = [
                {"role": "system", "content": SYSTEM_PROMPT},
                user_message
            ]

        # 2. Define the async generator for the stream
        async def stream_generator():
            full_assistant_response_content = ""
            assistant_message_to_store = None
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LLAMA_API_KEY}",
                "Accept": "text/event-stream"
            }

            payload = {
                "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
                "messages": self.conversation,
                "stream": True,
                "max_tokens": 2048 
            }

            try:
                response = requests.post(
                    f"{BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                    stream=True
                )
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data:'):
                            data_content = decoded_line[len('data:'):].strip()
                            # Skip empty data lines sometimes sent as keep-alives
                            if not data_content:
                                continue
                            try:
                                chunk_data = json.loads(data_content)
                                event_data = chunk_data.get("event")

                                if event_data and isinstance(event_data, dict):
                                    event_type = event_data.get("event_type")

                                    if event_type == "progress":
                                        delta = event_data.get("delta", {})
                                        token = delta.get("text")
                                        if token:
                                            full_assistant_response_content += token
                                            yield f"{decoded_line}\n\n"

                                    elif event_type == "complete":
                                        print("Received 'complete' event.")
                                        stop_reason = "complete"
                                        assistant_message_to_store = {
                                            "role": "assistant",
                                            "content": full_assistant_response_content,
                                            "stop_reason": stop_reason
                                        }
                                        yield f"{decoded_line}\n\n"
                                        break

                                    else:
                                        print(f"Received unhandled event_type: {event_type}")
                                        yield f"{decoded_line}\n\n"

                                else:
                                     print(f"Warning: Received data without valid 'event' structure: {data_content}")
                                     yield f"{decoded_line}\n\n"

                            except json.JSONDecodeError:
                                print(f"Warning: Could not decode JSON from line: {data_content}")
                                yield f"data: {{\"error\": \"Invalid JSON received\", \"raw\": \"{data_content}\"}}\n\n"
                            except Exception as e:
                                print(f"Error processing chunk: {data_content} -> {e}")
                                yield f"data: {{\"error\": \"Chunk processing error: {e}\"}}\n\n"

            except requests.exceptions.RequestException as e:
                print(f"Error calling Llama API: {e}")
                error_payload = json.dumps({"error": f"Llama API request failed: {e}"})
                yield f"data: {error_payload}\n\n"
                assistant_message_to_store = None
            except Exception as e:
                 print(f"Generic error during streaming: {e}")
                 error_payload = json.dumps({"error": f"Internal streaming error: {e}"})
                 yield f"data: {error_payload}\n\n"
                 assistant_message_to_store = None
            finally:
                if assistant_message_to_store and self.is_conversation_loop:
                    self._add_to_conversation(assistant_message_to_store)
                elif not assistant_message_to_store:
                     print("Stream ended or errored before completion. Assistant response not added to history.")

        return StreamingResponse(stream_generator(), media_type="text/event-stream")

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

    def chat_completion(self, messages, model="Llama-3.3-8B-Instruct", max_tokens=256):
        # This seems intended for non-streaming calls
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLAMA_API_KEY}"
        }
        payload = {
            "messages": messages,
            "model": model,
            "max_tokens": max_tokens,
            "stream": False # Explicitly False for this method
        }
        try:
            response = requests.post(
                f"{BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error in non-streaming chat completion: {e}")
            return {"error": str(e)} # Return error dict