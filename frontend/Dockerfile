# Build stage
FROM node:20-bookworm AS deps

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

FROM deps AS build

WORKDIR /app

# Reuse installed dependencies from the deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source code
COPY . .

# Copy environment file for production
COPY .env.production .env

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
