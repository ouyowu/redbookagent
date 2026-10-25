const app = getApp();
const api = require('../../utils/api');
const { getLevelInfo, getCreditLevel, formatDate, showToast } = require('../../utils/util');

Page({
  data: {
    player: null,
    reviews: [],
    levelInfo: null,
    creditLevel: null,
    loading: true,
    isOwnProfile: false,
    activeTab: 'reviews',
  },

  onLoad(options) {
    const userId = options.id;
    this.userId = userId;
    this.loadPlayerData(userId);
  },

  async loadPlayerData(userId) {
    this.setData({ loading: true });
    try {
      const [player, reviews] = await Promise.all([
        api.getUserInfo(userId),
        api.getUserReviews(userId),
      ]);
      const isOwnProfile = userId === app.globalData.userInfo?._id;
      this.setData({
        player,
        reviews,
        levelInfo: getLevelInfo(player.level),
        creditLevel: getCreditLevel(player.creditScore),
        isOwnProfile,
      });
    } catch (err) {
      showToast('加载失败');
    } finally {
      this.setData({ loading: false });
    }
  },

  onTabChange(e) {
    this.setData({ activeTab: e.currentTarget.dataset.tab });
  },

  onReviewTap(e) {
    const gameId = e.currentTarget.dataset.gameid;
    wx.navigateTo({ url: `/pages/game-detail/game-detail?id=${gameId}` });
  },
});
