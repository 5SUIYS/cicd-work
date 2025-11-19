#!/usr/bin/env python3
import os
import requests
import urllib.parse
from flask import Flask, request, jsonify
import json
from datetime import datetime

class VoiceNotificationAPI:
    def __init__(self, accesskey, secret):
        self.accesskey = accesskey
        self.secret = secret
        self.base_url = "http://api.1cloudsp.com"
    
    def send_voice_notification(self, template_id, mobile, content=None):
        """发送语音通知"""
        url = f"{self.base_url}/noticevoice/api/v2/send"
        
        data = {
            'accesskey': self.accesskey,
            'secret': self.secret,
            'templateId': template_id,
            'mobile': mobile
        }
        
        if content:
            data['content'] = urllib.parse.quote(content, encoding='utf-8')
        
        try:
            response = requests.post(url, data=data)
            result = response.json()
            
            if result.get('code') == "0" or result.get('code') == 0:
                print(f"✅ 语音通知发送成功，批次ID: {result.get('batchId')}")
                return True, result
            else:
                print(f"❌ 语音通知发送失败: {result.get('msg')}")
                return False, result
                
        except Exception as e:
            print(f"❌ 语音通知请求异常: {e}")
            return False, None

# Flask应用
app = Flask(__name__)

# 配置语音通知
VOICE_CONFIG = {
    'accesskey': os.environ.get('VOICE_ACCESS_KEY', 'vy2VVE3Kb6FLCVlw'),
    'secret': os.environ.get('VOICE_SECRET', 'EnmvlEXzQH5zfXVf8zjhskAxfFRE2BK3'),
    'template_id': os.environ.get('VOICE_TEMPLATE_ID', '2038'),
    'mobile': os.environ.get('VOICE_MOBILE', '19299178449')
}

voice_api = VoiceNotificationAPI(VOICE_CONFIG['accesskey'], VOICE_CONFIG['secret'])

def should_send_voice_alert(alert):
    """判断是否需要发送语音通知（最高级别告警）"""
    labels = alert.get('labels', {})
    
    # 最高级别告警条件
    critical_conditions = [
        labels.get('severity') == 'critical',
        labels.get('severity') == 'high',
        'down' in labels.get('alertname', '').lower(),
        'outage' in labels.get('alertname', '').lower(),
        'exceeded' in labels.get('alertname', '').lower(),
        labels.get('service') in ['ElastiCache', 'RDS', 'EKS']  # 关键服务
    ]
    
    return any(critical_conditions)

def format_alert_content(alert):
    """格式化告警内容为语音通知"""
    labels = alert.get('labels', {})
    annotations = alert.get('annotations', {})
    
    # 提取关键信息
    alertname = labels.get('alertname', '未知告警')
    instance = labels.get('instance', labels.get('resource', '未知资源'))
    service = labels.get('service', labels.get('job', '未知服务'))
    
    # 构建语音内容（简短明了）
    content = f"{service}##服务异常##{alertname}##请立即处理"
    
    return content

@app.route('/webhook/voice', methods=['POST'])
def alertmanager_voice_webhook():
    """接收Alertmanager告警并发送语音通知"""
    try:
        alert_data = request.json
        print(f"收到Alertmanager告警: {json.dumps(alert_data, indent=2, ensure_ascii=False)}")
        
        alerts = alert_data.get('alerts', [])
        status = alert_data.get('status', 'unknown')
        
        # 只处理firing状态的告警
        if status != 'firing':
            print(f"忽略非firing状态的告警: {status}")
            return jsonify({"status": "ignored", "reason": f"status is {status}"})
        
        critical_alerts = []
        
        # 筛选需要语音通知的告警
        for alert in alerts:
            if should_send_voice_alert(alert):
                critical_alerts.append(alert)
        
        if not critical_alerts:
            print("没有需要语音通知的关键告警")
            return jsonify({"status": "ignored", "reason": "no critical alerts"})
        
        # 发送语音通知
        success_count = 0
        for alert in critical_alerts:
            content = format_alert_content(alert)
            
            success, result = voice_api.send_voice_notification(
                template_id=VOICE_CONFIG['template_id'],
                mobile=VOICE_CONFIG['mobile'],
                content=content
            )
            
            if success:
                success_count += 1
            
            # 记录告警日志
            print(f"告警处理: {alert.get('labels', {}).get('alertname')} - {'成功' if success else '失败'}")
        
        return jsonify({
            "status": "success",
            "message": f"处理了 {len(critical_alerts)} 个关键告警，成功发送 {success_count} 个语音通知"
        })
        
    except Exception as e:
        print(f"处理告警失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/webhook/test', methods=['POST'])
def test_voice_webhook():
    """测试语音通知"""
    try:
        data = request.json or {}
        
        # 构建测试告警
        test_content = data.get('content', 'ElastiCache##网络超限##测试告警##请处理')
        
        success, result = voice_api.send_voice_notification(
            template_id=VOICE_CONFIG['template_id'],
            mobile=VOICE_CONFIG['mobile'],
            content=test_content
        )
        
        if success:
            return jsonify({"status": "success", "message": "测试语音通知发送成功"})
        else:
            return jsonify({"status": "error", "message": "测试语音通知发送失败"}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == "__main__":
    print("启动语音通知Webhook服务...")
    print(f"配置信息:")
    print(f"  - 模板ID: {VOICE_CONFIG['template_id']}")
    print(f"  - 通知手机: {VOICE_CONFIG['mobile']}")
    print(f"  - Webhook地址: http://localhost:5000/webhook/voice")
    print(f"  - 测试地址: http://localhost:5000/webhook/test")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
