FROM python:3.12-slim

# Create system user and group for running the application
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Change ownership of application files to non-root user
RUN chown -R app:app /app

EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Switch to non-root user
USER app

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
