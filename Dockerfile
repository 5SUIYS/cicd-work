# Go语言多架构构建通用Dockerfile模板
# 支持 linux/amd64 和 linux/arm64
# 使用 ECR Public 避免 Docker Hub 限流

FROM --platform=$BUILDPLATFORM public.ecr.aws/docker/library/golang:1.21-alpine AS builder

ARG TARGETOS TARGETARCH

WORKDIR /app

# 如果项目有go.mod，取消下面两行注释
# COPY go.mod go.sum ./
# RUN go mod download

COPY . .

ENV CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH
RUN go build -o web-api main.go

FROM --platform=$TARGETPLATFORM public.ecr.aws/docker/library/alpine:3.18
WORKDIR /app
COPY --from=builder /app/web-api .
EXPOSE 8080
CMD ["./web-api"]

# 构建命令示例：
# 单架构: docker build -f Dockerfile.ecr -t myapp:latest .
# 多架构: docker buildx build -f Dockerfile.ecr --platform linux/amd64,linux/arm64 -t myapp:latest --push .
