const KEYS = {
  entitlement: 'phase3Entitlement',
  orders: 'phase3Orders',
  reports: 'phase3Reports',
  visuals: 'phase3Visuals'
};

export const plans = [
  { id: 'starter', name: '灵感补给包', price: 9.9, quota: 10, tag: '轻量体验', description: '适合偶尔使用，购买后增加 10 次生成额度。' },
  { id: 'pro', name: '创意进阶包', price: 29.9, quota: 40, tag: '推荐', description: '包含 40 次生成额度与 1 份高级报告演示权益。' },
  { id: 'brand', name: '品牌启动包', price: 69.9, quota: 100, tag: '企业优选', description: '包含 100 次生成额度、3 份报告和 3 次视觉任务演示权益。' }
];

const read = (key, fallback) => uni.getStorageSync(key) || fallback;
const write = (key, value) => { uni.setStorageSync(key, value); return value; };
const now = () => new Date().toISOString();
const makeNo = (prefix) => `${prefix}${Date.now()}${Math.floor(Math.random() * 90 + 10)}`;

export const getEntitlement = () => read(KEYS.entitlement, { plan: '免费版', paid_quota: 0, report_quota: 0, visual_quota: 0 });
export const getOrders = () => read(KEYS.orders, []);
export const getReports = () => read(KEYS.reports, []);
export const getVisuals = () => read(KEYS.visuals, []);

export const mockPurchase = (plan) => {
  const order = { id: makeNo('O'), order_no: makeNo('AI'), product_name: plan.name, amount: plan.price, status: 'paid', created_at: now() };
  write(KEYS.orders, [order, ...getOrders()]);
  const current = getEntitlement();
  const bonus = plan.id === 'brand' ? { report: 3, visual: 3 } : plan.id === 'pro' ? { report: 1, visual: 0 } : { report: 0, visual: 0 };
  write(KEYS.entitlement, { plan: plan.name, paid_quota: current.paid_quota + plan.quota, report_quota: current.report_quota + bonus.report, visual_quota: current.visual_quota + bonus.visual });
  return order;
};

export const createReport = (name) => {
  const report = { id: makeNo('R'), name: name || '未命名候选', status: 'completed', score: 88, created_at: now(), summary: '名字意象清晰、读音流畅，具备良好的传播潜力。', dimensions: { 文化寓意: 92, 音韵传播: 86, 需求匹配: 90, 可用性: 82 } };
  write(KEYS.reports, [report, ...getReports()]);
  return report;
};

export const createVisual = ({ name, style, color }) => {
  const visual = { id: makeNo('V'), name: name || '未命名品牌', style, color, status: 'completed', created_at: now(), concept: `${style}风格，以${color}为主色，强调简洁识别与品牌延展性。` };
  write(KEYS.visuals, [visual, ...getVisuals()]);
  return visual;
};

export const phase3MockEnabled = true;
