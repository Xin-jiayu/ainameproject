import { API_CONFIG, API_ENDPOINTS, buildApiUrl, buildQuery } from "@/config/api.js";

const getErrorMessage = (data) => {
  if (data && Array.isArray(data.detail)) {
    return data.detail[0]?.msg || "表单参数校验失败";
  }
  if (data && typeof data.detail === "string") return data.detail;
  return "服务器请求失败";
};

const redirectToLogin = () => {
  uni.removeStorageSync("token");
  uni.removeStorageSync("user");
  const pages = getCurrentPages();
  const route = pages.length ? pages[pages.length - 1].route : "";
  if (route !== "pages/login/login") {
    setTimeout(() => uni.reLaunch({ url: "/pages/login/login" }), 300);
  }
};

const request = (url, options = {}) => {
  const token = uni.getStorageSync("token");
  return new Promise((resolve, reject) => {
    uni.request({
      url: buildApiUrl(url),
      timeout: API_CONFIG.timeout,
      ...options,
      // 避免 options.header 覆盖统一鉴权头。
      header: {
        "content-type": "application/json",
        authorization: token ? `Bearer ${token}` : "",
        ...(options.header || {})
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
          return;
        }
        const message = getErrorMessage(res.data);
        if (res.statusCode === 401) redirectToLogin();
        uni.showToast({ title: String(message), icon: "none", duration: 3000 });
        reject({ statusCode: res.statusCode, message, data: res.data });
      },
      fail: (error) => {
        uni.showToast({ title: "无法连接服务器，请检查后端服务", icon: "none" });
        reject(error);
      }
    });
  });
};

const uploadFile = (url, filePath) => {
  const token = uni.getStorageSync("token");
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: buildApiUrl(url),
      timeout: API_CONFIG.uploadTimeout,
      filePath,
      name: "file",
      header: { authorization: token ? `Bearer ${token}` : "" },
      success: (res) => {
        let data = res.data;
        try { data = JSON.parse(res.data); } catch (_) {}
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(data);
          return;
        }
        const message = getErrorMessage(data) || "文件上传失败";
        if (res.statusCode === 401) redirectToLogin();
        uni.showToast({ title: String(message), icon: "none" });
        reject({ statusCode: res.statusCode, message, data });
      },
      fail: (error) => {
        uni.showToast({ title: "网络异常，上传中断", icon: "none" });
        reject(error);
      }
    });
  });
};

export default {
  getEmailCode: (email) => request(buildQuery(API_ENDPOINTS.auth.code, { email }), { method: "GET" }),
  register: (data) => request(API_ENDPOINTS.auth.register, { method: "POST", data }),
  login: (data) => request(API_ENDPOINTS.auth.login, { method: "POST", data }),
  generateName: (data) => request(API_ENDPOINTS.names.generate, { method: "POST", data }),
  feedbackName: (data) => request(API_ENDPOINTS.names.feedback, { method: "POST", data }),
  getNameRecords: (skip = 0, limit = 20) => request(buildQuery(API_ENDPOINTS.names.records, { skip, limit }), { method: "GET" }),
  getNameRecord: (id) => request(API_ENDPOINTS.names.record(id), { method: "GET" }),
  deleteNameRecord: (id) => request(API_ENDPOINTS.names.record(id), { method: "DELETE" }),
  uploadKnowledge: (filePath) => uploadFile(API_ENDPOINTS.knowledge.upload, filePath),
  getKnowledgeFiles: (skip = 0, limit = 20) => request(buildQuery(API_ENDPOINTS.knowledge.files, { skip, limit }), { method: "GET" }),
  getKnowledgeFile: (id) => request(API_ENDPOINTS.knowledge.file(id), { method: "GET" })
};
