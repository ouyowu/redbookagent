const api = require('../../utils/api');
const { showToast } = require('../../utils/util');

Page({
  data: {
    messages: [],
    loading: false,
    unreadCount: 0,
  },

  onShow() {
    this.loadMessages();
  },

  async loadMessages() {
    this.setData({ loading: true });
    try {
      const messages = await api.getMessages();
      const unreadCount = messages.filter(m => !m.isRead).length;
      this.setData({ messages, unreadCount });
      // 更新 tabBar 角标
      if (unreadCount > 0) {
        wx.showTabBarRedDot({ index: 3 });
      } else {
        wx.hideTabBarRedDot({ index: 3 });
      }
    } catch (err) {
      showToast('加载失败');
    } finally {
      this.setData({ loading: false });
    }
  },

  async onMessageTap(e) {
    const { id, type, gameid } = e.currentTarget.dataset;
    // 标记已读
    await api.markMessageRead(id);

    // 根据消息类型跳转
    if (type === 'join_request' && gameid) {
      wx.navigateTo({ url: `/pages/game-detail/game-detail?id=${gameid}` });
    } else if (type === 'system' && gameid) {
      wx.navigateTo({ url: `/pages/game-detail/game-detail?id=${gameid}` });
    } else if (type === 'approved' && gameid) {
      wx.navigateTo({ url: `/pages/game-detail/game-detail?id=${gameid}` });
    } else if (type === 'review') {
      wx.switchTab({ url: '/pages/profile/profile' });
    }

    this.loadMessages();
  },

  onPullDownRefresh() {
    this.loadMessages().then(() => wx.stopPullDownRefresh());
  },
});
