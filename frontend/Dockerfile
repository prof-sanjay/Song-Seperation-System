# syntax=docker/dockerfile:1.4
FROM node:20-alpine AS build

WORKDIR /app
# Copy package files
COPY frontend/package*.json ./
# Install dependencies
RUN npm install

# Copy frontend source code
COPY frontend/ ./
# Build the Vite React application
RUN npm run build

# Use Nginx to serve the static frontend
FROM nginx:alpine
# Copy built assets from builder stage
COPY --from=build /app/dist /usr/share/nginx/html

# Replace default nginx config with one that proxies /api to backend
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
    location /api/ { \
        proxy_pass http://backend:8000/; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
