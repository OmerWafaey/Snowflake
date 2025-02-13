FROM python:3.10-slim
ENV LANG=C.UTF-8

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# Install required packages
RUN apt-get update && apt-get install -y \
    openssh-client \
    curl \
    gnupg \
    unzip \
    sudo \
    awscli \
    ansible \
    rsync \
    jq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages globally (for general usage)
RUN pip install ansible boto3 botocore requests \
    && ansible-galaxy collection install amazon.aws \
    && curl -sSL https://github.com/mikefarah/yq/releases/download/v4.6.1/yq_linux_amd64 -o /usr/bin/yq \
    && chmod +x /usr/bin/yq

# Set working directory
WORKDIR /ansible

# Create a virtual environment and install required Python dependencies
RUN python3 -m venv /opt/venv
RUN /opt/venv/bin/pip install --upgrade pip
RUN /opt/venv/bin/pip install chromadb transformers torch pdfplumber python-docx

# Copy the necessary files into the container
COPY . /ansible

# Add EC2 host to known hosts (to avoid SSH prompts)
RUN mkdir -p /root/.ssh && ssh-keyscan -H 35.173.203.104 >> /root/.ssh/known_hosts

# Set default entrypoint for the container
ENTRYPOINT ["/opt/venv/bin/ansible-playbook"]
