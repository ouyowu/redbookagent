const app = getApp();
const api = require('../../utils/api');
const { showToast } = require('../../utils/util');
const { mockUsers } = require('../../utils/mock');

Page({
  data: {
    unreadMessages: [],
    readMessages: [],
    activeUsers: [],
    loading: false,
  },

  onShow() {
    this.loadMessages();
  },

  async loadMessages() {
    this.setData({ loading: true });
    try {
      const messages = await api.getMessages();

      const unreadMessages = messages.filter(m => !m.isRead);
      const readMessages = messages.filter(m => m.isRead);

      // 取有 fromUser 的消息发送者去重作为活跃用户，补充固定球友
      const seenIds = new Set();
      const activeUsers = [];
      messages.forEach(m => {
        if (m.fromUser && !seenIds.has(m.fromUser._id)) {
          seenIds.add(m.fromUser._id);
          activeUsers.push(m.fromUser);
        }
      });
      // 补充更多活跃球友
      mockUsers.slice(0, 6).forEach(u => {
        if (!seenIds.has(u._id)) {
          seenIds.add(u._id);
          activeUsers.push(u);
        }
      });

      const unreadCount = unreadMessages.length;
      this.setData({ unreadMessages, readMessages, activeUsers });

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
    await api.markMessageRead(id);

    if ((type === 'join_request' || type === 'system' || type === 'approved') && gameid) {
      wx.navigateTo({ url: `/pages/game-detail/game-detail?id=${gameid}` });
    } else if (type === 'review') {
      wx.switchTab({ url: '/pages/profile/profile' });
    }

    this.loadMessages();
  },

  onPlayerTap(e) {
    wx.navigateTo({ url: `/pages/player-profile/player-profile?id=${e.currentTarget.dataset.id}` });
  },

  onPullDownRefresh() {
    this.loadMessages().then(() => wx.stopPullDownRefresh());
  },
});
