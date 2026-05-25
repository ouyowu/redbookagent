const api = require('../../utils/api');
const { formatDate, getSpotsLeft, showToast, showLoading, hideLoading } = require('../../utils/util');

Page({
  data: {
    games: [],
    loading: false,
    filters: {
      status: 'OPEN',
      level: '',
      district: '',
    },
    statusTabs: [
      { key: 'OPEN', label: '招募中' },
      { key: 'FULL', label: '已满员' },
      { key: 'COMPLETED', label: '已结束' },
    ],
    levelOptions: [
      { key: '', label: '全部等级' },
      { key: 'P1', label: 'P1 新手' },
      { key: 'P2', label: 'P2 初级' },
      { key: 'P3', label: 'P3 进阶' },
      { key: 'P4', label: 'P4 中高级' },
      { key: 'P5', label: 'P5 高水平' },
      { key: 'P6', label: 'P6 竞技型' },
    ],
    activeStatusIndex: 0,
  },

  onLoad() {
    this.loadGames();
  },

  onShow() {
    this.loadGames();
  },

  async loadGames() {
    this.setData({ loading: true });
    try {
      const { status, level, district } = this.data.filters;
      const result = await api.getGames({ status: status || undefined, level: level || undefined });
      const games = result.list.map(g => ({
        ...g,
        formattedDate: formatDate(g.date),
        spotsLeft: getSpotsLeft(g),
      }));
      this.setData({ games });
    } catch (err) {
      showToast('加载失败');
    } finally {
      this.setData({ loading: false });
    }
  },

  onStatusTabChange(e) {
    const index = e.currentTarget.dataset.index;
    const tab = this.data.statusTabs[index];
    this.setData({
      activeStatusIndex: index,
      'filters.status': tab.key,
    });
    this.loadGames();
  },

  onLevelFilter(e) {
    this.setData({ 'filters.level': e.detail.value });
    this.loadGames();
  },

  onGameTap(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({ url: `/pages/game-detail/game-detail?id=${id}` });
  },

  onCreateGame() {
    wx.navigateTo({ url: '/pages/game-create/game-create' });
  },

  onPullDownRefresh() {
    this.loadGames().then(() => wx.stopPullDownRefresh());
  },
});
