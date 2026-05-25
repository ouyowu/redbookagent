const app = getApp();
const api = require('../../utils/api');
const { getLevelInfo, getCreditLevel, formatDate, showToast } = require('../../utils/util');

Page({
  data: {
    userInfo: null,
    levelInfo: null,
    creditLevel: null,
    nearbyGames: [],
    loading: true,
    banners: [
      { id: 1, title: '上传球技视频，获得认证等级', bg: '#00B96B', icon: '🎥' },
      { id: 2, title: '信用积分越高，约球越顺利', bg: '#2196F3', icon: '⭐' },
      { id: 3, title: '同城球友，随时约战', bg: '#FF9800', icon: '📍' },
    ],
    bannerCurrent: 0,
    stats: { gamesPlayed: 0, creditScore: 80, level: 'P1' },
  },

  onShow() {
    const userInfo = app.globalData.userInfo;
    if (!userInfo) {
      wx.redirectTo({ url: '/pages/login/login' });
      return;
    }
    this.setData({
      userInfo,
      levelInfo: getLevelInfo(userInfo.level),
      creditLevel: getCreditLevel(userInfo.creditScore),
    });
    this.loadNearbyGames();
  },

  async loadNearbyGames() {
    this.setData({ loading: true });
    try {
      const result = await api.getGames({ status: 'OPEN' });
      const games = result.list.slice(0, 3).map(g => ({
        ...g,
        formattedDate: formatDate(g.date),
        spotsLeft: g.maxPlayers - g.currentPlayers,
      }));
      this.setData({ nearbyGames: games });
    } catch (err) {
      showToast('加载失败，请刷新');
    } finally {
      this.setData({ loading: false });
    }
  },

  onBannerChange(e) {
    this.setData({ bannerCurrent: e.detail.current });
  },

  onBannerTap(e) {
    const { id } = e.currentTarget.dataset;
    if (id === 1) wx.navigateTo({ url: '/pages/video-upload/video-upload' });
  },

  onGameTap(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({ url: `/pages/game-detail/game-detail?id=${id}` });
  },

  onProfileTap() {
    const userId = this.data.userInfo._id;
    wx.navigateTo({ url: `/pages/player-profile/player-profile?id=${userId}` });
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

  onRefresh() {
    this.loadNearbyGames();
  },

  onPullDownRefresh() {
    this.loadNearbyGames().then(() => wx.stopPullDownRefresh());
  },
});
