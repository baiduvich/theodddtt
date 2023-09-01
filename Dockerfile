# Use an official Python runtime as base image
FROM python:3.8-slim-buster

# Install LibreOffice, Java Runtime Environment, and PostgreSQL client
RUN apt-get update && \
    apt-get install -y --no-install-recommends libreoffice default-jre libreoffice-java-common postgresql-client && \
    apt-get clean

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt into the container at /app
COPY requirements.txt /app/

# Install required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 5000 available to the world outside this container
EXPOSE 8080

# Run app.py when the container launches
CMD ["waitress-serve", "--host=0.0.0.0", "--port=8080", "app:app"]
