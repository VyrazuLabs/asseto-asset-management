FROM python:3.12
WORKDIR /app

# Installing pip dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt
RUN pip install setuptools
# Copying Source Code
COPY . .
EXPOSE 8000

# Running command
CMD ["python3", "manage.py", "migrate", "python3", "manage.py", "runserver", "127.0.0.1:8000"]


