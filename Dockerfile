# Go语言多架构构建通用Dockerfile模板
# 支持 linux/amd64 和 linux/arm64

FROM --platform=$BUILDPLATFORM golang:1.21-alpine AS builder

ARG TARGETOS TARGETARCH

WORKDIR /app

# 如果项目有go.mod，取消下面两行注释
# COPY go.mod go.sum ./
# RUN go mod download

COPY . .

ENV CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH
RUN go build -o web-api main.go

FROM --platform=$TARGETPLATFORM alpine:3.18
WORKDIR /app
COPY --from=builder /app/web-api .
EXPOSE 8080
CMD ["./web-api"]

# 构建命令示例：
# 单架构: docker build -t myapp:latest .
# 多架构: docker buildx build --platform linux/amd64,linux/arm64 -t myapp:latest --push .

# 使用说明：
# 1. 修改二进制文件名 (web-api -> your-app-name)
# 2. 修改端口号 (8080 -> your-port)
# 3. 如果使用CGO，设置 CGO_ENABLED=1 并安装gcc
# 4. 如果有go.mod，取消注释依赖下载部分
