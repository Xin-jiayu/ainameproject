// 前端接口统一配置。联调其他设备时，只需修改 defaultBaseUrl。
const defaultBaseUrl = "http://127.0.0.1:8000";

export const API_CONFIG = Object.freeze({
  baseUrl: defaultBaseUrl,
  timeout: 30000,
  uploadTimeout: 60000
});

export const API_ENDPOINTS = Object.freeze({
  auth: {
    code: "/auth/code",
    register: "/auth/register",
    login: "/auth/login"
  },
  names: {
    generate: "/names/generate",
    feedback: "/names/feedback",
    records: "/names/records",
    record: (id) => `/names/records/${encodeURIComponent(id)}`
  },
  knowledge: {
    upload: "/knowledge/upload",
    files: "/knowledge/files",
    file: (id) => `/knowledge/files/${encodeURIComponent(id)}`
  }
});

const normalizeBaseUrl = (value) => String(value || "").trim().replace(/\/+$/, "");

// 可在开发调试页执行 uni.setStorageSync('apiBaseUrl', 'http://局域网IP:8000') 覆盖地址。
export const getApiBaseUrl = () => normalizeBaseUrl(uni.getStorageSync("apiBaseUrl") || API_CONFIG.baseUrl);

export const setApiBaseUrl = (value) => {
  const baseUrl = normalizeBaseUrl(value);
  if (!/^https?:\/\//i.test(baseUrl)) throw new Error("接口地址必须以 http:// 或 https:// 开头");
  uni.setStorageSync("apiBaseUrl", baseUrl);
  return baseUrl;
};

export const resetApiBaseUrl = () => uni.removeStorageSync("apiBaseUrl");

export const buildQuery = (path, params = {}) => {
  const query = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join("&");
  return query ? `${path}?${query}` : path;
};

export const buildApiUrl = (path) => `${getApiBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;
