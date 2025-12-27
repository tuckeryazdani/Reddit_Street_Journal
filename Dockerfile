# Use an existing docker image as a base
FROM python:3.11

# Set the working directory early to organize files
WORKDIR /app 

COPY powerful-balm-482518-i5-66d1f96462b4.json ./
# Copy requirements first to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt 

# Copy the rest of the application code
COPY ./app . 

# Ensure python can find your modules
ENV PYTHONPATH=/app

ENV GOOGLE_APPLICATION_CREDENTIALS="/app/powerful-balm-482518-i5-66d1f96462b4.json"

# Run main.py when the container launches
CMD ["python", "main.py"]