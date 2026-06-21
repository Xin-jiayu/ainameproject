DB_URI = "mysql+aiomysql://root:123456@localhost:3306/ainame?charset=utf8mb4"

# 邮箱相关配置
MAIL_USERNAME="2776599147@qq.com"
MAIL_PASSWORD="fxseblojhbqzdeja"    #授权码
MAIL_FROM="2776599147@qq.com"
MAIL_PORT=587
MAIL_SERVER="smtp.qq.com"
MAIL_FROM_NAME="ainameapp"
MAIL_STARTTLS=True # 显式加密
MAIL_SSL_TLS=False # 隐式加密

JWT_SECRET_KEY="asdfb345erts23525sry585ojug"  # 自定义
from datetime import timedelta
JWT_ACCESS_TOKEN_EXPIRES=timedelta(days=1)
JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=30)