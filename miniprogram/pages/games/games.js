const api = require('../../utils/api');
const { formatDate, getSpotsLeft, getLevelInfo, showToast } = require('../../utils/util');

const CARD_GRADIENTS = [
  'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
  'linear-gradient(135deg, #F093FB 0%, #F5576C 100%)',
  'linear-gradient(135deg, #43E97B 0%, #38A169 100%)',
  'linear-gradient(135deg, #FA709A 0%, #FEE140 100%)',
  'linear-gradient(135deg, #4FACFE 0%, #00F2FE 100%)',
  'linear-gradient(135deg, #F7971E 0%, #FFD200 100%)',
];

Page({
  data: {
    games: [],
    loading: false,
    filters: { status: 'OPEN', level: '' },
    statusTabs: [
      { key: 'OPEN', label: '招募中' },
      { key: 'FULL', label: '已满员' },
      { key: 'COMPLETED', label: '已结束' },
    ],
    levelOptions: [
      { key: '', label: '全部' },
      { key: 'P1', label: 'P1' },
      { key: 'P2', label: 'P2' },
      { key: 'P3', label: 'P3' },
      { key: 'P4', label: 'P4' },
      { key: 'P5', label: 'P5' },
      { key: 'P6', label: 'P6' },
    ],
    activeStatusIndex: 0,
  },

  onLoad() { this.loadGames(); },
  onShow() { this.loadGames(); },

  async loadGames() {
    this.setData({ loading: true });
    try {
      const { status, level } = this.data.filters;
      const result = await api.getGames({ status: status || undefined, level: level || undefined });
      const games = result.list.map((g, i) => ({
        ...g,
        formattedDate: formatDate(g.date),
        spotsLeft: getSpotsLeft(g),
        cardGradient: CARD_GRADIENTS[i % CARD_GRADIENTS.length],
        participants: g.participants || [],
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
    this.setData({ activeStatusIndex: Number(index), 'filters.status': tab.key });
    this.loadGames();
  },

  onLevelChip(e) {
    const level = e.currentTarget.dataset.level;
    this.setData({ 'filters.level': level });
    this.loadGames();
  },

  onGameTap(e) {
    wx.navigateTo({ url: `/pages/game-detail/game-detail?id=${e.currentTarget.dataset.id}` });
  },

  onCreateGame() {
    wx.navigateTo({ url: '/pages/game-create/game-create' });
  },

  onPullDownRefresh() {
    this.loadGames().then(() => wx.stopPullDownRefresh());
  },
});
