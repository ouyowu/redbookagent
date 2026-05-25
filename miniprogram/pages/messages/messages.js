const api = require('../../utils/api');
const { showToast } = require('../../utils/util');

const MSG_COLORS = ['c-lavender', 'c-mint', 'c-peach', 'c-yellow', 'c-blue'];

const WEEK_DAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

Page({
  data: {
    unreadMessages: [],
    readMessages: [],
    dateStr: '',
    loading: false,
  },

  onShow() {
    const d = new Date();
    const dateStr = `${d.getMonth() + 1}月${d.getDate()}日 ${WEEK_DAYS[d.getDay()]}`;
    this.setData({ dateStr });
    this.loadMessages();
  },

  async loadMessages() {
    this.setData({ loading: true });
    try {
      const messages = await api.getMessages();

      const unreadMessages = messages
        .filter(m => !m.isRead)
        .map((m, i) => ({ ...m, cardColor: MSG_COLORS[i % MSG_COLORS.length] }));

      const readMessages = messages.filter(m => m.isRead);

      this.setData({ unreadMessages, readMessages });

      if (unreadMessages.length > 0) {
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

  onPullDownRefresh() {
    this.loadMessages().then(() => wx.stopPullDownRefresh());
  },
});
