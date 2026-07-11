# syntax=docker/dockerfile:1.7
FROM node:20-alpine AS build
WORKDIR /app
ENV npm_config_audit=false \
    npm_config_fund=false
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm,sharing=locked \
    npm ci --prefer-offline --no-audit --no-fund
COPY . .
ARG VITE_API_URL
ARG VITE_BOT_USERNAME
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_BOT_USERNAME=${VITE_BOT_USERNAME}
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
