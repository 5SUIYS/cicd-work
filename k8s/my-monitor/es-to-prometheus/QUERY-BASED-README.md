# Query-Based Elasticsearch Exporter

## 核心设计理念

效仿 AWS CloudWatch Exporter 的设计，**以查询为核心**，而非以索引分类为核心。

### AWS CloudWatch Exporter 的设计
```
aws_rds_free_storage_space_average{dbinstance_identifier="rds-all-test-s-2"} 3.4068856832E10
aws_rds_free_storage_space_average{dbinstance_identifier="rds-all-test-s-1"} 3.3927016448E10
aws_rds_free_storage_space_average{dbinstance_identifier="rds-mars-kong"} 2.612076544E9
```

**特点：**
- 以资源（RDS 实例）为核心
- 每个资源独立一行，不合并
- 使用 label 区分不同资源

### 本导出器的设计
```
es_http_5xx_errors_total{index_pattern="mars-kong-nginx-logs-", job="elasticsearch", instance=""} 42
es_http_5xx_errors_total{index_pattern="mars-api-app-k8s-logs-", job="elasticsearch", instance=""} 15
es_http_5xx_errors_total{index_pattern="mars-backend-app-k8s-logs-", job="elasticsearch", instance=""} 8
```

**特点：**
- 以查询（如 http_5xx_errors）为核心
- 每个 index pattern 独立一行，不合并
- 使用 label 区分不同 index

## 架构对比

### 旧架构（以索引分类为核心）
```
配置 → 索引分类 → 标准指标 → 查询
```
- 先定义索引类别（kong_nginx, api_app 等）
- 为每个类别应用所有标准指标
- 复杂的分类规则和优先级

### 新架构（以查询为核心）
```
配置 → 查询定义 → 目标索引 → 执行
```
- 直接定义查询（http_5xx_errors, slow_requests 等）
- 为每个查询指定目标 index patterns
- 简单直接，易于扩展

## 配置示例

```yaml
queries:
  - name: "http_5xx_errors"
    description: "HTTP 5xx errors by index"
    query:
      query:
        bool:
          must:
            - range:
                response_code:
                  gte: 500
    indices:
      - "mars-kong-nginx-logs-*"
      - "mars-api-app-k8s-logs-*"
```

## 添加新查询

只需在配置中添加新的查询定义：

```yaml
queries:
  - name: "custom_business_error"
    description: "Custom business error"
    query:
      query:
        match:
          error_code: "BUSINESS_ERROR_001"
    indices:
      - "mars-payment-logs-*"
      - "mars-order-logs-*"
```

## Metrics 输出格式

```
# HELP es_http_5xx_errors_total HTTP 5xx errors by index
# TYPE es_http_5xx_errors_total gauge
es_http_5xx_errors_total{index_pattern="mars-kong-nginx-logs-",job="elasticsearch",instance=""} 42.0
es_http_5xx_errors_total{index_pattern="mars-api-app-k8s-logs-",job="elasticsearch",instance=""} 15.0

# HELP es_slow_requests_total Requests slower than 1 second by index
# TYPE es_slow_requests_total gauge
es_slow_requests_total{index_pattern="mars-kong-nginx-logs-",job="elasticsearch",instance=""} 128.0
```

## 部署

```bash
# 应用配置
kubectl apply -f query-based-config.yaml

# 部署导出器
kubectl apply -f query-based-exporter.yaml

# 查看 metrics
kubectl port-forward -n monitoring svc/es-query-exporter 8080:8080
curl http://localhost:8080/metrics
```

## 优势

1. **简单直接**：查询即配置，无需复杂的分类规则
2. **易于扩展**：添加新查询只需添加配置项
3. **独立监控**：每个 index 独立一行，便于告警和可视化
4. **灵活性高**：可以为不同查询指定不同的 index patterns
5. **符合 Prometheus 最佳实践**：类似 AWS CloudWatch Exporter 的设计
