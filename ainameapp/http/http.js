const BASE_URL = "http://127.0.0.1:8000";

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
      url: BASE_URL + url,
      header: {
        "content-type": "application/json",
        authorization: token ? `Bearer ${token}` : ""
      },
      ...options,
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
      url: BASE_URL + url,
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
  getEmailCode: (email) => request(`/auth/code?email=${encodeURIComponent(email)}`, { method: "GET" }),
  register: (data) => request("/auth/register", { method: "POST", data }),
  login: (data) => request("/auth/login", { method: "POST", data }),
  generateName: (data) => request("/names/generate", { method: "POST", data }),
  feedbackName: (data) => request("/names/feedback", { method: "POST", data }),
  getNameRecords: (skip = 0, limit = 20) => request(`/names/records?skip=${skip}&limit=${limit}`, { method: "GET" }),
  getNameRecord: (id) => request(`/names/records/${id}`, { method: "GET" }),
  deleteNameRecord: (id) => request(`/names/records/${id}`, { method: "DELETE" }),
  uploadKnowledge: (filePath) => uploadFile("/knowledge/upload", filePath),
  getKnowledgeFiles: (skip = 0, limit = 20) => request(`/knowledge/files?skip=${skip}&limit=${limit}`, { method: "GET" }),
  getKnowledgeFile: (id) => request(`/knowledge/files/${id}`, { method: "GET" })
};
