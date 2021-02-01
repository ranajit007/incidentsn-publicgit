# Create our image based on Python 3.8
FROM continuumio/anaconda3
LABEL "author"="Daniel Nava / Jorge Bustillos"
LABEL "company"="IBM"

# Tell Python to not generate .pyc
ENV PYTHONDONTWRITEBYTECODE 1

# Turn off buffering
ENV PYTHONUNBUFFERED 1

# Set working directory and addour Flask API files
WORKDIR /app
ADD . /app

# Install requirements using pip
RUN python -m pip install -r /app/server/requirements.txt > /dev/null

# Expose ports
EXPOSE 5000

# Prepare setup file
RUN chmod +x ./server/setup.sh

# Run setup
RUN sh server/setup.sh

# Prepare runstart file
RUN chmod +x ./server/runstart.sh

# Start bootstrap
#ENTRYPOINT ["sh", "server/runstart.sh"]
WORKDIR /app/server
CMD ["python3","Server.py"]
