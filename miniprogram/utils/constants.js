// 匹克球等级
const PICKLEBALL_LEVELS = {
  P1: { label: 'P1 新手', color: '#9E9E9E', desc: '刚接触匹克球，正在学习基础规则和动作' },
  P2: { label: 'P2 初级', color: '#4CAF50', desc: '掌握基本动作，能打简单对打' },
  P3: { label: 'P3 进阶', color: '#2196F3', desc: '技术稳定，有一定战术意识' },
  P4: { label: 'P4 中高级', color: '#9C27B0', desc: '技术全面，具备较强比赛能力' },
  P5: { label: 'P5 高水平业余', color: '#FF9800', desc: '技术出色，能参加高水平业余比赛' },
  P6: { label: 'P6 竞技型', color: '#F44336', desc: '接近专业水平，参加竞技赛事' },
};

// 信用分规则
const CREDIT_RULES = {
  PUNCTUAL: { change: 2, reason: '准时到场' },
  PUNCTUAL_3X: { change: 5, reason: '连续3次准时' },
  LATE_15MIN: { change: -5, reason: '迟到15分钟以上' },
  CANCEL_2H: { change: -10, reason: '开局前2小时内取消' },
  NO_SHOW: { change: -20, reason: '确认后未到场' },
  MISSING: { change: -25, reason: '无故失联' },
  GOOD_REVIEW: { change: 2, reason: '获得好评' },
  BAD_REVIEW: { change: -3, reason: '获得差评' },
};

// 信用分等级
const CREDIT_LEVELS = [
  { min: 90, label: '信誉极佳', color: '#4CAF50', icon: '⭐' },
  { min: 75, label: '信誉良好', color: '#2196F3', icon: '👍' },
  { min: 60, label: '信誉一般', color: '#FF9800', icon: '⚠️' },
  { min: 0, label: '信誉较差', color: '#F44336', icon: '⛔' },
];

// 球局状态
const GAME_STATUS = {
  OPEN: { label: '招募中', color: '#4CAF50' },
  FULL: { label: '已满员', color: '#FF9800' },
  CANCELLED: { label: '已取消', color: '#9E9E9E' },
  COMPLETED: { label: '已完成', color: '#2196F3' },
};

// 参与者状态
const PARTICIPANT_STATUS = {
  PENDING: '待确认',
  APPROVED: '已确认',
  REJECTED: '已拒绝',
  CANCELLED: '已取消',
};

// 评价标签
const REVIEW_TAGS_POSITIVE = ['准时守信', '球技出色', '态度友好', '乐于助人', '遵守规则', '沟通顺畅'];
const REVIEW_TAGS_NEGATIVE = ['迟到', '态度差', '规则不熟', '临时放鸽子', '难以沟通'];

const INITIAL_CREDIT_SCORE = 80;

module.exports = {
  PICKLEBALL_LEVELS,
  CREDIT_RULES,
  CREDIT_LEVELS,
  GAME_STATUS,
  PARTICIPANT_STATUS,
  REVIEW_TAGS_POSITIVE,
  REVIEW_TAGS_NEGATIVE,
  INITIAL_CREDIT_SCORE,
};
