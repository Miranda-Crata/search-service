FROM public.ecr.aws/lambda/python:3.13

# Install Python dependencies
COPY requirements.txt ./
RUN pip3 install -r requirements.txt

# Copy application source code
COPY src/ ./src/
