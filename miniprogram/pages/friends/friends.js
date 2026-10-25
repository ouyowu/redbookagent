const api = require('../../utils/api');
const { getLevelInfo, getCreditLevel, showToast } = require('../../utils/util');

Page({
  data: {
    players: [],
    loading: false,
    searchValue: '',
    selectedLevel: '',
    levelOptions: [
      { key: '', label: '全部' },
      { key: 'P1', label: 'P1' },
      { key: 'P2', label: 'P2' },
      { key: 'P3', label: 'P3' },
      { key: 'P4', label: 'P4' },
      { key: 'P5', label: 'P5' },
      { key: 'P6', label: 'P6' },
    ],
  },

  onLoad() {
    this.loadPlayers();
  },

  async loadPlayers() {
    this.setData({ loading: true });
    try {
      const result = await api.getPlayers({ level: this.data.selectedLevel || undefined });
      const players = result.list.map(p => ({
        ...p,
        levelInfo: getLevelInfo(p.level),
        creditLevel: getCreditLevel(p.creditScore),
      }));
      this.setData({ players });
    } catch (err) {
      showToast('加载失败');
    } finally {
      this.setData({ loading: false });
    }
  },

  onLevelSelect(e) {
    const level = e.currentTarget.dataset.level;
    this.setData({ selectedLevel: level });
    this.loadPlayers();
  },

  onPlayerTap(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({ url: `/pages/player-profile/player-profile?id=${id}` });
  },

  onSearchInput(e) {
    this.setData({ searchValue: e.detail.value });
  },

  onSearchConfirm() {
    const value = this.data.searchValue.trim();
    if (!value) {
      this.loadPlayers();
      return;
    }
    const filtered = this.data.players.filter(p =>
      p.nickName.includes(value) || p.city?.includes(value)
    );
    this.setData({ players: filtered });
  },

  onPullDownRefresh() {
    this.loadPlayers().then(() => wx.stopPullDownRefresh());
  },
});
