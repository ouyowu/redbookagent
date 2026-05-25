const api = require('./utils/api');
const { mockUsers } = require('./utils/mock');

App({
  globalData: {
    userInfo: null,
    isLoggedIn: false,
    systemInfo: null,
  },

  onLaunch() {
    // 获取系统信息
    wx.getSystemInfo({
      success: (res) => {
        this.globalData.systemInfo = res;
      },
    });

    // 检查登录态
    const token = wx.getStorageSync('token');
    const userInfo = wx.getStorageSync('userInfo');
    if (token && userInfo) {
      this.globalData.userInfo = userInfo;
      this.globalData.isLoggedIn = true;
    }

    // 云开发初始化（正式版使用）
    // if (wx.cloud) {
    //   wx.cloud.init({ env: 'your-env-id', traceUser: true });
    // }
  },

  // 微信登录
  async doLogin() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: async (res) => {
          if (res.code) {
            try {
              const result = await api.login(res.code);
              this.globalData.userInfo = result.user;
              this.globalData.isLoggedIn = true;
              wx.setStorageSync('token', result.token);
              wx.setStorageSync('userInfo', result.user);
              resolve(result.user);
            } catch (err) {
              reject(err);
            }
          } else {
            reject(new Error('微信登录失败'));
          }
        },
        fail: reject,
      });
    });
  },

  // 更新全局用户信息
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
