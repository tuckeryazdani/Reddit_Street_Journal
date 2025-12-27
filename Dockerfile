# Use an existing docker image as a base
FROM python:3.11

# Set the working directory early to organize files
WORKDIR /app 

# Copy requirements first to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt 

# Copy the rest of the application code
COPY ./app . 

# Ensure python can find your modules
ENV PYTHONPATH=/app

# Run main.py when the container launches
CMD ["python", "main.py"]