FROM node:18
WORKDIR /app
COPY server.js package*.json ./
RUN npm install express ws
EXPOSE 8080
CMD ["node", "server.js"]
