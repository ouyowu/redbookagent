const app = getApp();
const api = require('../../utils/api');
const { getLevelInfo, getCreditLevel, formatDate, showToast } = require('../../utils/util');

Page({
  data: {
    userInfo: null,
    levelInfo: null,
    creditLevel: null,
    creditLogs: [],
    myGames: [],
    activeTab: 'games',
    loading: false,
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
    this.loadData();
  },

  async loadData() {
    this.setData({ loading: true });
    try {
      const [gamesResult, logs] = await Promise.all([
        api.getMyGames('joined'),
        api.getCreditLogs(this.data.userInfo._id),
      ]);
      this.setData({
        myGames: gamesResult.list.map(g => ({ ...g, formattedDate: formatDate(g.date) })),
        creditLogs: logs,
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

  onEditProfile() {
    wx.navigateTo({ url: '/pages/profile-edit/profile-edit' });
  },

  onUploadVideo() {
    wx.navigateTo({ url: '/pages/video-upload/video-upload' });
  },

  onGameTap(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({ url: `/pages/game-detail/game-detail?id=${id}` });
  },

  onGoMembership() {
    wx.navigateTo({ url: '/pages/membership/membership' });
  },

  onMyGamesTab() {
    this.setData({ activeTab: 'games' });
  },

  onCreditTab() {
    this.setData({ activeTab: 'credit' });
  },

  onLogout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) app.logout();
      },
    });
  },
});
