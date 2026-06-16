const { PICKLEBALL_LEVELS, CREDIT_LEVELS } = require('./constants');

function getLevelInfo(level) {
  return PICKLEBALL_LEVELS[level] || PICKLEBALL_LEVELS.P1;
}

function getCreditLevel(score) {
  return CREDIT_LEVELS.find(l => score >= l.min) || CREDIT_LEVELS[CREDIT_LEVELS.length - 1];
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
  const weekday = weekdays[date.getDay()];
  return `${month}月${day}日 周${weekday}`;
}

function formatDateTime(dateStr, timeStr) {
  if (!dateStr) return '';
  return `${formatDate(dateStr)} ${timeStr || ''}`;
}

function getGameStatusDisplay(game) {
  const now = new Date();
  const gameDate = new Date(`${game.date} ${game.startTime}`);
  if (game.status === 'CANCELLED') return { label: '已取消', color: '#9E9E9E' };
  if (game.status === 'COMPLETED' || gameDate < now) return { label: '已结束', color: '#9E9E9E' };
  if (game.status === 'FULL') return { label: '已满员', color: '#FF9800' };
  return { label: '招募中', color: '#4CAF50' };
}

function getSpotsLeft(game) {
  return Math.max(0, game.maxPlayers - game.currentPlayers);
}

function showToast(title, icon = 'none', duration = 2000) {
  wx.showToast({ title, icon, duration });
}

function showLoading(title = '加载中...') {
  wx.showLoading({ title, mask: true });
}

function hideLoading() {
  wx.hideLoading();
}

function navigateTo(url) {
  wx.navigateTo({ url });
}

function navigateBack() {
  wx.navigateBack();
}

module.exports = {
  getLevelInfo,
  getCreditLevel,
  formatDate,
  formatDateTime,
  getGameStatusDisplay,
  getSpotsLeft,
  showToast,
  showLoading,
  hideLoading,
  navigateTo,
  navigateBack,
};
