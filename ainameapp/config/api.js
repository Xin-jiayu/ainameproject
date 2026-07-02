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
  },
  adminUsers: {
    list: "/admin/users",
    detail: (id) => `/admin/users/${encodeURIComponent(id)}`,
    freeze: (id) => `/admin/users/${encodeURIComponent(id)}/freeze`,
    resetPassword: (id) => `/admin/users/${encodeURIComponent(id)}/reset-password`
  },
  candidates: { byRecord: (id) => `/records/${encodeURIComponent(id)}/candidates` },
  commerce: {
    products: "/products", orders: "/orders",
    order: (id) => `/orders/${encodeURIComponent(id)}`,
    paySuccess: (id) => `/orders/${encodeURIComponent(id)}/alipay-sandbox/success`,
    closeOrder: (id) => `/orders/${encodeURIComponent(id)}/close`,
    accounts: "/entitlements/accounts", records: "/entitlements/records",
    reports: "/reports/tasks", reportTask: (id) => `/reports/tasks/${encodeURIComponent(id)}`,
    reportDetail: (id) => `/reports/tasks/${encodeURIComponent(id)}/report`,
    reportRetry: (id) => `/reports/tasks/${encodeURIComponent(id)}/retry`,
    visuals: "/visual/tasks", visualTask: (id) => `/visual/tasks/${encodeURIComponent(id)}`,
    visualRetry: (id) => `/visual/tasks/${encodeURIComponent(id)}/retry`
  },
  adminCommerce: {
    products: "/admin/products", product: (id) => `/admin/products/${encodeURIComponent(id)}`,
    productStatus: (id) => `/admin/products/${encodeURIComponent(id)}/status`,
    orders: "/admin/orders", reports: "/admin/reports/tasks", visuals: "/admin/visual/tasks",
    stats: "/admin/commercial/stats", adjust: "/admin/entitlements/adjust",
    closeExpired: "/admin/orders/close-expired"
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
