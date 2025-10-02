FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o web-api main.go

FROM alpine:3.18
WORKDIR /app
COPY --from=builder /app/web-api . 
EXPOSE 8080	
CMD ["./web-api"]
