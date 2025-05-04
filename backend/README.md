# Important Steps to run the Backend:

## 1. Create a virtual environment and activate it:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

## 2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 3. Set environment variables:
```bash
export LLAMA_API_KEY=your_llama_api_key
```

## 4. Run the server:
```bash
python main.py
```