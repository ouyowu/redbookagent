const app = getApp();
const api = require('../../utils/api');
const { formatDate, getLevelInfo, getCreditLevel, showToast } = require('../../utils/util');

Page({
  data: {
    game: null,
    loading: true,
    joining: false,
    currentUserId: '',
    isCreator: false,
    isParticipant: false,
    canJoin: false,
  },

  onLoad(options) {
    const gameId = options.id;
    this.gameId = gameId;
    this.loadGameDetail(gameId);
  },

  async loadGameDetail(gameId) {
    this.setData({ loading: true });
    try {
      const game = await api.getGameDetail(gameId);
      const currentUserId = app.globalData.userInfo?._id;
      const isCreator = game.creatorId === currentUserId;
      const isParticipant = game.participants.some(p => p._id === currentUserId);
      const canJoin = !isParticipant && game.status === 'OPEN' && game.currentPlayers < game.maxPlayers;

      const enriched = {
        ...game,
        formattedDate: formatDate(game.date),
        spotsLeft: game.maxPlayers - game.currentPlayers,
        participants: game.participants.map(p => ({
          ...p,
          levelInfo: getLevelInfo(p.level),
          creditLevel: getCreditLevel(p.creditScore),
        })),
      };

      this.setData({ game: enriched, currentUserId, isCreator, isParticipant, canJoin });
    } catch (err) {
      showToast('加载失败');
    } finally {
      this.setData({ loading: false });
    }
  },

  async onJoinGame() {
    if (this.data.joining) return;

    wx.showModal({
      title: '确认加入球局',
      content: `费用：¥${this.data.game.fee}/人\n场地：${this.data.game.venue}\n时间：${this.data.game.formattedDate} ${this.data.game.startTime}`,
      success: async (res) => {
        if (!res.confirm) return;
        this.setData({ joining: true });
        try {
          const result = await api.joinGame(this.gameId);
          if (result.success) {
            showToast('已成功加入球局！', 'success');
            this.loadGameDetail(this.gameId);
          } else {
            showToast(result.message || '加入失败');
          }
        } catch (err) {
          showToast('操作失败，请重试');
        } finally {
          this.setData({ joining: false });
        }
      },
    });
  },

  async onCancelJoin() {
    wx.showModal({
      title: '确认取消',
      content: '取消参加此球局？注意：开局前2小时内取消将扣除10信用分',
      success: async (res) => {
        if (!res.confirm) return;
        try {
          await api.cancelJoinGame(this.gameId);
          showToast('已取消参加');
          this.loadGameDetail(this.gameId);
        } catch (err) {
          showToast('操作失败');
        }
      },
    });
  },

  onPlayerTap(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({ url: `/pages/player-profile/player-profile?id=${id}` });
  },

  onShareGame() {
    wx.showShareMenu({ withShareTicket: true });
  },

  onShareAppMessage() {
    return {
      title: `${this.data.game.title} — 匹克约球`,
      path: `/pages/game-detail/game-detail?id=${this.gameId}`,
    };
  },
});
