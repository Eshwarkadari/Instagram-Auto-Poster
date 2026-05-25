FROM n8nio/n8n:latest

USER root

# Install Python + dependencies
RUN apk add --no-cache python3 py3-pip gcc musl-dev python3-dev libffi-dev
RUN pip3 install requests --break-system-packages

# Copy project files
COPY python/ /home/node/instagram/python/
WORKDIR /home/node/instagram

USER node
CMD ["n8n", "start"]
