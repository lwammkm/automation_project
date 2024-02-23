# base image for your Docker container
FROM python:3.11

# Install texlive and other dependencies
RUN apt-get update && apt-get install -y \
    texlive \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-latex-base \
    texlive-latex-extra \
    && rm -rf /var/lib/apt/lists/*



#  Set the working directory inside the container to /app
WORKDIR /app

# Copy the 'requirements.txt' file from the host machine to the '/app' directory in the container
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copies the entire content of the current directory to the /app directory in the container
COPY . .

# default command to run when the container starts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
