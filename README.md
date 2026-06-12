## Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/RosaAtenah/learnflow-ai.git
cd learnflow-ai
````

---

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate   # On Linux / Mac
venv\Scripts\activate      # On Windows
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure API Key

Create a Streamlit secrets file:

```
.streamlit/secrets.toml
```

Add your API key inside:

```toml
MODEL_API_KEY = "your_api_key_here"
```

---

### 5. Run the application

```bash
streamlit run app.py
```

---

## Notes

* Make sure your API key is valid before running the app
* If Streamlit is not installed:

```bash
pip install streamlit
```

---

## Expected Result

After running the command, the app will be available at:

```
http://localhost:8501
```

```