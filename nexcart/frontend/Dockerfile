# ══════════════════════════════════════════════════════════════════
# NexCart — Frontend Dockerfile
# Node 20 Alpine image running Vite dev server
# ══════════════════════════════════════════════════════════════════

FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files first for layer caching
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend source
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Start Vite dev server (bind to all interfaces for Docker)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
