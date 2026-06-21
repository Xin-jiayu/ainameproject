// http/http.js

// 动态获取环境：开发模式连接本地后端，发行模式连接线上域名
const BASE_URL = "http://192.168.1.91:8000";

/**
 * 核心请求封装函数
 */
const request = (url, options) => {
  // 每次请求前，动态获取最新的 token
  const token = uni.getStorageSync("token");
  
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      header: {
        "content-type": "application/json",
        "authorization": token ? "Bearer " + token : ""
      },
      ...options,
      success: (res) => {
        // HTTP 状态码 200 代表完全成功
        if (res.statusCode === 200) {
          resolve(res.data);
        } else {
          // --- 核心修复：智能解析 FastAPI 的错误格式 ---
          let errorMsg = '服务器请求失败';
          
          if (res.data && Array.isArray(res.data.detail)) {
            // 捕获 Pydantic 数据校验 422 错误 (Array 格式)
            // 取第一条错误信息并展示
            errorMsg = res.data.detail[0].msg || '表单参数校验失败';
          } else if (res.data && typeof res.data.detail === 'string') {
            // 捕获我们自定义的 HttpException 错误 (String 格式)
            errorMsg = res.data.detail;
          }
          
          // 确保 title 绝对是字符串，防止前端崩溃红屏
          uni.showToast({ 
            title: String(errorMsg), 
            icon: 'none', 
            duration: 3000 
          });
          
          // 将错误抛出，供业务层 catch 处理（比如用来关掉 loading 动画）
          reject(res.data);
        }
      },
      fail: (err) => {
        uni.showToast({ title: '网络连接断开，请检查网络', icon: 'none' });
        reject(err);
      }
    });
  });
};

/**
 * 专门处理文件上传的封装函数 (针对 RAG 私有知识库)
 */
const uploadFile = (url, filePath) => {
  const token = uni.getStorageSync("token");
  
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: BASE_URL + url,
      filePath: filePath,
      name: 'file',
      header: { 
        "authorization": token ? "Bearer " + token : "" 
      },
      success: (res) => {
        if (res.statusCode === 200) {
          // uni.uploadFile 返回的 data 是字符串格式的 JSON，需要手动 parse
          resolve(JSON.parse(res.data));
        } else {
          uni.showToast({ title: '文件上传失败', icon: 'none' });
          reject(res);
        }
      },
      fail: (err) => {
        uni.showToast({ title: '网络异常，上传中断', icon: 'none' });
        reject(err);
      }
    });
  });
};

// 导出所有后端接口
export default {
  // ================= 1. 账号鉴权接口 =================
  getEmailCode: (email) => request("/auth/code?email=" + email, { method: 'GET' }),
  register: (data) => request("/auth/register", { method: 'POST', data }),
  login: (data) => request("/auth/login", { method: 'POST', data }),
  
  // ================= 2. 智能体核心工作流 =================
  generateName: (data) => request("/names/generate", { method: 'POST', data }), // 首次起名 (无记忆)
  feedbackName: (data) => request("/names/feedback", { method: 'POST', data }), // 多轮微调 (带记忆 thread_id)
  
  // ================= 3. RAG 知识库接口 =================
  uploadKnowledge: (filePath) => uploadFile("/knowledge/upload", filePath)
};