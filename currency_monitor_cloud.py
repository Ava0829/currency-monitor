#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端汇率监控脚本 - 适用于GitHub Actions/服务器/云函数
文件名: currency_monitor_cloud.py
为用户 guozaitou0829@gmail.com 定制
监控 AUD/CNY 汇率，低于 4.5 时发送邮件通知
"""

import requests
import smtplib
import os
import json
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class CloudCurrencyMonitor:
    def __init__(self):
        # 从环境变量获取配置
        self.alert_threshold = float(os.getenv('ALERT_THRESHOLD', '4.5'))
        self.email_sender = os.getenv('EMAIL_SENDER', 'your_email@gmail.com')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        self.email_receiver = os.getenv('EMAIL_RECEIVER', 'guozaitou0829@gmail.com')
        self.webhook_url = os.getenv('WEBHOOK_URL', '')  # 可选：Webhook通知
        
        # 状态管理（使用GitHub Gist或外部存储）
        self.last_alert_rate = None
        
    def log(self, message, level="INFO"):
        """简单日志函数"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {level}: {message}"
        print(log_msg)
        
        # 写入日志文件（用于Actions artifact）
        with open(f'monitor_{datetime.now().strftime("%Y%m%d")}.log', 'a', encoding='utf-8') as f:
            f.write(log_msg + '\n')
    
    def get_exchange_rate(self):
        """获取AUD/CNY汇率"""
        apis = [
            "https://api.exchangerate-api.com/v4/latest/AUD",
            "https://api.fixer.io/latest?base=AUD&symbols=CNY",
            "https://open.er-api.com/v6/latest/AUD"
        ]
        
        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                # 处理不同API的响应格式
                if 'rates' in data and 'CNY' in data['rates']:
                    rate = data['rates']['CNY']
                    self.log(f"✅ 成功获取汇率: 1 AUD = {rate:.4f} CNY (来源: {api_url})")
                    return rate
                    
            except Exception as e:
                self.log(f"❌ API失败 {api_url}: {e}", "ERROR")
                continue
        
        self.log("🚨 所有汇率API都失败了！", "ERROR")
        return None
    
    def send_email_alert(self, rate):
        """发送邮件通知到 guozaitou0829@gmail.com"""
        if not self.email_sender or not self.email_password:
            self.log("📧 邮件配置不完整，跳过邮件发送", "WARNING")
            return False
            
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_sender
            msg['To'] = self.email_receiver
            msg['Subject'] = f"🚨 汇率预警 - AUD/CNY: {rate:.4f}"
            
            # HTML邮件内容（精美格式）
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">🚨 汇率预警</h1>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">澳币兑人民币监控系统</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                    <div style="background: #dc3545; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <h2 style="margin: 0; font-size: 20px;">⚠️ 汇率已低于预设阈值！</h2>
                    </div>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">当前汇率:</td>
                                <td style="padding: 10px; border-bottom: 1px solid #eee; color: #dc3545; font-size: 18px; font-weight: bold;">1 AUD = {rate:.4f} CNY</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">预警阈值:</td>
                                <td style="padding: 10px; border-bottom: 1px solid #eee;">{self.alert_threshold}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">触发时间:</td>
                                <td style="padding: 10px; border-bottom: 1px solid #eee;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">联系电话:</td>
                                <td style="padding: 10px; border-bottom: 1px solid #eee;">18069364956</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="margin-top: 20px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h3 style="margin-top: 0; color: #495057;">💰 换算参考</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li style="padding: 5px 0; border-bottom: 1px solid #f0f0f0;">• 100 AUD = <strong>{rate * 100:.2f} CNY</strong></li>
                            <li style="padding: 5px 0; border-bottom: 1px solid #f0f0f0;">• 500 AUD = <strong>{rate * 500:.2f} CNY</strong></li>
                            <li style="padding: 5px 0; border-bottom: 1px solid #f0f0f0;">• 1,000 AUD = <strong>{rate * 1000:.2f} CNY</strong></li>
                            <li style="padding: 5px 0; border-bottom: 1px solid #f0f0f0;">• 5,000 AUD = <strong>{rate * 5000:.2f} CNY</strong></li>
                            <li style="padding: 5px 0;">• 10,000 AUD = <strong>{rate * 10000:.2f} CNY</strong></li>
                        </ul>
                    </div>
                    
                    <div style="margin-top: 20px; padding: 15px; background: #e7f3ff; border-left: 4px solid #007bff; border-radius: 4px;">
                        <p style="margin: 0; color: #0056b3; font-size: 14px;">
                            📱 这是自动监控系统发送的通知邮件。<br>
                            💻 监控程序运行在云端，24小时不间断监控。<br>
                            📧 邮件接收: guozaitou0829@gmail.com<br>
                            📞 联系电话: 18069364956
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 纯文本版本（备用）
            text_body = f"""
🚨 汇率预警通知

当前汇率: 1 AUD = {rate:.4f} CNY
预警阈值: {self.alert_threshold}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
联系电话: 18069364956

💰 换算参考:
- 100 AUD = {rate * 100:.2f} CNY
- 500 AUD = {rate * 500:.2f} CNY
- 1,000 AUD = {rate * 1000:.2f} CNY
- 5,000 AUD = {rate * 5000:.2f} CNY
- 10,000 AUD = {rate * 10000:.2f} CNY

📧 这是发送给 guozaitou0829@gmail.com 的自动预警邮件
💻 24小时云端监控系统
            """
            
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # 发送邮件
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email_sender, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_sender, self.email_receiver, text)
            server.quit()
            
            self.log(f"📧 邮件通知已发送到 {self.email_receiver}")
            return True
            
        except Exception as e:
            self.log(f"📧 邮件发送失败: {e}", "ERROR")
            return False
    
    def send_webhook_notification(self, rate):
        """发送Webhook通知（可接入微信、钉钉、Slack等）"""
        if not self.webhook_url:
            return False
            
        try:
            payload = {
                "msgtype": "text",
                "text": {
                    "content": f"🚨 汇率预警！\n\n当前 AUD/CNY 汇率: {rate:.4f}\n已低于预设阈值: {self.alert_threshold}\n\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n联系: 18069364956"
                }
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.log("📱 Webhook通知已发送")
            return True
            
        except Exception as e:
            self.log(f"📱 Webhook发送失败: {e}", "ERROR")
            return False
    
    def should_send_alert(self, current_rate):
        """判断是否需要发送警报（避免重复发送）"""
        # 简单的重复检测：如果汇率变化不大，则不重复发送
        if self.last_alert_rate is None:
            return True
        
        rate_change = abs(current_rate - self.last_alert_rate) / self.last_alert_rate
        return rate_change > 0.001  # 汇率变化超过0.1%才重新发送
    
    def run_single_check(self):
        """执行一次检查（适用于云函数/GitHub Actions）"""
        self.log("🚀 开始执行汇率检查")
        self.log(f"🎯 监控配置: AUD/CNY < {self.alert_threshold}")
        self.log(f"📧 接收邮箱: {self.email_receiver}")
        self.log(f"📱 联系电话: 18069364956")
        
        # 获取汇率
        rate = self.get_exchange_rate()
        if rate is None:
            self.log("❌ 无法获取汇率，本次检查结束", "ERROR")
            return False
        
        # 判断是否需要预警
        status = "🟢 正常" if rate >= self.alert_threshold else "🔴 预警"
        self.log(f"📊 汇率状态: {status} (当前: {rate:.4f}, 阈值: {self.alert_threshold})")
        
        if rate < self.alert_threshold:
            if self.should_send_alert(rate):
                self.log(f"🚨 触发预警！开始发送通知...")
                
                # 发送各种通知
                email_sent = self.send_email_alert(rate)
                webhook_sent = self.send_webhook_notification(rate)
                
                if email_sent or webhook_sent:
                    self.last_alert_rate = rate
                    self.log("✅ 预警通知发送完成")
                else:
                    self.log("❌ 所有通知方式都失败了", "ERROR")
                    
            else:
                self.log("⏳ 汇率仍低于阈值，但变化不大，跳过重复通知")
        
        self.log("✅ 本次检查完成")
        return True

def main():
    """主函数"""
    print("🌟 云端汇率监控系统启动")
    print("=" * 50)
    print("👤 为用户定制: guozaitou0829@gmail.com")
    print("📱 联系电话: 18069364956") 
    print("💱 监控汇率: AUD/CNY")
    print("🎯 预警阈值: 4.5")
    print("=" * 50)
    
    # 检查必要的环境变量
    required_vars = ['EMAIL_SENDER', 'EMAIL_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ 缺少必要的环境变量: {missing_vars}")
        print("请在GitHub Secrets中设置以下变量:")
        print("- EMAIL_SENDER: 发送方Gmail邮箱")
        print("- EMAIL_PASSWORD: Gmail应用密码")
        print("- EMAIL_RECEIVER: 接收方邮箱（可选，默认: guozaitou0829@gmail.com）")
        print("- ALERT_THRESHOLD: 预警阈值（可选，默认: 4.5）")
        return False
    
    # 创建监控器并执行检查
    monitor = CloudCurrencyMonitor()
    return monitor.run_single_check()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
