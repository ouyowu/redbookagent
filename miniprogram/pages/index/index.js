const app = getApp();
const api = require('../../utils/api');
const { getLevelInfo, getCreditLevel, formatDate, showToast } = require('../../utils/util');

const CARD_GRADIENTS = [
  'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
  'linear-gradient(135deg, #F093FB 0%, #F5576C 100%)',
  'linear-gradient(135deg, #43E97B 0%, #38A169 100%)',
  'linear-gradient(135deg, #FA709A 0%, #FEE140 100%)',
  'linear-gradient(135deg, #4FACFE 0%, #00F2FE 100%)',
];

Page({
  data: {
    userInfo: null,
    levelInfo: null,
    creditLevel: null,
    nearbyGames: [],
    nearbyPlayers: [],
    loading: true,
    joiningId: '',
  },

  onShow() {
    const userInfo = app.globalData.userInfo;
    if (!userInfo) {
      wx.redirectTo({ url: '/pages/login/login' });
      return;
    }
    this.setData({
      userInfo: { ...userInfo },
      levelInfo: getLevelInfo(userInfo.level),
      creditLevel: getCreditLevel(userInfo.creditScore),
    });
    this.loadData();
  },

  async loadData() {
    this.setData({ loading: true });
    try {
      const [gamesResult, playersResult] = await Promise.all([
        api.getGames({ status: 'OPEN' }),
        api.getPlayers(),
      ]);

      const currentUserId = app.globalData.userInfo?._id;

      const games = gamesResult.list.slice(0, 5).map((g, i) => ({
        ...g,
        formattedDate: formatDate(g.date),
        spotsLeft: g.maxPlayers - g.currentPlayers,
        cardGradient: CARD_GRADIENTS[i % CARD_GRADIENTS.length],
        creator: {
          ...g.creator,
          levelInfo: getLevelInfo(g.creator.level),
        },
      }));

      const players = playersResult.list
        .filter(u => u._id !== currentUserId)
        .slice(0, 6)
        .map(u => ({ ...u, levelInfo: getLevelInfo(u.level) }));

      this.setData({ nearbyGames: games, nearbyPlayers: players });
    } catch (err) {
      showToast('加载失败，请下拉刷新');
    } finally {
      this.setData({ loading: false });
    }
  },

  async onQuickJoin(e) {
    const gameId = e.currentTarget.dataset.id;
    if (this.data.joiningId) return;
    this.setData({ joiningId: gameId });
    try {
      const result = await api.joinGame(gameId);
      if (result.success) {
        showToast('已加入！', 'success');
        this.loadData();
      } else {
        showToast(result.message || '加入失败');
      }
    } catch (err) {
      showToast('操作失败');
    } finally {
      this.setData({ joiningId: '' });
    }
  },

  onGameTap(e) {
    wx.navigateTo({ url: `/pages/game-detail/game-detail?id=${e.currentTarget.dataset.id}` });
  },

  onPlayerTap(e) {
    wx.navigateTo({ url: `/pages/player-profile/player-profile?id=${e.currentTarget.dataset.id}` });
  },

  onProfileTap() {
    wx.switchTab({ url: '/pages/profile/profile' });
  },

  onCreateGame() {
    wx.navigateTo({ url: '/pages/game-create/game-create' });
  },

  onMoreGames() {
    wx.switchTab({ url: '/pages/games/games' });
  },

  onGoFriends() {
    wx.switchTab({ url: '/pages/friends/friends' });
  },

  onUploadVideo() {
    wx.navigateTo({ url: '/pages/video-upload/video-upload' });
  },

  onPullDownRefresh() {
    this.loadData().then(() => wx.stopPullDownRefresh());
  },
});
