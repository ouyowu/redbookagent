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
    canReview: false,
    reviewablePlayers: [],  // 完成球局后可评价的其他参与者
  },

  onLoad(options) {
    this.gameId = options.id;
    this.loadGameDetail(this.gameId);
  },

  onShow() {
    // 返回后刷新（评价完成后信用分可能变化）
    if (this.gameId && this.data.game) {
      this.loadGameDetail(this.gameId);
    }
  },

  async loadGameDetail(gameId) {
    this.setData({ loading: true });
    try {
      const game = await api.getGameDetail(gameId);
      if (!game) {
        showToast('球局不存在');
        return;
      }

      const currentUserId = app.globalData.userInfo?._id;
      const isCreator = game.creatorId === currentUserId;
      const isParticipant = game.participants.some(p => p._id === currentUserId);
      const canJoin = !isParticipant && game.status === 'OPEN' && game.currentPlayers < game.maxPlayers;

      // 已结束且参与过的球局，可以对其他参与者进行评价
      const canReview = game.status === 'COMPLETED' && isParticipant;
      const reviewablePlayers = canReview
        ? game.participants
            .filter(p => p._id !== currentUserId)
            .map(p => ({
              ...p,
              hasReviewed: api.hasReviewed(gameId, p._id),
              levelInfo: getLevelInfo(p.level),
            }))
        : [];

      const enriched = {
        ...game,
        formattedDate: formatDate(game.date),
        spotsLeft: Math.max(0, game.maxPlayers - game.currentPlayers),
        participants: game.participants.map(p => ({
          ...p,
          levelInfo: getLevelInfo(p.level),
          creditLevel: getCreditLevel(p.creditScore),
        })),
      };

      this.setData({
        game: enriched,
        currentUserId,
        isCreator,
        isParticipant,
        canJoin,
        canReview,
        reviewablePlayers,
      });
    } catch (err) {
      showToast('加载失败');
    } finally {
      this.setData({ loading: false });
    }
  },

  async onJoinGame() {
    if (this.data.joining) return;
    const { game } = this.data;
    wx.showModal({
      title: '确认加入球局',
      content: `场地：${game.venue}\n时间：${game.formattedDate} ${game.startTime}\n费用：¥${game.fee}/人`,
      confirmText: '确认加入',
      success: async (res) => {
        if (!res.confirm) return;
        this.setData({ joining: true });
        try {
          const result = await api.joinGame(this.gameId);
          if (result.success) {
            showToast('已成功加入！', 'success');
            await this.loadGameDetail(this.gameId);
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
      title: '确认取消参加',
      content: '开局前2小时内取消将扣除10信用分，是否继续？',
      confirmText: '确认取消',
      confirmColor: '#F44336',
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

  onReviewPlayer(e) {
    const { id } = e.currentTarget.dataset;
    if (api.hasReviewed(this.gameId, id)) {
      showToast('已评价过该球友');
      return;
    }
    wx.navigateTo({
      url: `/pages/review/review?gameId=${this.gameId}&revieweeId=${id}`,
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
      title: `${this.data.game?.title} — 匹克约球`,
      path: `/pages/game-detail/game-detail?id=${this.gameId}`,
    };
  },
});
