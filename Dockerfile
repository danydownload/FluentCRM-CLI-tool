# Use a slim Python base image for a small final image size
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy and install the dependencies first to leverage Docker's layer caching
COPY requirements.cli.txt .
RUN pip install --no-cache-dir -r requirements.cli.txt

# Copy the main CLI script into the container
COPY fluent_cli.py .

# Copy documentation into the image
WORKDIR /
COPY *.md /docs/
WORKDIR /app

# Set the script as the main command. Any arguments passed to `docker run`
# will be appended to this, allowing our CLI to function.
ENTRYPOINT ["python", "fluent_cli.py"]