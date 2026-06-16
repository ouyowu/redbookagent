const app = getApp();

Page({
  data: {
    loading: false,
  },

  onLoad() {
    // 自动跳转（app.js 已设置 mock 用户）
    if (app.globalData.isLoggedIn) {
      wx.switchTab({ url: '/pages/index/index' });
    }
  },

  // 开发调试用
  onMockLogin() {
    const { currentUser } = require('../../utils/mock');
    app.globalData.userInfo = { ...currentUser };
    app.globalData.isLoggedIn = true;
    wx.setStorageSync('token', 'mock_token_dev');
    wx.setStorageSync('userInfo', currentUser);
    wx.switchTab({ url: '/pages/index/index' });
  },
});
