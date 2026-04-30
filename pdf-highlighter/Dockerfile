FROM node:20-alpine
WORKDIR /app
COPY pdf-highlighter/package*.json ./
RUN npm ci
COPY pdf-highlighter/ .
EXPOSE 4000
CMD ["node", "server.js"]
