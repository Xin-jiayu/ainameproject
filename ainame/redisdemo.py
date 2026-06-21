import redis
REDIS_URL = "redis://localhost:6379/0"
redis_client = redis.from_url(REDIS_URL,decode_responses=True)
# #存入数据
# redis_client.set("username","admin")
# redis_client.set("password","123456")
# # 获取数据
# username = redis_client.get("username")
# print(username)
# print(redis_client.exists("username"))
# print(redis_client.exists("aaa"))
# redis_client.delete("username")
# print(redis_client.exists("username"))

# 存入redis验证码 setex(键,过期秒数,值)
# 示例：有效期300秒，存储邮箱对应的验证码
redis_client.setex("mail", 300, "654321")
# 判断是否有效
data = redis_client.get("mail")
if data:
    print(f"验证码{data}有效")