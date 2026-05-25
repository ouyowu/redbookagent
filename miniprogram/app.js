const { currentUser } = require('./utils/mock');

App({
  globalData: {
    userInfo: null,
    isLoggedIn: false,
    systemInfo: null,
  },

  onLaunch() {
    wx.getSystemInfo({
      success: (res) => { this.globalData.systemInfo = res; },
    });

    // 开发模式：直接使用 Mock 用户，跳过微信登录
    this.globalData.userInfo = { ...currentUser };
    this.globalData.isLoggedIn = true;
    wx.setStorageSync('token', 'mock_token_dev');
    wx.setStorageSync('userInfo', currentUser);
    // 加载圆体字体
    wx.loadFontFace({
      family: 'ZCOOL QingKe HuangYou',
      source: "url('https://fonts.gstatic.com/s/zcoolqingkehuangyou/v17/2Eb5L_R5IXJEWhD3I_5rZCBUPMoLoMbnBfJWf_-1.woff2')",
      success: () => {},
      fail: () => {},
    });
  },

  updateUserInfo(data) {
    this.globalData.userInfo = { ...this.globalData.userInfo, ...data };
    wx.setStorageSync('userInfo', this.globalData.userInfo);
  },

  logout() {
    this.globalData.userInfo = null;
    this.globalData.isLoggedIn = false;
    wx.removeStorageSync('token');
    wx.removeStorageSync('userInfo');
    wx.reLaunch({ url: '/pages/login/login' });
  },
});
