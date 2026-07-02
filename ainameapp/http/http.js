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
  getKnowledgeFile: (id) => request(API_ENDPOINTS.knowledge.file(id), { method: "GET" }),
  getAdminUsers: (params = {}) => request(buildQuery(API_ENDPOINTS.adminUsers.list, params), { method: "GET" }),
  updateAdminUser: (id, data) => request(API_ENDPOINTS.adminUsers.detail(id), { method: "PATCH", data }),
  setAdminUserFrozen: (id, isFrozen) => request(API_ENDPOINTS.adminUsers.freeze(id), { method: "POST", data: { is_frozen: isFrozen } }),
  resetAdminUserPassword: (id, password) => request(API_ENDPOINTS.adminUsers.resetPassword(id), { method: "POST", data: { password } }),
  deleteAdminUser: (id) => request(API_ENDPOINTS.adminUsers.detail(id), { method: "DELETE" })
  ,getCandidates: (recordId) => request(API_ENDPOINTS.candidates.byRecord(recordId), { method: "GET" })
  ,getProducts: () => request(API_ENDPOINTS.commerce.products, { method: "GET" })
  ,createOrder: (productId, requestKey) => request(API_ENDPOINTS.commerce.orders, { method: "POST", data: { product_id: productId, request_key: requestKey } })
  ,getOrders: (params = {}) => request(buildQuery(API_ENDPOINTS.commerce.orders, params), { method: "GET" })
  ,payOrder: (id) => request(API_ENDPOINTS.commerce.paySuccess(id), { method: "POST", data: { trade_no: `WEB-${Date.now()}`, callback_data: { source: "member_b_frontend" } } })
  ,closeOrder: (id, reason = "用户取消") => request(API_ENDPOINTS.commerce.closeOrder(id), { method: "POST", data: { reason } })
  ,getEntitlementAccounts: () => request(API_ENDPOINTS.commerce.accounts, { method: "GET" })
  ,getEntitlementRecords: (params = {}) => request(buildQuery(API_ENDPOINTS.commerce.records, params), { method: "GET" })
  ,createReportTask: (data) => request(API_ENDPOINTS.commerce.reports, { method: "POST", data })
  ,getReportTasks: (params = {}) => request(buildQuery(API_ENDPOINTS.commerce.reports, params), { method: "GET" })
  ,getReportDetail: (id) => request(API_ENDPOINTS.commerce.reportDetail(id), { method: "GET" })
  ,retryReportTask: (id) => request(API_ENDPOINTS.commerce.reportRetry(id), { method: "POST" })
  ,createVisualTask: (data) => request(API_ENDPOINTS.commerce.visuals, { method: "POST", data })
  ,getVisualTasks: (params = {}) => request(buildQuery(API_ENDPOINTS.commerce.visuals, params), { method: "GET" })
  ,retryVisualTask: (id) => request(API_ENDPOINTS.commerce.visualRetry(id), { method: "POST" })
  ,deleteVisualTask: (id) => request(API_ENDPOINTS.commerce.visualTask(id), { method: "DELETE" })
  ,getAdminProducts: (params = {}) => request(buildQuery(API_ENDPOINTS.adminCommerce.products, params), { method: "GET" })
  ,createAdminProduct: (data) => request(API_ENDPOINTS.adminCommerce.products, { method: "POST", data })
  ,updateAdminProduct: (id, data) => request(API_ENDPOINTS.adminCommerce.product(id), { method: "PATCH", data })
  ,setAdminProductStatus: (id, isActive) => request(API_ENDPOINTS.adminCommerce.productStatus(id), { method: "POST", data: { is_active: isActive } })
  ,getAdminOrders: (params = {}) => request(buildQuery(API_ENDPOINTS.adminCommerce.orders, params), { method: "GET" })
  ,getAdminReports: (params = {}) => request(buildQuery(API_ENDPOINTS.adminCommerce.reports, params), { method: "GET" })
  ,getAdminVisuals: (params = {}) => request(buildQuery(API_ENDPOINTS.adminCommerce.visuals, params), { method: "GET" })
  ,getAdminCommercialStats: () => request(API_ENDPOINTS.adminCommerce.stats, { method: "GET" })
  ,adjustEntitlement: (data) => request(API_ENDPOINTS.adminCommerce.adjust, { method: "POST", data })
  ,closeExpiredOrders: () => request(API_ENDPOINTS.adminCommerce.closeExpired, { method: "POST" })
};
