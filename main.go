package main

import (
    "encoding/json"
    _ "fmt"
    "net/http"
    "os"
    "time"
)

// 定义服务信息结构体
type Info struct {
    Version string `json:"version"`
    Hostname string `json:"hostname"`
    Timestamp string `json:"timestamp"`
}

// 健康检查接口处理函数
func healthHandler(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    w.Write([]byte("okkkkkkkkkk"))
}

// 服务信息接口处理函数
func infoHandler(w http.ResponseWriter, r *http.Request) {
    hostname, _ := os.Hostname()
    info := Info{
        Version: "v1.0.0",
        Hostname: hostname,
        Timestamp: time.Now().Format("2006-01-02 15:04:05"),
    }
    json.NewEncoder(w).Encode(info)
}

func main() {
    http.HandleFunc("/health", healthHandler)
    http.HandleFunc("/api/info", infoHandler)
    http.ListenAndServe(":8080", nil)
}
