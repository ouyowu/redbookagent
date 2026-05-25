const app = getApp();
const api = require('../../utils/api');
const { showToast } = require('../../utils/util');

Page({
  data: {
    loading: false,
  },

  onLoad() {
    if (app.globalData.isLoggedIn) {
      wx.switchTab({ url: '/pages/index/index' });
    }
  },

  async onWxLogin() {
    if (this.data.loading) return;
    this.setData({ loading: true });

    try {
      const user = await app.doLogin();

      if (!user.nickName || user.nickName === '未设置') {
        // 新用户，跳转完善资料
        wx.redirectTo({ url: '/pages/profile-edit/profile-edit?isNew=true' });
      } else {
        wx.switchTab({ url: '/pages/index/index' });
      }
    } catch (err) {
      showToast('登录失败，请重试');
    } finally {
      this.setData({ loading: false });
    }
  },

  // 开发调试：直接使用 mock 用户登录
  onMockLogin() {
    const { mockUsers } = require('../../utils/mock');
    app.globalData.userInfo = mockUsers[0];
    app.globalData.isLoggedIn = true;
    wx.setStorageSync('token', 'mock_token');
    wx.setStorageSync('userInfo', mockUsers[0]);
    wx.switchTab({ url: '/pages/index/index' });
  },
});
