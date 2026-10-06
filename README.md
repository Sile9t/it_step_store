# IT Step Store

**Python WEB API project for "IT Step" learning company**

## Preparation
1. Create and activate virtual environment
```bash
    python -m venv /path/to/new/virtual/environment
    # Activation
    \path\to\env\virtual\environment\Scripts\activate # for Windows
    source /path/to/env/virtual/environment/bin/activate # for Linux/masOS
```

2. Install all required packages
```bash
    python3 install -r ./requirements
```

3. Create database with tables
```bash
    # from ./it_step_store/it_step_store
    python3 manage.py migrate
```

## How to run web server
```bash
    python3 manage.py runserver
```