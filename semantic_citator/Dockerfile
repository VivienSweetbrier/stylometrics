# Use Ubuntu 22.04 to stabilize C++, R, and Lean library linkages
FROM ubuntu:22.04

# Prevent tzdata and apt prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.elan/bin:${PATH}"

# 1. Install System Dependencies, R-base, and C++ Compilers
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    r-base \
    libv8-dev \
    libcurl4-openssl-dev \
    python3.11 \
    python3-pip \
    python3.11-venv \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Lean 4 Toolchain
RUN curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y --default-toolchain leanprover/lean4:stable

# 3. Compile R Dependencies
RUN Rscript -e "install.packages(c('V8', 'jsonlite', 'dagitty', 'SimDesign', 'rstream', 'ReplicationSuccess'), repos='https://cloud.r-project.org/')"

# 4. Configure Python Backend
WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 5. Application Assembly
COPY . .

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
